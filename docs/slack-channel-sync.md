# Design Slack Mobile App — Multi-Workspace Channel Sync

## Overview
Designing a mobile messaging application like Slack requires handling real-time multi-workspace synchronization efficiently. This problem is frequently asked at FAANG and top-tier tech companies because it tests a candidate's ability to design a resilient real-time architecture, handle complex database schemas (multi-tenant/workspace isolation), and optimize for both battery life and perceived performance under poor network conditions.

## Target Companies & Frequency
| Company | Why They Ask | Frequency |
| :--- | :--- | :--- |
| Slack | Core product architecture; multi-workspace DB isolation is critical. | ★★★★★ |
| Salesforce | Parent company of Slack; enterprise collaboration focus. | ★★★★☆ |
| Microsoft | Teams has similar multi-tenant architecture and real-time needs. | ★★★★☆ |
| Meta | Messenger/WhatsApp rely heavily on SQLite and real-time syncing. | ★★★☆☆ |
| Discord | Similar server/channel structure with high-throughput WebSockets. | ★★★☆☆ |

## Scope Definition

### In Scope
- Multi-workspace database isolation (one DB per workspace).
- Real-time message, presence, and reaction synchronization via WebSockets.
- Unread badge count calculation across channels and workspaces.
- Thread pagination and channel loading (cursor-based).
- Optimistic UI updates for reactions and sending messages.
- Offline support and background syncing.

### Out of Scope
- Audio/Video calling (Huddles).
- Rich text editor implementation details.
- User registration and workspace creation.
- End-to-end encryption (E2EE) key exchange.
- Push notification delivery backend architecture.

## Requirements

### Functional Requirements
1. **Multi-Workspace**: Users can be logged into multiple workspaces simultaneously without data cross-contamination.
2. **Real-Time Sync**: Messages, reactions, and presence must sync in real-time across active workspaces.
3. **Unread Counts**: Accurate unread badge counts per channel and workspace, updated instantly.
4. **Offline Support**: Users can read cached messages and queue actions (send, react) while offline.
5. **Pagination**: Efficient loading of channel history and threaded replies.
6. **Presence**: Accurate user presence (active/away) indicators.

### Non-Functional Requirements
| Requirement | Target | Source |
| :--- | :--- | :--- |
| App Launch Time | < 2.0s | Apple HIG |
| Message Send Latency | < 200ms (Optimistic) | Slack Eng Blog |
| Real-time Event Latency | < 500ms (WebSocket) | Slack Eng Blog |
| Battery Drain | < 2% per hour active | iOS System Norms |
| Database Size limit | ~500MB per workspace | Mobile Constraints |
| Crash-free sessions | > 99.9% | Industry Standard |

## High-Level Architecture (HLD)

### Component Diagram

```mermaid
flowchart TD
    subgraph Client [iOS Application (MVVM)]
        UI[UI / SwiftUI Views]
        VM[ViewModels / ObservableObject]
        
        subgraph Services [Service Layer]
            WSM[WorkspaceSocketManager]
            WM[WorkspaceManager]
            SMM[SyncManager]
            BC[BadgeCalculator]
        end
        
        subgraph Storage [Data Layer]
            DB1[(SQLite: WS_1.db)]
            DB2[(SQLite: WS_2.db)]
            UD[UserDefaults]
        end
    end
    
    subgraph Network [API Gateway & Real-time]
        REST[REST API]
        WSS[WebSocket Gateway]
    end
    
    UI -->|Bind| VM
    VM -->|Fetch/Mutate| WM
    WM -->|Read/Write| DB1
    WM -->|Read/Write| DB2
    
    WSM <-->|Events| WSS
    SMM <-->|HTTP Req| REST
    
    WSM -->|Process Event| DB1
    WSM -->|Process Event| DB2
    
    DB1 -.->|Trigger| BC
    BC -.->|Update| VM
```

### Component Responsibilities
| Component | Responsibility | iOS Implementation |
| :--- | :--- | :--- |
| WorkspaceManager | Manages active workspaces, vends DB connections. | `actor WorkspaceManager` |
| WorkspaceSocketManager| Maintains WS connection per workspace, parses events. | `URLSessionWebSocketTask` per workspace |
| SyncManager | Handles REST API calls, background sync, pagination. | `URLSession` with background config |
| BadgeCalculator | Computes unread counts asynchronously off main thread. | `actor BadgeCalculator` with GCD background queue |
| Database (SQLite) | Stores channels, messages, users with workspace isolation.| `GRDB` or raw SQLite3 C-API wrappers |

