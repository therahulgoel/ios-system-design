<[Problem Title]>
# Mobile Analytics & Telemetry SDK

## Overview
Designing a mobile analytics SDK (like Firebase Analytics, Amplitude, or Mixpanel) is a heavy infrastructure and platform question. The focus is entirely on thread safety, persistent storage, batching, minimizing battery/network impact, and ensuring zero main-thread block time. The SDK must be completely invisible to the host app's performance.

## Target Companies & Frequency
| Company | Why They Ask | Frequency |
| :--- | :--- | :--- |
| Google / Firebase | Core product of the Firebase platform team | ★★★★★ |
| Uber | Telemetry and platform teams need highly robust event logging | ★★★★☆ |
| Meta | App infrastructure teams handling massive data pipelines | ★★★★☆ |
| Airbnb | Platform engineering roles handling observability | ★★★★☆ |

## Scope Definition

### In Scope
- Thread-safe event ingestion (non-blocking).
- Persistent local storage of events (SQLite).
- Batch uploading with compression (GZIP).
- Retry mechanisms and exponential backoff.
- Network condition and battery state awareness.
- Session management.
- Dynamic sampling configurations from the server.

### Out of Scope
- UI event auto-tracking (swizzling views).
- Backend data lake architecture (Kafka/Hadoop).
- Dashboard visualization.
- Crash reporting (e.g., symbolication, stack traces).

## Requirements

### Functional Requirements
1. **Ingest Events**: Accept arbitrary JSON properties attached to an event name.
2. **Persist Events**: Save events locally so they survive app crashes or terminations.
3. **Batch and Upload**: Send events in batches to save network overhead.
4. **Retry**: If upload fails, keep events and retry later.

### Non-Functional Requirements
| Requirement | Target | Source / Justification |
| :--- | :--- | :--- |
| Main Thread Block Time | ~0ms (Lock-free) | Calling `track()` should never block the UI |
| Battery Impact | < 1% of total drain | Wake the radio as little as possible |
| Network Usage | GZIP compressed payloads | JSON compresses well (up to 80% reduction) |
| Max Local Storage | 10MB or 10,000 events | Prevents SDK from eating user storage |
| Batch Size | ~100 events | Optimal size for standard REST payloads |

## High-Level Architecture (HLD)

### Component Diagram
```ascii
+-------------------+       +--------------------+       +-------------------+
|                   |       |                    |       |                   |
|    Host App       | ----> | AnalyticsManager   | ----> |   Ring Buffer     |
|   (Any Thread)    |       |   (Singleton)      |       |   (Memory Queue)  |
|                   |       |                    |       |                   |
+-------------------+       +--------------------+       +-------------------+
                                                                   |
                                                             Background Flush
                                                               (Every 500ms)
                                                                   |
                                                                   v
                            +--------------------+       +-------------------+
                            |                    |       |                   |
                            |   BatchUploader    | <---- |   SQLite Store    |
                            |   (NetworkLayer)   |       |   (Persistence)   |
                            |                    |       |                   |
                            +--------------------+       +-------------------+
                                     |
                             Upload (GZIP, POST)
                                     |
                                     v
                            +--------------------+
                            |                    |
                            |  Analytics Server  |
                            |                    |
                            +--------------------+
```

### Component Responsibilities
| Component | Responsibility | iOS Implementation |
| :--- | :--- | :--- |
| AnalyticsManager | Public API surface, handles fast ingestion | Swift Actor or Serial Dispatch Queue |
| Ring Buffer | Holds events in memory temporarily to return instantly to caller | Fixed-size Array or Queue |
| SQLite Store | Safely stores events on disk | SQLite3 C-API or GRDB |
| BatchUploader | Reads events from DB, POSTs them, deletes on success | URLSession background tasks |
| EnvironmentMonitor| Listens for reachability, battery mode, and app lifecycle | NWPathMonitor, ProcessInfo |

### Data Flow
1. App calls `Analytics.shared.track("button_tap", props: ["id": 1])` from *any* thread.
2. `AnalyticsManager` immediately appends the event to a lock-free memory structure (Ring Buffer) and returns.
3. A background timer (every 500ms) or size threshold (100 items) flushes the Ring Buffer to `SQLite Store`.
4. The `BatchUploader` triggers a network upload if conditions are met (e.g., 50 events in DB, WiFi connected).
5. Events are converted to JSON, GZIP compressed, and POSTed.
6. Upon HTTP 200 OK, the successfully uploaded events are deleted from the `SQLite Store`.

