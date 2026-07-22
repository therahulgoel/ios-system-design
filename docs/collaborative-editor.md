# Collaborative Document Editor (Google Docs / Notion / Quip)

## Overview
Designing a collaborative document editor involves complex distributed systems concepts applied to mobile clients. It tests a candidate's grasp of conflict resolution, optimistic UI updates, and synchronization mechanisms when multiple users edit the same text simultaneously.

## Target Companies & Frequency
| Company | Why They Ask | Frequency |
|---------|--------------|-----------|
| Google | Google Docs is the pioneer; rigorous testing on concurrency. | ★★★★☆ |
| Notion | Heavy mobile usage; local-first offline capabilities. | ★★★★☆ |
| Microsoft | Office 365 / Loop rely on these exact principles. | ★★★★☆ |
| Dropbox | Dropbox Paper requires deep understanding of sync engines. | ★★★☆☆ |

## Scope Definition

### In Scope
- Real-time text editing by multiple concurrent users.
- Conflict resolution mechanisms.
- Offline editing capabilities and background sync.
- Optimistic UI updates.
- Cursor and presence sharing.

### Out of Scope
- Rich text formatting (bold, italic, embedded images) - limit to plain text / simple blocks.
- Document permissions and ACLs.
- Folder hierarchies and search.
- Version history UI.

## Requirements

### Functional Requirements
1. Users can open and edit a document concurrently with others.
2. Changes appear in real-time to other users.
3. Edits made while offline are saved and synced upon reconnection without overwriting others' work.
4. Users can see where others are currently typing (presence).

### Non-Functional Requirements
| Requirement | Target | Source |
|-------------|--------|--------|
| Sync Latency | < 100ms | Collaborative Editing HCI Studies |
| Local Input Latency | < 16ms (60fps) | iOS HIG |
| Concurrent Editors | Up to 100 | Google Docs Limits |
| Presence Broadcast | Every 500ms | Standard UI Debounce |

## High-Level Architecture (HLD)

### Component Diagram
```text
[iOS Client]
    │
    ├─► UI Layer (TextKit / CoreText ViewModels)
    │
    ├─► Domain Layer (OT Engine / CRDT, Optimistic Applier)
    │
    ├─► Repository Layer (Local OpLog, Snapshot Cache)
    │      │
    │      └─► SQLite (Append-only Op Log)
    │
    └─► Network Layer
           │
           ├─► WebSocketManager (Real-time Ops & Presence)
           └─► REST API (Initial Snapshot Fetch)

[Backend Infrastructure]
    │
    ├─► WebSocket Gateway
    ├─► OT Server (Single Source of Truth, Sequence Assigner)
    ├─► Redis (Pub/Sub for Presence)
    └─► Document Database (MongoDB / DynamoDB for Snapshots & Op History)
```

### Component Responsibilities
| Component | Responsibility | iOS Implementation |
|-----------|----------------|--------------------|
| OperationTransformer | Handles OT math (transforming client ops against server ops). | Pure Swift struct/class |
| OpLogRepository | Persists local pending ops and server applied ops. | SQLite |
| DocumentViewModel | Manages Text view state, handles local inputs. | `ObservableObject` |
| SyncEngine | Coordinates between OpLog, OT Engine, and Network. | Actor / Background Queue |

### Data Flow
1. **Local Edit**: User types character -> Generated Op -> Applied locally immediately (Optimistic UI) -> Saved to pending queue.
2. **Sync**: Send pending Op + `baseRevision` to server via WebSocket.
3. **Server Transform**: Server receives Op. If server revision > `baseRevision`, server transforms Op against intermediate history, applies, broadcasts to others, and ACKs client with `newRevision`.
4. **Client ACK**: Client receives ACK, removes Op from pending, updates local revision.
5. **Remote Edit**: Client receives remote Op -> Transforms against local pending ops -> Applies to UI.

## Data Models

