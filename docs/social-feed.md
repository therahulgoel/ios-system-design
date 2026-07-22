<[Problem Title]>
# Infinite Social Feed

## Overview
Designing an infinite social feed is a cornerstone system design question for consumer-facing mobile applications. The goal is to present an endless, smooth-scrolling timeline of text, images, and videos. This evaluates a candidate's grasp of pagination (cursor vs offset), memory management in UICollectionView, offline caching, and optimistic UI updates for interactions like liking and commenting.

## Target Companies & Frequency
| Company | Why They Ask | Frequency |
| :--- | :--- | :--- |
| Meta | Instagram, Facebook, Threads are entirely feed-driven | ★★★★★ |
| Twitter / X | The core product is a real-time chronological feed | ★★★★★ |
| LinkedIn | Feed is the primary engagement surface for users | ★★★★★ |
| Snap | Discover and Spotlight feeds are heavily media-based | ★★★★☆ |
| TikTok | A purely video-driven feed (similar principles apply) | ★★★★☆ |

## Scope Definition

### In Scope
- Cursor-based pagination API design.
- UI layer using UICollectionView with DiffableDataSource for smooth updates.
- Prefetching the next page (triggering at ~70% scroll depth).
- Image pipeline integration (prefetching thumbnails).
- Offline feed persistence using SQLite.
- Optimistic interactions (liking a post).
- Pull-to-refresh logic and state management.
- Impression tracking (analytics for visible cells).

### Out of Scope
- Video streaming architecture (focus is on text/image posts).
- Backend ranking and recommendation machine learning models.
- Real-time WebSockets for new post indicators (unless specifically requested).

## Requirements

### Functional Requirements
1. **Infinite Scroll**: Users can scroll continuously without hitting a hard bottom.
2. **Offline Support**: The app must show the most recent cached feed when offline.
3. **Interactions**: Users can like and comment on posts with immediate visual feedback.
4. **Pull to Refresh**: Users can fetch the latest content from the top.
5. **Impression Tracking**: The system must log when a user views a post.

### Non-Functional Requirements
| Requirement | Target | Source / Justification |
| :--- | :--- | :--- |
| Scroll Frame Rate | 60 FPS | Apple UI Guidelines (No main thread blocking) |
| Pagination Latency | < 500ms | P99 network latency expectation for smooth UX |
| Memory Footprint | < 150MB | Instagram engineering blogs on memory limits |
| Offline Cache | Last 200 items | Balanced between storage size and UX |
| Cache TTL | 5 minutes | Stale feeds lead to poor engagement |

## High-Level Architecture (HLD)

### Component Diagram
```ascii
+-------------------+       +--------------------+       +-------------------+
|                   |       |                    |       |                   |
|  FeedController   | <---> |   FeedViewModel    | <---> |   FeedRepository  |
| (UICollectionView)|       |   (Observable)     |       | (Data Coordinator)|
|                   |       |                    |       |                   |
+-------------------+       +--------------------+       +-------------------+
          |                                                        |
          v                                                        |
+-------------------+                                              v
|                   |                                    +-------------------+
|  DiffableData     |                                    |                   |
|     Source        |                                    |   SQLite Cache    |
|                   |                                    |  (Local Storage)  |
+-------------------+                                    |                   |
                                                         +-------------------+
                                                                   |
                                                                   v
                                                         +-------------------+
                                                         |                   |
                                                         |   NetworkLayer    |
                                                         |   (API Client)    |
                                                         |                   |
                                                         +-------------------+
```

### Component Responsibilities
| Component | Responsibility | iOS Implementation |
| :--- | :--- | :--- |
| FeedController | Displays UI, reports scroll depth, fires interaction events | UIViewController, UICollectionView |
| FeedViewModel | Manages state, handles business logic, applies optimistic updates | ObservableObject (SwiftUI) or standard class |
| FeedRepository | Decides whether to fetch from cache or network, handles TTL | Injectable Service |
| SQLite Cache | Persists items for offline mode and fast cold starts | GRDB / CoreData / SQLite.swift |
| NetworkLayer | Executes API requests, manages pagination parameters | URLSession |

### Data Flow
1. User opens the app. `FeedController` asks `FeedViewModel` for data.
2. `FeedViewModel` calls `FeedRepository.fetchFeed()`.
3. `FeedRepository` immediately returns the first 200 items from `SQLite Cache` (offline mode). UI updates.
4. Simultaneously, `FeedRepository` hits the `NetworkLayer` to fetch fresh items.
5. `NetworkLayer` calls `GET /v1/feed`. Upon success, it updates `SQLite Cache` and pushes new items to the `FeedViewModel`.
6. `FeedViewModel` updates its published state. The `DiffableDataSource` animates the new items into the `UICollectionView`.
7. User scrolls down. At 70% depth, `FeedController` triggers `FeedViewModel.fetchNextPage()`.
8. `FeedViewModel` uses the `after_cursor` to fetch the next batch.

