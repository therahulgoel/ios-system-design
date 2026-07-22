# Offline-First Data Sync Engine (Notes / Tasks / Drive)

## Overview
An offline-first data sync engine is designed to ensure that users can read, write, and interact with the application seamlessly regardless of their network connection state. This architecture is heavily asked in FAANG interviews for productivity and content creation applications, as it forces candidates to tackle complex problems like local state management, eventual consistency, background synchronization, and conflict resolution, avoiding the pitfall of blocking the UI on network requests.

## Target Companies & Frequency
| Company | Why They Ask | Frequency |
| :--- | :--- | :--- |
| Google | Google Drive, Docs, Keep rely heavily on offline availability and collaborative sync. | ★★★★☆ |
| Apple | Notes, iCloud Drive, Reminders use local-first principles and background sync extensively. | ★★★★★ |
| Dropbox | Core business is file synchronization and offline availability. | ★★★★★ |
| Notion | Heavy emphasis on block-based offline-first editing and conflict resolution. | ★★★★☆ |
| Microsoft | OneDrive, To Do, and Outlook mobile apps are built around offline sync engines. | ★★★★☆ |

## Scope Definition

### In Scope
- Local-first architecture (SQLite as single source of truth)
- Background syncing mechanisms (pushing local changes to the server)
- Delta sync for pulling updates (fetching only changed records)
- Basic conflict resolution (Last-Write-Wins based on server timestamp)
- Optimistic UI updates
- Handling background tasks (BGAppRefreshTask, BGProcessingTask)
- Batch syncing to reduce round-trips
- Database schema for managing local vs. remote state

### Out of Scope
- Real-time collaborative editing using Operational Transformation (OT)
- Rich media (images/video) uploading and processing pipeline (focus is on structured data)
- Authentication flows and session management
- Cross-device push notifications for instant updates

## Requirements

### Functional Requirements
1. The app must allow users to view, create, edit, and delete items while completely offline.
2. Changes made offline must automatically sync to the server when network connectivity is restored.
3. The UI must reflect changes instantly without waiting for network acknowledgment (Optimistic UI).
4. The client must periodically fetch changes made on other devices (delta sync).
5. The system must handle conflicts automatically (e.g., same record edited locally and remotely).
6. Deleted items must be fully removed from the server and other devices.

### Non-Functional Requirements
| Requirement | Target | Source |
| :--- | :--- | :--- |
| UI Responsiveness | < 16ms per frame (60fps) | Apple Human Interface Guidelines |
| Background Task Max Runtime | < 30 seconds | Apple BGTaskScheduler Docs |
| Local Read/Write Latency | < 50ms | Typical SQLite performance |
| Battery Impact | < 2% total drain per day | iOS Background Execution Limits |
| Batch Sync Limits | Up to 50 records per batch | Standard REST API best practices |

## High-Level Architecture (HLD)

### Component Diagram

```ascii
                      +-------------------+
                      |   Cloud Backend   |
                      |  (Sync API, DB)   |
                      +---------+---------+
                                ^
                                | HTTP Push/Pull (JSON)
                                v
+-------------------------------------------------------------+
|                         iOS Client                          |
|                                                             |
|  +-------------+       +---------------+                    |
|  |             |       |               |                    |
|  | UI (SwiftUI)| <---> |   ViewModel   |                    |
|  |             |       | (Observable)  |                    |
|  +-------------+       +-------+-------+                    |
|                                ^                            |
|                                | Combine / async stream     |
|                                v                            |
|  +-------------+       +---------------+                    |
|  |             |       |               |  (Triggers sync)   |
|  | Local  DB   | <---> |  Sync Engine  | <-----------------+|
|  | (SQLite)    |       |               |                    |
|  +-------------+       +-------+-------+                    |
|                                ^                            |
|                                |                            |
|                        +-------+-------+                    |
|                        | Background    |                    |
|                        | Task Scheduler|                    |
|                        +---------------+                    |
+-------------------------------------------------------------+
```