### Core Entities
```swift
import Foundation

enum OpType: String, Codable {
    case insert
    case delete
    case retain // For rich text, but useful for basic OT to skip chars
}

struct Operation: Codable, Equatable {
    let id: String // UUID
    let type: OpType
    let position: Int
    let text: String
    
    // Generates a reverse operation for local undo
    func inverse() -> Operation {
        switch type {
        case .insert: return Operation(id: UUID().uuidString, type: .delete, position: position, text: text)
        case .delete: return Operation(id: UUID().uuidString, type: .insert, position: position, text: text)
        case .retain: return self
        }
    }
}

struct DocumentSnapshot: Codable {
    let id: String
    let content: String
    let revision: Int
}
```

### Database Schema
```sql
CREATE TABLE document_snapshots (
    doc_id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    revision INTEGER NOT NULL
);

-- Append-only log of operations
CREATE TABLE operation_log (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    revision INTEGER, -- Null if pending locally
    op_type TEXT NOT NULL,
    position INTEGER NOT NULL,
    text_content TEXT,
    state INTEGER NOT NULL, -- 0: pending, 1: synced
    created_at REAL NOT NULL,
    FOREIGN KEY(doc_id) REFERENCES document_snapshots(doc_id)
);

CREATE INDEX idx_oplog_state ON operation_log(doc_id, state);
```

## API Design

### Endpoints

**1. GET /v1/docs/{id}/snapshot**
- **Response**:
```json
{
  "doc_id": "doc-123",
  "content": "Hello World",
  "revision": 42
}
```

**2. WebSocket Sync Channel**
- **Payloads**:
```json
// Client -> Server (Submit Ops)
{
  "action": "submit_ops",
  "base_revision": 42,
  "ops": [
    { "type": "insert", "position": 5, "text": "!" }
  ]
}

// Server -> Client (Broadcast/ACK)
{
  "action": "apply_ops",
  "new_revision": 43,
  "ops": [
    { "type": "insert", "position": 5, "text": "!" }
  ]
}

// Client -> Server (Presence)
{
  "action": "presence",
  "user_id": "user-1",
  "cursor_position": 6
}
```

## Client Architecture Deep-Dives

### 1. Operational Transformation (OT) Engine
OT is the core algorithm. If two clients edit at the same time, their operations must be mathematically transformed so the final document state matches regardless of application order.

```swift
class OperationTransformer {
    /// Transforms Op A against Op B. 
    /// Assumes both ops were generated at the same base revision.
    static func transform(clientOp: Operation, serverOp: Operation) -> Operation {
        // Simplified OT logic for single character insert/delete
        var transformedPosition = clientOp.position
        
        if serverOp.type == .insert {
            if serverOp.position < clientOp.position {
                // Server inserted before client, shift client right
                transformedPosition += serverOp.text.count
            } else if serverOp.position == clientOp.position {
                // Tie breaker: standard is server wins, or rely on site/user ID
                // Let's assume server op comes first
                transformedPosition += serverOp.text.count
            }
        } else if serverOp.type == .delete {
            if serverOp.position < clientOp.position {
                // Server deleted before client, shift client left
                let shift = min(clientOp.position - serverOp.position, serverOp.text.count)
                transformedPosition -= shift
            }
        }
        
        return Operation(
            id: clientOp.id,
            type: clientOp.type,
            position: transformedPosition,
            text: clientOp.text
        )
    }
}
```

### 2. Synchronization & Pending Queue
The client must maintain a `localRevision` and a queue of `pendingOps`.

