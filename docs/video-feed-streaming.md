Short-form Video Feed (TikTok / Instagram Reels / YouTube Shorts)
## Overview
Designing a short-form video feed focuses heavily on perceived latency, buttery smooth scrolling, memory management, and bandwidth conservation. It requires sophisticated prefetching strategies, AVPlayer connection pooling, and strict UI recycling.

## Target Companies & Frequency
| Company | Why They Ask | Frequency |
|---------|--------------|-----------|
| Meta | Instagram Reels is a core product. | ★★★★★ |
| ByteDance| Core business (TikTok). | ★★★★★ |
| Google | YouTube Shorts architecture. | ★★★★★ |
| Snap | Spotlight feature relies on this. | ★★★★☆ |

## Scope Definition

### In Scope
- Sliding window AVPlayer pool (prev, current, next).
- Prefetch trigger strategies (start buffering next video at 80% progress).
- Visibility tracking for autoplay (UICollectionView + intersection).
- Cursor-based pagination and data fetching.
- Low-bandwidth detection and adaptive bitrate adjustments.
- Memory and battery guardrails (disposing items, pausing prefetch on Low Power Mode).
- Caching thumbnails and initial chunks.

### Out of Scope
- Video recording, editing, and uploading (creation tools).
- Backend encoding pipeline (transcoding to HLS/Dash).
- Complex comment threading architecture.

## Requirements

### Functional Requirements
1. Videos must autoplay instantly when scrolled into view.
2. Smooth infinite scrolling without stutter.
3. Automatically prefetch the next video to eliminate buffering.
4. Adapt video quality based on network conditions.
5. Respect system states (Low Power Mode, Background).

### Non-Functional Requirements
| Requirement | Target | Source |
|-------------|--------|--------|
| Time to First Frame (TTFF) | < 300ms | TikTok Engineering Blog |
| Scroll FPS | 60 FPS (16ms/frame) | Apple WWDC Core Animation |
| Payload Size (Feed Page) | < 15KB | Meta Engineering |
| Cache Hit Ratio (Thumbnails) | > 95% | General CDN guidelines |
| Memory Overhead | < 150MB total | AVFoundation guidelines |

## High-Level Architecture (HLD)

### Component Diagram
```text
[ Client Device ]
       |
       | (Cursor-based Pagination)
       v
[ API Gateway / Load Balancer ] ---> [ Feed Service ] ---> [ Redis Feed Cache ]
       |
       | (Media Delivery)
       v
[ Video CDN ] ---> [ Edge Nodes ]

--- iOS Client Internals ---
+-----------------------------------------------------------+
| Feed UI (UICollectionView / ScrollView)                   |
|       |                                                   |
|       v                                                   |
| [ Visibility Tracker ] ---> [ Feed ViewModel ]            |
|                               |                           |
|                               +-> [ Feed Paginator ]      |
|                               |                           |
|                               v                           |
| [ Prefetch Engine ] <---> [ AVPlayer Pool ]               |
|                               |                           |
|                               v                           |
| [ Network / Path Monitor (Adaptive Bitrate) ]             |
+-----------------------------------------------------------+
```

### Component Responsibilities
| Component | Responsibility | iOS Implementation |
|-----------|----------------|--------------------|
| AVPlayerPool | Maintain 3 active players, recycle unused ones | AVQueuePlayer / AVPlayer |
| PrefetchEngine| Download initial video chunks ahead of time | AVAssetDownloadTask / AVAssetResourceLoaderDelegate |
| VisibilityTracker| Determine which cell is >85% visible | ScrollViewDidScroll / GeometryReader |
| FeedPaginator | Manage cursor, fetch next batch at 70% depth | URLSession |
| PathMonitor | Detect low bandwidth / WiFi vs Cellular | NWPathMonitor |

### Data Flow
1. **Initial Load**: `FeedPaginator` fetches first 10 items.
2. **Display**: UI renders first cell. `VisibilityTracker` detects 100% visibility.
3. **Playback**: `AVPlayerPool` assigns a player to index 0, starts playback.
4. **Prefetch**: User watches video. At 80% playback duration, `PrefetchEngine` loads index 1.
5. **Scroll**: User scrolls. `VisibilityTracker` pauses index 0, autoplays index 1.
6. **Recycle**: Index 0 moved to 'previous' state, index 2 prefetched. If user scrolls to index 3, index 0 player is deallocated.