### Data Flow
**Receiving a Real-Time Message:**
1. `WorkspaceSocketManager` receives a JSON `message` event over WebSocket.
2. It parses the JSON and identifies the target workspace.
3. The event is passed to `WorkspaceManager`, which gets the correct SQLite DB connection.
4. The message is inserted into the `messages` table.
5. The DB insert triggers an update to the `BadgeCalculator` (if the message is unread).
6. `@Published` properties in `ChannelViewModel` and `WorkspaceViewModel` are updated.
7. SwiftUI re-renders the views to show the new message and updated badge.

## Data Models

### Core Entities

```swift
import Foundation

struct Workspace: Identifiable, Codable {
    let id: String
    let name: String
    let iconUrl: URL?
    let token: String
}

struct Channel: Identifiable, Codable {
    let id: String
    let name: String
    let type: ChannelType
    var lastReadTs: Int64
    var memberCount: Int
    var isStarred: Bool
    
    enum ChannelType: String, Codable {
        case publicChannel = "public"
        case privateChannel = "private"
        case dm = "dm"
    }
}

struct Message: Identifiable, Codable {
    let id: String
    let channelId: String
    let senderId: String
    let text: String
    let ts: Int64
    let threadTs: Int64?
    let editedTs: Int64?
    var reactions: [Reaction]
    var localState: LocalState
    
    enum LocalState: String, Codable {
        case pending, sent, failed
    }
}

struct Reaction: Codable {
    let emoji: String
    var count: Int
    var userIds: [String]
}

struct User: Identifiable, Codable {
    let id: String
    let displayName: String
    let avatarUrl: URL?
    var statusEmoji: String?
    var statusText: String?
    var presence: PresenceStatus
    var lastPresenceUpdateTs: Int64
    
    enum PresenceStatus: String, Codable {
        case active, away
    }
}
```

### Database Schema
Each workspace has its own database (e.g., `workspace_A1B2C3.db`).

```sql
CREATE TABLE channels (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('public','private','dm')) NOT NULL,
    last_read_ts INTEGER NOT NULL DEFAULT 0,
    member_count INTEGER NOT NULL,
    is_starred INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    text TEXT NOT NULL,
    ts INTEGER NOT NULL,
    thread_ts INTEGER,
    edited_ts INTEGER,
    reactions TEXT, -- JSON encoded reactions
    local_state TEXT CHECK(local_state IN ('pending','sent','failed')) NOT NULL DEFAULT 'sent',
    FOREIGN KEY(channel_id) REFERENCES channels(id) ON DELETE CASCADE
);

-- Index for querying messages in a channel ordered by time (descending for pagination)
CREATE INDEX idx_messages_channel ON messages(channel_id, ts DESC);
CREATE INDEX idx_messages_thread ON messages(channel_id, thread_ts DESC) WHERE thread_ts IS NOT NULL;

CREATE TABLE users (
    id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    avatar_url TEXT,
    status_emoji TEXT,
    status_text TEXT,
    presence TEXT CHECK(presence IN ('active','away')) NOT NULL DEFAULT 'away',
    last_presence_update_ts INTEGER NOT NULL
);
```

## API Design

### Endpoints

**1. Fetch Channel History (Cursor Pagination)**
- **Method**: `GET`
- **Path**: `/api/conversations.history`
- **Headers**: `Authorization: Bearer {token}`
- **Query Params**: `channel={id}&cursor={cursor}&limit=50`
- **Response**:
```json
{
  "ok": true,
  "messages": [
    {
      "type": "message",
      "user": "U12345",
      "text": "Hello world",
      "ts": "1620000000.000100"
    }
  ],
  "has_more": true,
  "response_metadata": {
    "next_cursor": "dXNlcjpVMDYxTkZUVDI="
  }
}
```

**2. Send Message**
- **Method**: `POST`
- **Path**: `/api/chat.postMessage`
- **Body**:
```json
{
  "channel": "C123456",
  "text": "Hello team!",
  "client_msg_id": "550e8400-e29b-41d4-a716-446655440000" // Idempotency key
}
```

**3. WebSocket Connect**
- **Endpoint**: `wss://wss-primary.slack.com/?token={token}`
- **Events**:
  - Receive: `message`, `channel_marked`, `reaction_added`, `presence_change`, `ping`
  - Send: `pong`

### Pagination Strategy
Slack uses cursor-based pagination. Cursor pagination prevents duplicate items when new messages are inserted at the top of the feed while the user is paginating older messages. The client passes the `next_cursor` from the previous response to fetch the next 50 items.

## Client Architecture Deep-Dives