```swift
actor SyncEngine {
    private var localRevision: Int
    private var pendingOps: [Operation] = []
    private var documentContent: String
    
    init(snapshot: DocumentSnapshot) {
        self.localRevision = snapshot.revision
        self.documentContent = snapshot.content
    }
    
    // 1. User types -> Optimistic application
    func applyLocalEdit(op: Operation) {
        documentContent = apply(op: op, to: documentContent)
        pendingOps.append(op)
        // Trigger network send: send(ops: pendingOps, baseRevision: localRevision)
    }
    
    // 2. Network receives server ops
    func receiveServerOps(serverOps: [Operation], newRevision: Int) {
        // We must transform pending ops against incoming server ops
        var transformedServerOps = serverOps
        
        for serverOp in serverOps {
            var currentServerOp = serverOp
            
            for (index, pendingOp) in pendingOps.enumerated() {
                // Transform pending op against server op
                let transformedPending = OperationTransformer.transform(clientOp: pendingOp, serverOp: currentServerOp)
                // Transform server op against pending op (for local application)
                currentServerOp = OperationTransformer.transform(clientOp: currentServerOp, serverOp: pendingOp)
                
                pendingOps[index] = transformedPending
            }
            
            // Apply the transformed server op to local document
            documentContent = apply(op: currentServerOp, to: documentContent)
        }
        
        // Remove pending ops that were ACK'd by server (simplified matching)
        // Update revision
        self.localRevision = newRevision
    }
    
    private func apply(op: Operation, to string: String) -> String {
        // String manipulation logic
        var result = string
        // ... apply index manipulation
        return result
    }
}
```

### 3. Local Persistence & Offline Mode
In offline mode, all local edits are appended to the SQLite `operation_log` as pending. The document can always be reconstructed by loading the last snapshot and replaying the log. When reconnecting, the background task batches the pending ops and sends them.

## Performance & Optimizations
| Optimization | Technique | Benchmark/Impact |
|--------------|-----------|------------------|
| Text Rendering | Use TextKit / `NSAttributedString` directly instead of SwiftUI `TextEditor` for large docs. | Avoids main thread lockups on >10k words. |
| Batching Ops | Group multiple character inserts within 500ms into a single string insert Op. | Reduces WebSocket traffic by 80%. |
| Snapshotting | Server periodically (every 100 ops) saves a hard snapshot. | Client load time O(1) instead of replaying thousands of ops. |

## Failure Modes & Fallbacks
| Failure Scenario | Detection | Fallback Strategy |
|------------------|-----------|-------------------|
| Desync / Bad OT | Client hash mismatch with Server hash | Client forces a full snapshot reload, discarding invalid local ops. |
| Prolonged Offline | Local ops > 1000 | Warn user; auto-compact local ops where possible (e.g. insert+delete same char = no-op). |

## Trade-off Analysis
| Decision | Option A | Option B | Chosen | Why |
|----------|----------|----------|--------|-----|
| Algorithm | CRDTs | OT (Op Transformation) | OT | OT is standard for centralized servers (Google Docs). CRDTs (Figma) use more memory and metadata (tombstones) per character, which can bloat mobile memory. |
| Text Input | SwiftUI `TextEditor` | `UITextView` / TextKit | `UITextView` | Standard UI components don't expose character-level precise offsets and mutations easily; TextKit allows granular control. |
| Sync Protocol | REST Polling | WebSockets | WebSockets | 100ms latency requirement makes polling unviable. |

## Observability & Metrics
- **Sync Latency**: Time from local edit to server ACK.
- **Desync Rate**: Number of times client hashes mismatch server hashes (critical metric for OT correctness).
- **Conflict Resolution Time**: CPU time spent in `OperationTransformer` per loop.

## Production Benchmarks Reference
| Metric | Value | Source |
|--------|-------|--------|
| Tech Stack | OT via central server | Google Docs Engineering |
| Alternative Stack| CRDTs via peer-to-peer | Figma / Automerge |
| Op Batching | 500ms or word-boundary | Common practice |

## Interview Tips
- **CRDT vs OT**: You WILL be asked this. Know that CRDTs resolve conflicts mathematically without a central server by assigning unique IDs to every character. OT relies on a central server to dictate order.
- **Optimistic UI**: Emphasize that the user should NEVER feel blocked by the network.
- **Text Frameworks**: Acknowledge that standard SwiftUI bindings (`@State var text`) break down here; you need precise offset control via `UITextViewDelegate`.