## Data Models

### Core Entities
```swift
import Foundation

struct FeedItem: Identifiable, Hashable, Codable {
    let id: String
    let authorId: String
    let authorName: String
    let authorAvatarUrl: URL
    let textContent: String?
    let imageUrls: [URL]
    var likeCount: Int
    var isLikedByMe: Bool
    let createdAt: Date
    
    // Hashable requirement for DiffableDataSource
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}

struct FeedPage: Codable {
    let items: [FeedItem]
    let nextCursor: String?
    let hasMore: Bool
}
```

### Database Schema
```sql
CREATE TABLE IF NOT EXISTS feed_items (
    id TEXT PRIMARY KEY,
    author_id TEXT NOT NULL,
    author_name TEXT NOT NULL,
    author_avatar_url TEXT,
    text_content TEXT,
    image_urls_json TEXT,
    like_count INTEGER NOT NULL,
    is_liked_by_me BOOLEAN NOT NULL,
    created_at REAL NOT NULL,
    inserted_at REAL NOT NULL -- Used for TTL and cache eviction
);

CREATE INDEX idx_created_at ON feed_items(created_at DESC);
```

## API Design

### Endpoints

**1. Fetch Feed**
- **Method**: GET
- **Path**: `/v1/feed`
- **Query Params**:
  - `limit`: 20
  - `after_cursor`: `base64_encoded_string` (Optional)
- **Response**:
```json
{
  "items": [
    {
      "id": "post_123",
      "text_content": "Hello World!",
      "like_count": 42,
      "is_liked_by_me": false
    }
  ],
  "next_cursor": "cursor_xyz",
  "has_more": true
}
```

**2. Like Post**
- **Method**: POST
- **Path**: `/v1/posts/{post_id}/like`
- **Response**: 200 OK

### Pagination Strategy
**Cursor-based pagination is mandatory for feeds.** 
Offset-based pagination (`OFFSET 20 LIMIT 20`) is $O(n)$ for the database and prone to errors. If a new post is inserted at the top of the feed while the user is on page 1, the item at index 20 shifts to 21. When the client requests page 2 (`OFFSET 20`), they will see the same post twice. 
Cursors (e.g., an opaque string representing a timestamp + UUID) solve this by pointing to a specific row, providing $O(1)$ lookup and stable results during inserts.

## Client Architecture Deep-Dives

### [Subsystem 1 — Pagination & Prefetching]
To achieve infinite scrolling without the user seeing a loading spinner at the bottom, we prefetch the next page when the user reaches ~70% of the current content.

```swift
import UIKit

class FeedViewModel: ObservableObject {
    @Published var items: [FeedItem] = []
    @Published var isFetchingNextPage = false
    
    private var nextCursor: String?
    private let repository: FeedRepository
    
    init(repository: FeedRepository) {
        self.repository = repository
    }
    
    func onScrollThresholdReached() {
        guard let cursor = nextCursor, !isFetchingNextPage else { return }
        fetchNextPage(cursor: cursor)
    }
    
    private func fetchNextPage(cursor: String) {
        isFetchingNextPage = true
        Task {
            do {
                let page = try await repository.fetchFeed(cursor: cursor)
                await MainActor.run {
                    self.items.append(contentsOf: page.items)
                    self.nextCursor = page.nextCursor
                    self.isFetchingNextPage = false
                }
                
                // Trigger Image Pipeline Prefetch for new items
                ImagePrefetcher.shared.prefetch(urls: page.items.flatMap { $0.imageUrls })
            } catch {
                await MainActor.run { self.isFetchingNextPage = false }
            }
        }
    }
}
```

### [Subsystem 2 — Optimistic Updates]
When a user taps "Like", waiting for the network request to finish before turning the heart red feels sluggish. We update the UI immediately and rollback if the API fails.

```swift
extension FeedViewModel {
    func toggleLike(for itemID: String) {
        // 1. Find index
        guard let index = items.firstIndex(where: { $0.id == itemID }) else { return }
        
        // 2. Optimistic UI Update
        var item = items[index]
        let originalLikeState = item.isLikedByMe
        
        item.isLikedByMe.toggle()
        item.likeCount += item.isLikedByMe ? 1 : -1
        items[index] = item // Triggers DiffableDataSource update
        
        // 3. Network Request
        Task {
            do {
                try await repository.likePost(id: itemID, like: item.isLikedByMe)
                // Success: update SQLite Cache to reflect the new state
                try await repository.updateLocalCache(item: item)
            } catch {
                // 4. Rollback on Failure
                await MainActor.run {
                    var failedItem = self.items[index]
                    failedItem.isLikedByMe = originalLikeState
                    failedItem.likeCount += originalLikeState ? 1 : -1
                    self.items[index] = failedItem
                    
                    // Show error toast
                    ToastManager.show(message: "Failed to like post.")
                }
            }
        }
    }
}
```