## Data Models

### Core Entities
```swift
import Foundation

struct AnalyticsEvent: Codable {
    let id: String           // UUID
    let name: String         // e.g., "checkout_completed"
    let properties: Data?    // JSON encoded payload
    let timestamp: TimeInterval // UNIX epoch
    let sessionId: String
    
    init(name: String, properties: [String: Any]?) {
        self.id = UUID().uuidString
        self.name = name
        self.timestamp = Date().timeIntervalSince1970
        self.sessionId = SessionManager.shared.currentSessionId
        
        if let props = properties {
            self.properties = try? JSONSerialization.data(withJSONObject: props)
        } else {
            self.properties = nil
        }
    }
}
```

### Database Schema
```sql
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    properties BLOB,
    timestamp REAL NOT NULL,
    session_id TEXT NOT NULL,
    retry_count INTEGER DEFAULT 0
);

-- Index for efficient batch querying
CREATE INDEX idx_timestamp ON events(timestamp ASC);
```

## API Design

### Endpoints

**POST /v1/events/batch**
- **Headers**:
  - `Content-Type`: `application/json`
  - `Content-Encoding`: `gzip`
  - `Authorization`: `Bearer {sdk_api_key}`
- **Request Body (Uncompressed Example)**:
```json
{
  "device_info": { "os": "iOS 17.0", "model": "iPhone 15 Pro" },
  "events": [
    {
      "id": "abc-123",
      "name": "login_success",
      "timestamp": 1700000000.0,
      "properties": { "method": "apple_id" }
    }
  ]
}
```
- **Response**: `200 OK` (Indicates SDK can delete these events locally).

## Client Architecture Deep-Dives

### [Subsystem 1 — Thread-safe Lock-free Event Collection]
The `track()` method will be called thousands of times from various threads. Using standard locks (`NSLock`) can cause priority inversion and block the main thread. We use a Swift `Actor` to serialize access asynchronously, ensuring zero blocking.

```swift
import Foundation

actor EventQueue {
    private var buffer: [AnalyticsEvent] = []
    private let flushThreshold = 50
    private let store: SQLiteEventStore
    
    init(store: SQLiteEventStore) {
        self.store = store
    }
    
    // Called by the public SDK wrapper
    func enqueue(_ event: AnalyticsEvent) {
        buffer.append(event)
        
        if buffer.count >= flushThreshold {
            flushToDisk()
        }
    }
    
    func flushToDisk() {
        guard !buffer.isEmpty else { return }
        let eventsToSave = buffer
        buffer.removeAll(keepingCapacity: true) // Prevent memory re-allocation
        
        // Detach disk I/O to a background task
        Task.detached(priority: .background) {
            await self.store.insert(events: eventsToSave)
        }
    }
}

class Analytics {
    static let shared = Analytics()
    private let queue = EventQueue(store: SQLiteEventStore())
    
    // Public API - Fire and forget
    func track(_ name: String, properties: [String: Any]? = nil) {
        let event = AnalyticsEvent(name: name, properties: properties)
        Task {
            await queue.enqueue(event)
        }
    }
}
```

### [Subsystem 2 — Persistent Storage & App Lifecycle]
Memory is volatile. If the app crashes, items in the buffer are lost. We hook into `UIApplication.willResignActiveNotification` to immediately flush the buffer to SQLite before the OS suspends the app.

```swift
import UIKit

extension Analytics {
    func setupLifecycleObservers() {
        NotificationCenter.default.addObserver(forName: UIApplication.willResignActiveNotification, object: nil, queue: nil) { [weak self] _ in
            guard let self = self else { return }
            
            // Force flush immediately on backgrounding
            Task {
                await self.queue.flushToDisk()
                
                // Optionally trigger a background task to upload
                await self.triggerBackgroundUpload()
            }
        }
    }
    
    private func triggerBackgroundUpload() async {
        // Begin UIBackgroundTaskIdentifier to get ~30s of execution time from OS
        var backgroundTask: UIBackgroundTaskIdentifier = .invalid
        backgroundTask = UIApplication.shared.beginBackgroundTask {
            UIApplication.shared.endBackgroundTask(backgroundTask)
        }
        
        await BatchUploader.shared.uploadPendingEvents()
        
        UIApplication.shared.endBackgroundTask(backgroundTask)
    }
}
```