### Component Responsibilities
| Component | Responsibility | iOS Implementation |
| :--- | :--- | :--- |
| ViewModel | Bridges UI and data, holds transient state | `@MainActor class`, `ObservableObject` |
| LocalRepository | Manages all local reads and writes, single source of truth | GRDB, CoreData, or raw SQLite wrapper |
| SyncEngine | Orchestrates push/pull operations and conflict resolution | Actor, generic sync coordinator class |
| API Client | Executes network requests | `URLSession`, Request/Response parsing |
| BGTaskScheduler | Schedules periodic background syncs | `BGAppRefreshTask`, `BGProcessingTask` |

### Data Flow
1. **User Action**: User creates/edits a note in the UI.
2. **Local Write**: ViewModel calls `LocalRepository.save()`. The record is written to SQLite with `is_dirty = 1` and a `local_updated_at` timestamp.
3. **UI Update**: The SQLite write succeeds immediately. The UI updates optimistically based on the local database change.
4. **Sync Trigger**: `LocalRepository` notifies the `SyncEngine` that dirty records exist.
5. **Network Push**: `SyncEngine` batches dirty records and sends a `POST /sync/push` request.
6. **Server Acknowledgment**: Server processes the batch, resolves any conflicts, and returns the updated `server_id` and `server_updated_at`.
7. **Local Cleanup**: `SyncEngine` updates the local database: clears `is_dirty`, updates `server_id`, and updates `server_updated_at`.

## Data Models

### Core Entities

```swift
import Foundation

/// Represents a synchronizable entity (e.g., a Note)
struct Note: Identifiable, Codable, Equatable {
    /// Local UUID, generated instantly on the client
    let id: String 
    
    /// The actual content/payload
    var content: String
    
    /// Timestamp of the last local change
    var localUpdatedAt: Date
    
    /// Timestamp of the last known server change. Nil if never synced.
    var serverUpdatedAt: Date?
    
    /// The ID assigned by the server (if different from local, or used for remote linking)
    var serverId: String?
    
    /// True if the record has local changes not yet pushed to the server
    var isDirty: Bool
    
    /// True if the record was deleted locally (Tombstone pattern)
    var isDeleted: Bool
    
    init(id: String = UUID().uuidString, content: String) {
        self.id = id
        self.content = content
        self.localUpdatedAt = Date()
        self.isDirty = true
        self.isDeleted = false
    }
}
```

### Database Schema

```sql
CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    local_updated_at REAL NOT NULL,
    server_updated_at REAL,
    server_id TEXT,
    is_dirty INTEGER NOT NULL DEFAULT 0,
    is_deleted INTEGER NOT NULL DEFAULT 0
);

-- Index to quickly find records that need to be pushed
CREATE INDEX idx_notes_dirty ON notes(is_dirty) WHERE is_dirty = 1;

-- Index to quickly filter out deleted records for the UI
CREATE INDEX idx_notes_deleted ON notes(is_deleted);
```

## API Design

### Endpoints

#### 1. Push Changes (Client -> Server)
**POST** `/v1/sync/push`
Pushes local modifications to the server in batches.

**Request Body:**
```json
{
  "last_sync_token": "timestamp_or_opaque_string_from_last_pull",
  "records": [
    {
      "client_id": "uuid-1234",
      "content": "Meeting notes...",
      "local_updated_at": 1690001000.0,
      "is_deleted": false
    },
    {
      "client_id": "uuid-5678",
      "is_deleted": true,
      "local_updated_at": 1690002000.0
    }
  ]
}
```

**Response Body:**
```json
{
  "accepted_records": [
    {
      "client_id": "uuid-1234",
      "server_id": "srv-9876",
      "server_updated_at": 1690001005.0
    }
  ],
  "conflicts": [
    {
      "client_id": "uuid-5678",
      "server_record": {
         "server_id": "srv-5555",
         "content": "Conflicting content from another device",
         "server_updated_at": 1690002500.0,
         "is_deleted": false
      }
    }
  ]
}
```

#### 2. Pull Changes (Server -> Client)
**GET** `/v1/sync/pull?since={last_sync_token}&limit=100`
Fetches all records modified on the server since the last sync token.