### 1. Multi-Workspace Database Isolation
One of the most critical aspects of Slack's architecture is strict workspace isolation. Using a single SQLite database for all workspaces risks data leakage (e.g., querying channels across workspaces by mistake) and makes deleting a workspace complex.

**Implementation**:
- Store databases in `Application Support/Workspaces/{workspaceId}.db`.
- The `WorkspaceManager` acts as a factory, ensuring only one active connection pool per DB.

```swift
actor WorkspaceManager {
    static let shared = WorkspaceManager()
    private var databases: [String: DatabaseConnection] = [:]
    
    func getDatabase(for workspaceId: String) throws -> DatabaseConnection {
        if let db = databases[workspaceId] {
            return db
        }
        
        let fileManager = FileManager.default
        let appSupportUrl = try fileManager.url(for: .applicationSupportDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
        let dbUrl = appSupportUrl.appendingPathComponent("Workspaces").appendingPathComponent("\(workspaceId).db")
        
        // Ensure directory exists
        try fileManager.createDirectory(at: dbUrl.deletingLastPathComponent(), withIntermediateDirectories: true)
        
        // Initialize GRDB/SQLite connection
        let dbQueue = try DatabaseQueue(path: dbUrl.path)
        let connection = DatabaseConnection(queue: dbQueue)
        databases[workspaceId] = connection
        
        return connection
    }
    
    func deleteWorkspaceData(workspaceId: String) throws {
        databases.removeValue(forKey: workspaceId)
        // Delete the .db file
    }
}
```

### 2. WebSocket Per Workspace & Battery Optimization
Slack requires a persistent WebSocket per active workspace. A user with 5 workspaces maintains 5 sockets. Sockets must handle reconnects with exponential backoff and respond to server `ping`s to maintain liveness.

```swift
class WorkspaceSocketManager {
    private var webSockets: [String: URLSessionWebSocketTask] = [:]
    private let urlSession = URLSession(configuration: .default)
    
    func connect(workspace: Workspace) {
        let url = URL(string: "wss://wss-primary.slack.com/?token=\(workspace.token)")!
        let task = urlSession.webSocketTask(with: url)
        webSockets[workspace.id] = task
        
        task.resume()
        listen(task: task, workspaceId: workspace.id)
    }
    
    private func listen(task: URLSessionWebSocketTask, workspaceId: String) {
        task.receive { [weak self] result in
            guard let self = self else { return }
            
            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    self.handleEvent(jsonString: text, workspaceId: workspaceId)
                case .data(let data):
                    break // Handle binary if needed
                @unknown default:
                    break
                }
                // Continue listening
                self.listen(task: task, workspaceId: workspaceId)
                
            case .failure(let error):
                self.reconnect(workspaceId: workspaceId, error: error)
            }
        }
    }
    
    private func handleEvent(jsonString: String, workspaceId: String) {
        // Parse event type
        // If "ping", send "pong"
        // If "message", insert into WorkspaceManager.getDatabase(workspaceId)
    }
}
```
**Battery Guard**: When `ProcessInfo.processInfo.isLowPowerModeEnabled` becomes true, non-active workspace websockets can be downgraded to periodic HTTP polling or disconnected entirely, relying on APNs for critical mentions.

### 3. Unread Badge Count Architecture
Unread counts (`totalUnread`) are computed dynamically by comparing message timestamps with the channel's `last_read_ts`. To avoid UI freezes, `COUNT(*)` must NEVER run on the main thread.

```swift
actor BadgeCalculator {
    func calculateTotalUnread(for workspaceId: String) async throws -> Int {
        let db = try await WorkspaceManager.shared.getDatabase(for: workspaceId)
        
        return try await Task.detached(priority: .userInitiated) {
            // Execute SQL: 
            // SELECT SUM(
            //   (SELECT COUNT(*) FROM messages m WHERE m.channel_id = c.id AND m.ts > c.last_read_ts)
            // ) FROM channels c
            
            return try db.queryTotalUnread()
        }.value
    }
}

// In ViewModel
@MainActor
class WorkspaceViewModel: ObservableObject {
    @Published var totalUnread: Int = 0
    let workspaceId: String
    
    func updateBadge() async {
        do {
            let calculator = BadgeCalculator()
            let count = try await calculator.calculateTotalUnread(for: workspaceId)
            self.totalUnread = count
            // Update OS app icon badge
            UNUserNotificationCenter.current().setBadgeCount(count)
        } catch {
            print("Failed to calculate badge")
        }
    }
}
```