### [Subsystem 3 — Network & Battery Awareness]
Radios consume massive battery power when powering up. We should batch uploads, and alter our behavior based on the environment.

```swift
import Network

class EnvironmentMonitor {
    static let shared = EnvironmentMonitor()
    let monitor = NWPathMonitor()
    
    var isLowDataMode: Bool = false
    var isLowPowerMode: Bool {
        return ProcessInfo.processInfo.isLowPowerModeEnabled
    }
    
    func startMonitoring() {
        monitor.pathUpdateHandler = { path in
            self.isLowDataMode = path.isConstrained
        }
        monitor.start(queue: DispatchQueue.global(qos: .background))
    }
    
    func shouldUpload() -> Bool {
        // Don't upload telemetry if the user is in Low Data Mode (cellular constrained)
        if isLowDataMode { return false }
        
        // If low power mode, be more aggressive about holding batches (e.g. require 500 events instead of 50)
        return true
    }
}
```

## Performance & Optimizations
| Optimization | Technique | Benchmark/Impact |
| :--- | :--- | :--- |
| Compression | `gzip` the JSON body | Reduces 100KB payload to ~15-20KB |
| Serialization | Avoid `JSONSerialization` on main thread | Enqueue raw dictionaries, serialize to Data on background task |
| Database Writes | SQLite Transactions `BEGIN`/`COMMIT` | Inserting 100 items takes 2ms in a transaction vs 100ms individually |
| Memory Allocations | `removeAll(keepingCapacity: true)` | Reuses buffer memory, preventing ARC thrashing |

## Failure Modes & Fallbacks
| Failure Scenario | Detection | Fallback Strategy |
| :--- | :--- | :--- |
| API Rejects Payload (400)| HTTP Status Code | Drop the batch permanently to prevent infinite loops (malformed data). |
| Network Timeout (500)| HTTP Status / `URLError` | Keep events in SQLite, increment `retry_count`, use exponential backoff. |
| Database Corruption | SQLite throws fatal error | Delete the SQLite file entirely and recreate it. Data loss is acceptable for telemetry over a crash. |
| Disk Space Full | DB write fails | Drop events. Do not crash the host app. |

## Trade-off Analysis
| Decision | Option A | Option B | Chosen | Why |
| :--- | :--- | :--- | :--- | :--- |
| Memory Queue | `DispatchQueue.sync` | Swift `Actor` | Swift `Actor` | `DispatchQueue.sync` on a singleton can easily cause deadlocks in complex apps. Actors provide safe, non-blocking asynchronous access. |
| Persistence | CoreData | SQLite C-API / GRDB | SQLite / GRDB | CoreData has huge memory overhead and context merging complexities. Analytics requires raw, fast, append-only logs. |
| Upload Trigger | Every Event | Batched | Batched | Turning on the cellular radio for every single event drains the battery massively. Batching is strictly required by Apple guidelines. |

## Observability & Metrics
- **SDK Crash Rate**: Must be strictly 0.00%. The host app will uninstall the SDK if it causes crashes.
- **Delivery Rate**: Events created vs Events received by server. Target > 98%.
- **Average Payload Size**: Monitor to ensure GZIP is effective.
- **DB Size on Disk**: Monitor 99th percentile to ensure cleanup logic is working and we aren't eating gigabytes of user storage.

## Production Benchmarks Reference
| Metric | Target | Source / Justification |
| :--- | :--- | :--- |
| Batch Size (Firebase) | ~1 hour or 100 events | Firebase Analytics public documentation |
| Event Size | ~200-500 bytes | Average JSON representation |
| HTTP Request Overhead | ~500 bytes | TCP/TLS handshake overhead makes single-event sending horribly inefficient |

## Interview Tips
- **Zero Impact Rule**: Stress heavily that an Analytics SDK is a guest in the host app. It must NEVER block the main thread and NEVER crash the host app.
- **Fail Gracefully**: If the database is corrupted, delete it and lose the data. Do not crash.
- **GZIP Compression**: Always mention this. It shows senior-level awareness of mobile network constraints.
- **Low Power/Data Mode**: Showing awareness of `isLowPowerModeEnabled` and `NWPathMonitor` (`.isConstrained`) separates staff engineers from seniors.