**Response Body:**
```json
{
  "next_sync_token": "timestamp_or_opaque_string_for_next_time",
  "has_more": false,
  "records": [
    {
      "server_id": "srv-1111",
      "client_id": "uuid-abc",
      "content": "New note from iPad",
      "server_updated_at": 1690003000.0,
      "is_deleted": false
    }
  ]
}
```

### Pagination Strategy
Use **Cursor-based pagination** (using `sync_token` or a high-water mark timestamp) rather than offset pagination. 
Offsets fail if records are added/deleted during pagination. Cursors guarantee that the client resumes exactly where it left off.

## Client Architecture Deep-Dives

### [Subsystem 1 — The Sync Engine Orchestrator]
The `SyncEngine` is an actor that serializes sync operations to prevent race conditions. It handles the push and pull loops.

```swift
actor SyncEngine {
    private let api: NetworkService
    private let db: LocalRepository
    private var isSyncing = false
    
    init(api: NetworkService, db: LocalRepository) {
        self.api = api
        self.db = db
    }
    
    func sync() async {
        guard !isSyncing else { return }
        isSyncing = true
        defer { isSyncing = false }
        
        do {
            // 1. Push local changes first
            try await pushLocalChanges()
            
            // 2. Pull remote changes
            try await pullRemoteChanges()
            
        } catch {
            print("Sync failed: \(error)")
            // Retry logic or exponential backoff handled by caller/scheduler
        }
    }
    
    private func pushLocalChanges() async throws {
        let dirtyRecords = try db.fetchDirtyRecords(limit: 50)
        guard !dirtyRecords.isEmpty else { return }
        
        let lastSyncToken = try db.getLastSyncToken()
        let response = try await api.push(records: dirtyRecords, token: lastSyncToken)
        
        try db.inTransaction { transaction in
            for accepted in response.acceptedRecords {
                transaction.markClean(clientId: accepted.clientId, 
                                      serverId: accepted.serverId, 
                                      serverUpdatedAt: accepted.serverUpdatedAt)
            }
            for conflict in response.conflicts {
                // Conflict resolution logic
                transaction.resolveConflict(clientRecordId: conflict.clientId, 
                                            serverRecord: conflict.serverRecord)
            }
        }
    }
    
    private func pullRemoteChanges() async throws {
        var hasMore = true
        var currentToken = try db.getLastSyncToken()
        
        while hasMore {
            let response = try await api.pull(since: currentToken)
            
            try db.inTransaction { transaction in
                for record in response.records {
                    transaction.upsertFromRemote(record)
                }
                transaction.saveSyncToken(response.nextSyncToken)
            }
            
            hasMore = response.hasMore
            currentToken = response.nextSyncToken
        }
    }
}
```

### [Subsystem 2 — Background Tasks Integration]
To keep data fresh, we integrate with iOS `BGTaskScheduler`.

```swift
import BackgroundTasks

class BackgroundSyncManager {
    static let shared = BackgroundSyncManager()
    private let syncTaskIdentifier = "com.company.app.sync"
    
    func registerTasks(engine: SyncEngine) {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: syncTaskIdentifier, using: nil) { task in
            self.handleSync(task: task as! BGAppRefreshTask, engine: engine)
        }
    }
    
    func scheduleNextSync() {
        let request = BGAppRefreshTaskRequest(identifier: syncTaskIdentifier)
        // System minimum is ~15 mins, but system ultimately decides
        request.earliestBeginDate = Date(timeIntervalSinceNow: 15 * 60) 
        
        do {
            try BGTaskScheduler.shared.submit(request)
        } catch {
            print("Could not schedule app refresh: \(error)")
        }
    }
    
    private func handleSync(task: BGAppRefreshTask, engine: SyncEngine) {
        // Schedule the next one right away
        scheduleNextSync()
        
        // Expiration handler: Apple mandates max 30s for background tasks
        task.expirationHandler = {
            // Cancel network requests and halt sync loop
            // In a real app, pass a Task.cancel() or cancellation token to the engine
            print("Background task running out of time!")
        }
        
        Task {
            await engine.sync()
            task.setTaskCompleted(success: true)
        }
    }
}
```

### [Subsystem 3 — Conflict Resolution Strategy]
For standard entities (like a Note title or simple task), we use a **Last-Write-Wins (LWW)** strategy based on the server timestamp. 