## Data Models

### Core Entities
```swift
import Foundation

struct VideoFeedResponse: Codable {
    let items: [VideoItem]
    let nextCursor: String?
    let hasMore: Bool
}

struct VideoItem: Codable, Identifiable {
    let id: String
    let authorId: String
    let description: String
    let thumbnailUrls: MediaVariants
    let videoUrls: MediaVariants
    let stats: VideoStats
}

struct MediaVariants: Codable {
    let high: String    // e.g., 1080p, high bitrate
    let medium: String  // e.g., 720p
    let low: String     // e.g., 240p, ~200Kbps for low bandwidth
}

struct VideoStats: Codable {
    let likesCount: Int
    let sharesCount: Int
    let commentsCount: Int
}
```

## API Design

### Endpoints
**GET /v1/feed**
Fetches a batch of videos.

**Headers:**
- `Authorization: Bearer <token>`
- `X-Network-Quality: 3g` (Optional, hints server to send optimized URLs)

**Query Params:**
- `cursor`: Base64 encoded string (omit for first fetch)
- `limit`: 10

**Response Body:**
```json
{
  "items": [
    {
      "id": "vid_987",
      "author_id": "usr_123",
      "description": "Awesome dance!",
      "thumbnail_urls": {
        "low": "https://cdn.example.com/t/vid_987_240.webp",
        "high": "https://cdn.example.com/t/vid_987_1080.webp"
      },
      "video_urls": {
        "low": "https://cdn.example.com/v/vid_987_240.mp4",
        "high": "https://cdn.example.com/v/vid_987_1080.mp4"
      },
      "stats": {
        "likes_count": 12000,
        "shares_count": 450,
        "comments_count": 89
      }
    }
  ],
  "next_cursor": "eyJvZmZzZXQiOjEwfQ==",
  "has_more": true
}
```

## Client Architecture Deep-Dives

### AVPlayer Pool (Memory Guard)
Creating `AVPlayer` instances is expensive (~15MB memory overhead each). We use a sliding window of exactly 3 players: Previous, Current, Next.

```swift
import AVFoundation

class AVPlayerPool {
    static let shared = AVPlayerPool()
    
    // Max 3 players to keep memory < 50MB
    private var availablePlayers: [AVPlayer] = []
    private var activePlayers: [String: AVPlayer] = [:] // map videoId to player
    
    init() {
        for _ in 0..<3 {
            availablePlayers.append(AVPlayer())
        }
    }
    
    func player(for videoId: String, url: URL) -> AVPlayer? {
        // Return existing if active
        if let existing = activePlayers[videoId] { return existing }
        
        // Grab from pool
        guard let player = availablePlayers.popLast() else {
            print("⚠️ Player pool exhausted")
            return nil
        }
        
        let asset = AVURLAsset(url: url)
        let item = AVPlayerItem(asset: asset)
        player.replaceCurrentItem(with: item)
        activePlayers[videoId] = player
        return player
    }
    
    func releasePlayer(for videoId: String) {
        guard let player = activePlayers.removeValue(forKey: videoId) else { return }
        player.pause()
        player.replaceCurrentItem(with: nil)
        availablePlayers.append(player) // Return to pool
    }
}
```

### Visibility Tracker & Autoplay
We must determine exactly which video takes up the most screen real estate to autoplay it.

```swift
import UIKit

class VisibilityTracker {
    
    /// Called from scrollViewDidScroll
    func checkVisibility(collectionView: UICollectionView, visibleCells: [UICollectionViewCell]) -> IndexPath? {
        let centerPoint = CGPoint(x: collectionView.center.x + collectionView.contentOffset.x,
                                  y: collectionView.center.y + collectionView.contentOffset.y)
        
        // The cell closest to the center is the active one
        var closestCell: IndexPath? = nil
        var minDistance = CGFloat.greatestFiniteMagnitude
        
        for cell in visibleCells {
            let cellCenter = cell.center
            let distance = abs(cellCenter.y - centerPoint.y)
            
            if distance < minDistance {
                minDistance = distance
                closestCell = collectionView.indexPath(for: cell)
            }
        }
        return closestCell
    }
}
```