### 4. Thread Pagination & Data Loading
Threads use lazy loading. When a user taps a thread, the client first queries local DB: `SELECT * FROM messages WHERE thread_ts = ? ORDER BY ts ASC`. It then calls `/api/conversations.replies` to fetch any new replies, updates the DB, and refreshes the UI.
For main channel pagination, when scrolling up, `next_cursor` triggers an API call. Received messages are inserted into SQLite, and `NSFetchedResultsController` or Combine publishers update the `DiffableDataSource` seamlessly.

### 5. Optimistic Reactions & Messages
When a user adds a 👍 reaction, the UI updates instantly.
1. Update `reactions` JSON column in SQLite for the specific message.
2. Fire `POST /api/reactions.add` in the background.
3. If the API fails (e.g., 500 error, network loss), revert the SQLite change and show a toast: "Failed to add reaction."
4. If successful, do nothing (local state is already correct).
The same applies to messages. Messages are inserted with `local_state = .pending`. The `client_msg_id` UUID prevents duplicates if a network retry occurs. Upon success, update to `.sent`.

## Performance & Optimizations
| Optimization | Technique | Benchmark/Impact |
| :--- | :--- | :--- |
| DB Isolation | One SQLite DB per workspace | Fast queries, 0% cross-leakage |
| Unread Calc | Background `Task.detached` `COUNT(*)` | 0ms main thread blocking |
| Idempotency | `client_msg_id` on POST requests | Eliminates duplicate messages |
| Jitter Backoff | Random ±20% delay on WS reconnects | Prevents thundering herd on server |
| Presence Decay | Client-side 5min TTL for active state | Reduces network spam for presence |

## Failure Modes & Fallbacks
| Failure Scenario | Detection | Fallback Strategy |
| :--- | :--- | :--- |
| WebSocket Disconnect | `URLSessionWebSocketTask` failure | Exponential backoff reconnect. Sync missing history via REST. |
| Message Send Failure | HTTP timeout or 500 | Mark local state `.failed`, show retry button. |
| DB Corruption | SQLite `SQLITE_CORRUPT` error | Delete `.db` file, re-sync from scratch from server. |
| Low Power Mode | `ProcessInfo` notification | Disconnect inactive workspace WS, rely on polling/APNs. |

## Trade-off Analysis
| Decision | Option A | Option B | Chosen | Why |
| :--- | :--- | :--- | :--- | :--- |
| Database Architecture | Single DB for all workspaces | One DB per workspace | One DB per workspace | Absolute data isolation, easier to drop workspace data on logout, smaller index trees. |
| Unread Computation | Pre-compute in DB on every insert | Calculate dynamically (`COUNT`) on demand | Dynamic with background caching | Pre-computing requires complex transactional logic. Background `COUNT(*)` with index is extremely fast (<10ms). |
| Real-time Protocol | Server-Sent Events (SSE) | WebSockets (WSS) | WebSockets | Slack requires bidirectional real-time (typing indicators, presence). SSE is unidirectional. |

## Observability & Metrics
- **WebSocket Reconnect Rate**: Monitor how often clients reconnect. High rates indicate bad network management.
- **Message Send Latency (P99)**: Time from pressing "Send" to receiving server ACK. Target < 200ms.
- **App Launch to TTI (Time to Interact)**: Ensure SQLite loads and UI renders < 2s.
- **SQLite DB Size**: Track 99th percentile DB size per workspace to plan for eviction policies (e.g., deleting messages > 90 days old if size > 500MB).
- **Crash Rate**: Monitor `WorkspaceManager` and CoreData/GRDB concurrency crashes. Target > 99.9% crash-free.

## Production Benchmarks Reference
| Metric | Real World Number | Source |
| :--- | :--- | :--- |
| Daily Active Users | 32M+ | Slack 2023 Earnings |
| Ping Interval | 30s | Slack RTM API Docs |
| Message Page Size | 50 messages | Slack API Defaults |
| SQLite Architecture | 1 DB per workspace | Slack Engineering Blog (2022) |
| Badge Update Latency | < 500ms | Slack App Observation |

## Interview Tips
- **Emphasize Data Isolation**: Always start by separating databases per workspace. This shows you understand enterprise security and data leakage risks.
- **Main Thread Performance**: Interviewers will test if you block the main thread with large `COUNT(*)` queries for unread badges. Be explicit about background queues.
- **WebSocket Management**: Don't say "one websocket per channel". That's a classic junior mistake. It's one websocket per *workspace* (multiplexed).
- **Idempotency**: Mentioning `client_msg_id` for message sending demonstrates deep understanding of distributed systems and network retries.
- **Optimistic UI**: Walk through the exact rollback mechanism for a failed reaction or message send.