When a conflict occurs:
1. Client pushes a record with `local_updated_at` = T1, but the server sees a newer record with `server_updated_at` = T2 (where T2 > T1).
2. Server rejects the push and returns a conflict.
3. Client's `SyncEngine` overwrites the local record with the server's version.

For complex entities (e.g., collaborative rich text), a **CRDT (Conflict-free Replicated Data Type)** or **Operational Transformation (OT)** is necessary, but that often lives as an opaque blob in the database and requires dedicated merge functions.

## Performance & Optimizations
| Optimization | Technique | Benchmark/Impact |
| :--- | :--- | :--- |
| **Batching** | Send up to 50 records per push request | Reduces HTTP overhead; cuts sync time by 80% for bulk edits |
| **Delta Sync** | Send `last_sync_token` so server only returns changes | Reduces payload size from MBs to KBs |
| **Tombstones** | Mark items as `is_deleted=1` locally instead of deleting | Allows sync engine to propagate deletions to server safely |
| **Indexes** | `CREATE INDEX` on `is_dirty` | Reduces query time for finding sync candidates from O(N) to O(1) |

## Failure Modes & Fallbacks
| Failure Scenario | Detection | Fallback Strategy |
| :--- | :--- | :--- |
| **Device Offline** | `URLError.notConnectedToInternet` | Silent failure for sync engine. UI functions perfectly via SQLite. Retry when connection restored (NWPathMonitor). |
| **Server 500 / Timeout** | HTTP 5xx or timeout error | Exponential backoff for retries. Do not block UI. |
| **Sync Token Invalidated** | Server returns 400 or special error | Client clears its local sync token and performs a full pull (re-downloading all state) and reconciles. |
| **Database Corruption** | SQLite read/write throws fatal error | Delete local DB and force a full re-sync from server. Log to Crashlytics. |

## Trade-off Analysis
| Decision | Option A | Option B | Chosen | Why |
| :--- | :--- | :--- | :--- | :--- |
| **Pagination** | Offset/Limit | Cursor-based (Sync Token) | **Cursor-based** | Data changes rapidly; offset pagination leads to duplicate or skipped records. |
| **Conflict Resolution** | Ask User via UI | Last-Write-Wins (LWW) | **LWW** | Asking the user blocks background syncing and creates friction. LWW is industry standard for non-collaborative data. |
| **Local DB** | Core Data | raw SQLite / GRDB | **GRDB / SQLite** | Much easier to control thread safety and execute exact SQL queries (like bulk upserts). Avoids Core Data context merging complexities. |

## Observability & Metrics
- **Sync Success Rate**: Must be > 99.5%.
- **Sync Duration**: Measure p50 and p99 time taken to complete a push/pull cycle. Target p99 < 5 seconds.
- **Conflict Rate**: Track how often conflicts happen. If high, LWW might be destroying user data too often.
- **Dirty Record Queue Length**: If this grows unbounded, it means the client is failing to push changes (metrics alert!).
- **Background Task Completion Rate**: Track how often iOS kills the task due to the 30-second limit.

## Production Benchmarks Reference
| Benchmark | Value | Source |
| :--- | :--- | :--- |
| BGAppRefreshTask execution limit | ~30 seconds | Apple Developer Documentation |
| Minimum BG interval | ~15 minutes (system dependent) | Apple Developer Documentation |
| Optimal Batch Size | 50-100 records per request | REST API Best Practices / Firebase |
| Frame render target | 16.6ms (60 fps) | Apple Human Interface Guidelines |

## Interview Tips
- **Start with the DB**: For an offline-first app, always start your design by defining the local SQLite schema and the concept of `is_dirty`. The database is your API to the UI.
- **Never block the UI**: Emphasize that the UI *never* waits for a network request to finish. UI reads/writes to DB, DB syncs in background.
- **Tombstones**: Candidates often forget how to handle deletions. You must explain the tombstone pattern (`is_deleted=true`), otherwise deleted records will just get re-downloaded from the server.
- **Idempotency**: Ensure your sync APIs are idempotent. If a push request times out but actually succeeded on the server, a retry should not create duplicates.