### Network Monitoring & Bandwidth Adaptation
Detect network changes to adjust video quality request and prefetching aggression.

```swift
import Network

class NetworkMonitor {
    static let shared = NetworkMonitor()
    private let monitor = NWPathMonitor()
    
    var isLowBandwidth: Bool = false
    
    func start() {
        monitor.pathUpdateHandler = { [weak self] path in
            // If constrained (e.g. Low Data Mode) or expensive (Cellular)
            if path.isConstrained || path.usesInterfaceType(.cellular) {
                self?.isLowBandwidth = true
            } else {
                self?.isLowBandwidth = false
            }
        }
        monitor.start(queue: DispatchQueue.global(qos: .background))
    }
}
```

## Performance & Optimizations
| Optimization | Technique | Benchmark/Impact |
|--------------|-----------|------------------|
| Prefetch Trigger | Start buffering next item at 80% duration | Decreases TTFF to almost 0ms on scroll |
| Thumbnail Format | WebP progressive loading, 320px | Reduces payload by 30% compared to JPEG |
| Battery Guard | Check `ProcessInfo.processInfo.isLowPowerModeEnabled` | Pauses aggressive prefetching, extends battery life |
| Memory Guard | strict 3-player pool, clear thumbnails via `NSCache` | Keeps RAM usage < 100MB, prevents OOM jetsam |

## Failure Modes & Fallbacks
| Failure Scenario | Detection | Fallback Strategy |
|------------------|-----------|-------------------|
| Network loss | `URLError.notConnectedToInternet` | Play pre-cached videos in the loop. Show generic toast error. |
| Slow Network | Stalling AVPlayer (`playbackLikelyToKeepUp == false`) | Switch immediately to 240p URL variant. |
| OOM Warning | `UIApplication.didReceiveMemoryWarningNotification` | Empty AVPlayer pool, purge NSCache for thumbnails. |

## Trade-off Analysis
| Decision | Option A | Option B | Chosen | Why |
|----------|----------|----------|--------|-----|
| Pagination | Offset (Page 1, 2) | Cursor (next_id) | **Cursor** | Feed is real-time. Offset causes duplicate items if new videos are inserted at the top. |
| Video Protocol | HLS | MP4 (Progressive) | **MP4** | For short-form (<60s), MP4 via CDN is faster to start. HLS overhead (manifest fetching) delays TTFF too much. |
| Prefetch Depth | 1 video ahead | 5 videos ahead | **1 video** | 5 videos wastes user bandwidth and battery (often they swipe past quickly). 1 is sufficient. |

## Observability & Metrics
- `time_to_first_frame`: Target < 300ms.
- `video_stall_count`: Number of times player paused to buffer. Target < 1% of views.
- `feed_cache_hit_ratio`: How often a requested thumbnail/video was already on disk.
- `memory_warning_count`: Monitor for memory leaks in the player pool.

## Production Benchmarks Reference
| Metric | Value | Source |
|--------|-------|--------|
| AVPlayer Memory | ~15MB per instance | Apple Developer Forums |
| Low Bandwidth Video | ~200Kbps at 240p | Meta Engineering |
| JSON Feed Payload | 8-12KB per 10 items | Instagram Reels network trace |

## Interview Tips
- **The Pool is the key**: If you suggest instantiating a new `AVPlayer` for every cell, you will fail the interview. Emphasize the 3-item sliding window.
- **Protocol distinction**: Know *why* MP4 is often used over HLS for short-form (HLS requires downloading a playlist manifest first, delaying startup. MP4 progressive download starts instantly).
- **Edge cases**: Mention Low Power Mode (`ProcessInfo`) and Low Data Mode (`NWPathMonitor.isConstrained`). Interviewers love when you respect user device state.