### [Subsystem 3 — Impression Tracking]
Analytics are crucial. We need to know if a user actually *viewed* a post, not just scrolled past it at 100mph.

```swift
import UIKit

class FeedViewController: UICollectionViewController {
    var viewedItems = Set<String>()
    
    override func scrollViewDidScroll(_ scrollView: UIScrollView) {
        let visibleCells = collectionView.visibleCells
        for cell in visibleCells {
            guard let indexPath = collectionView.indexPath(for: cell),
                  let item = dataSource.itemIdentifier(for: indexPath) else { continue }
            
            // Calculate intersection area
            let cellFrame = collectionView.convert(cell.frame, to: collectionView.superview)
            let visibleRect = collectionView.bounds
            let intersection = visibleRect.intersection(cellFrame)
            let visibleRatio = (intersection.height * intersection.width) / (cell.frame.height * cell.frame.width)
            
            // If > 50% visible, track impression
            if visibleRatio > 0.5 && !viewedItems.contains(item.id) {
                viewedItems.insert(item.id)
                Analytics.shared.track(.feedItemViewed(itemId: item.id))
            }
        }
        
        // Check for pagination trigger (70% depth)
        let offsetY = scrollView.contentOffset.y
        let contentHeight = scrollView.contentSize.height
        let height = scrollView.frame.size.height
        if offsetY > contentHeight - height * 2.0 {
            viewModel.onScrollThresholdReached()
        }
    }
}
```

## Performance & Optimizations
| Optimization | Technique | Benchmark/Impact |
| :--- | :--- | :--- |
| UI Rendering | `UICollectionViewDiffableDataSource` | $O(N)$ safe UI updates without `NSInternalInconsistencyException` |
| Image Prefetching | `SDWebImagePrefetcher` | Reduces perceived image load time to 0ms for the next 20 cells |
| Cell Reusability | `prepareForReuse` | Prevents memory explosion by capping UI views to visible + buffer (~10 cells) |
| Off-Screen Memory | Cancel network requests in `didEndDisplaying` | Saves user bandwidth and CPU during fast scrolling |

## Failure Modes & Fallbacks
| Failure Scenario | Detection | Fallback Strategy |
| :--- | :--- | :--- |
| API Returns 5xx | Catch `URLError.badServerResponse` | Show offline SQLite cache with a "Cached" badge/banner. |
| Like Failure | API throws error | Rollback optimistic update, show toast. |
| OOM (Out of Memory)| OS Memory Warning | Clear decoded image cache (L1), drop old feed pages from memory list. |

## Trade-off Analysis
| Decision | Option A | Option B | Chosen | Why |
| :--- | :--- | :--- | :--- | :--- |
| Pagination Type | Offset-based | Cursor-based | Cursor-based | Avoids duplicated or skipped items when feed changes dynamically. O(1) DB lookup. |
| State Management | Delegate pattern | Publisher / ObservableObject | Publisher | DiffableDataSource pairs perfectly with a single source of truth published array. |
| Cache Expiration | Evict on start | Evict based on TTL (5 min) | TTL (5 min) | Prevents the app from showing 2-day old content for a split second before the network loads. |

## Observability & Metrics
- **Scroll Hitch Rate**: Target < 5%. (Frames taking > 16.6ms).
- **Time to First Feed (TTFF)**: Cold start to seeing cached feed < 1.0s.
- **Like Interaction Latency (Optimistic)**: Target < 16ms (1 frame) visual feedback.
- **Cache Hit Rate**: Percentage of sessions starting with valid SQLite cache > 80%.

## Production Benchmarks Reference
| Metric | Target | Source / Justification |
| :--- | :--- | :--- |
| Page Size | 15-20 items | Standard API batch size (Twitter/Instagram) |
| JSON Payload | ~8-12KB compressed | 20 items * 500 bytes |
| Memory Limits | < 150MB total app | Keeps OS from aggressively jetsam-ing the app |

## Interview Tips
- **DiffableDataSource**: Mention this! It prevents crashes related to index out of bounds that used to plague `reloadData()` or `performBatchUpdates()`.
- **Cursor vs Offset**: Have a crisp 2-sentence explanation ready for why cursor pagination is required for feeds.
- **Optimistic Updates**: Interviewers love this. It shows you care about the end-user UX, not just the code.
- **Memory Management**: Talk about releasing decoded images when cells go off-screen.
