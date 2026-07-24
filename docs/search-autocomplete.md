# Design Mobile Search with Autocomplete & Offline Index

## Overview
A robust mobile search experience requires balancing immediate feedback, offline capabilities, and comprehensive remote results. Features like search autocomplete and offline indexing are heavily scrutinized in system design interviews because they touch on complex topics such as debouncing, concurrency, local data indexing (Tries vs. SQLite FTS), and network efficiency.

## Target Companies & Frequency
| Company | Why They Ask | Frequency |
| :--- | :--- | :--- |
| Google | Search is their core business; requires extreme latency optimization. | ★★★★★ |
| Airbnb | Complex offline availability and caching requirements for locations. | ★★★★★ |
| Spotify | Offline-first experience for downloaded catalogs. | ★★★★☆ |
| Booking.com | Auto-completion for cities and hotels with massive datasets. | ★★★★☆ |

## Scope Definition

### In Scope
- Local instant autocomplete via recent searches and a Trie.
- Server-side autocomplete with debouncing and request cancellation.
- Full search results with cursor-based pagination.
- Offline search indexing using SQLite FTS5 for small to medium datasets.

### Out of Scope
- Detailed backend inverted index architecture (Elasticsearch internals).
- Complex personalized ranking algorithms (ML models).
- UI rendering specifics (Diffable Data Sources) unless related to latency.

## Requirements

### Functional Requirements
1. **Instant Suggestions**: Show recent searches immediately and match typed prefixes against local data in < 10ms.
2. **Remote Autocomplete**: Fetch server suggestions with a ~200ms latency target, minimizing redundant requests.
3. **Full Search Results**: Load full results on submission with cursor pagination.
4. **Offline Search**: Search against a pre-downloaded catalog when offline.

### Non-Functional Requirements
| Requirement | Target | Source |
| :--- | :--- | :--- |
| **Local Search** | < 10ms | Trie/FTS5 Benchmarks |
| **Remote Autocomplete p99**| < 200ms | Google Search Standard |
| **Debounce Window** | 300ms | Google/Network Inspectors |
| **Offline Index Size** | < 10MB | App Store Guidelines/Optimization |

## High-Level Architecture (HLD)

### Component Diagram

```mermaid
flowchart TD
    subgraph iOS Client
        UI[Search UI / View] --> VM[Search ViewModel]
        VM --> DBNC[Search Debouncer]
        
        DBNC --> |Local Queries| LS[Local Search Engine]
        DBNC --> |Remote Queries| API[Search API Client]
        
        LS --> TRIE[In-Memory Trie (Recent)]
        LS --> FTS[(SQLite FTS5 Offline Index)]
        
        API --> |Network| GW[API Gateway]
    end
    
    subgraph Backend
        GW --> AS[Autocomplete Service]
        GW --> FS[Full Search Service]
        AS --> REDIS[(Redis Cache)]
        FS --> ES[(Elasticsearch)]
    end
```

### Component Responsibilities
| Component | Responsibility | iOS Implementation |
| :--- | :--- | :--- |
| **Search Debouncer** | Delays requests to prevent network spam. | Swift `Task` & `Task.sleep` |
| **Local Search Engine** | Fast, local string matching. | Prefix Trie / SQLite FTS5 |
| **Search API Client** | Manages in-flight requests and cancellations. | `URLSession` data tasks |
| **Search ViewModel** | Merges local and remote results. | `@Published` properties, Combine / async-await |

### Data Flow
1. **Keystroke**: User types a character.
2. **Local Path**: Immediately query local Trie and SQLite FTS5. Emit local suggestions to UI.
3. **Debounce**: Cancel previous tasks. Wait 300ms.
4. **Remote Path**: If no new keystrokes, fire API request.
5. **Merge**: Receive remote suggestions, merge with local, and update UI.

## Data Models

### Core Entities

```swift
import Foundation

struct Suggestion: Identifiable, Equatable {
    let id: String
    let text: String
    let type: SuggestionType
    let iconUrl: URL?
}

enum SuggestionType: String {
    case recent
    case localCatalog
    case remote
}

struct SearchResult: Identifiable {
    let id: String
    let title: String
    let subtitle: String
    let imageUrl: URL?
}
```

### Database Schema
```sql
-- Recent Searches
CREATE TABLE IF NOT EXISTS recent_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT UNIQUE,
    timestamp INTEGER,
    result_count INTEGER
);

-- Offline Catalog using FTS5 (Full Text Search)
CREATE VIRTUAL TABLE catalog USING fts5(
    id, name, type, rank
);
```

## API Design

### Endpoints

**1. Remote Autocomplete**
- **Method**: `GET`
- **Path**: `/v1/search/autocomplete?q={query}&limit=10`
- **Response**:
```json
{
  "request_id": "req-12345",
  "suggestions": [
    {
      "id": "item-789",
      "text": "Starbucks",
      "type": "remote"
    }
  ]
}
```

**2. Full Search Results**
- **Method**: `GET`
- **Path**: `/v1/search/results?q={query}&cursor={cursor_token}&limit=20`
- **Response**:
```json
{
  "results": [...],
  "next_cursor": "eyJvZmZzZXQiOjIwfQ=="
}
```

### Pagination Strategy
We use **cursor-based pagination** for full search results. Offset pagination (`offset=20`) is dangerous in search because if the index is updated or rankings change between requests, items might shift, causing duplicates or missing items. Cursor pagination uses a token representing the exact last seen item.

## Client Architecture Deep-Dives

### 1. Debouncing & Cancellation
Preventing API spam requires canceling previous requests and only firing after a pause. Swift Concurrency makes this elegant.

```swift
import Foundation

class SearchDebouncer {
    private var searchTask: Task<Void, Never>?
    private let delayNanoseconds: UInt64 = 300_000_000 // 300ms
    
    func debounce(query: String, action: @escaping (String) async -> Void) {
        // Cancel the existing task if user typed again
        searchTask?.cancel()
        
        searchTask = Task {
            do {
                // Wait for the debounce window
                try await Task.sleep(nanoseconds: delayNanoseconds)
                
                // If not cancelled during sleep, execute action
                if !Task.isCancelled {
                    await action(query)
                }
            } catch {
                // Task was cancelled, do nothing
            }
        }
    }
}
```
*Note: The API client must also cancel the underlying `URLSessionTask` and validate the `requestId` on response to prevent race conditions.*

### 2. Local Search with Prefix Trie
For extremely fast, in-memory matching of small datasets (like recent searches).

```swift
class TrieNode {
    var children: [Character: TrieNode] = [:]
    var isTerminal: Bool = false
    var suggestion: Suggestion?
}

class PrefixTrie {
    private let root = TrieNode()
    
    func insert(_ suggestion: Suggestion) {
        var current = root
        for char in suggestion.text.lowercased() {
            if current.children[char] == nil {
                current.children[char] = TrieNode()
            }
            current = current.children[char]!
        }
        current.isTerminal = true
        current.suggestion = suggestion
    }
    
    func search(prefix: String) -> [Suggestion] {
        var current = root
        for char in prefix.lowercased() {
            guard let next = current.children[char] else { return [] }
            current = next
        }
        // Perform DFS from current to collect all terminal suggestions
        return collectAll(node: current)
    }
    
    private func collectAll(node: TrieNode) -> [Suggestion] {
        var results = [Suggestion]()
        if node.isTerminal, let s = node.suggestion { results.append(s) }
        for child in node.children.values {
            results.append(contentsOf: collectAll(node: child))
        }
        return results
    }
}
```

### 3. Offline Search via SQLite FTS5
For medium catalogs (e.g., 100K cities), an in-memory Trie uses too much RAM. We use SQLite FTS5.

```swift
// Pseudo-code for FMDB / SQLite execution
func searchOfflineCatalog(query: String) -> [Suggestion] {
    // Append wildcard for prefix matching
    let ftsQuery = "\(query)*"
    let sql = "SELECT id, name, type FROM catalog WHERE catalog MATCH ? ORDER BY rank LIMIT 10"
    
    // Execute SQL on a background queue to avoid main thread hangs
    // Map ResultSet to [Suggestion]
}
```

## Performance & Optimizations
| Optimization | Technique | Benchmark/Impact |
| :--- | :--- | :--- |
| **Avoid Over-fetching** | 300ms Debounce. | Reduces API load by 70-80% for fast typists. |
| **Prevent Stale UI** | Request Cancellation / ID Matching. | Ensures final UI state matches input exactly. |
| **Background Querying** | Dispatch SQLite FTS queries to a background queue. | Prevents main thread hangs / dropped frames. |
| **Delta Updates** | Only fetch `catalog` diffs using `ETag`. | Reduces background data usage significantly. |

## Failure Modes & Fallbacks
| Failure Scenario | Detection | Fallback Strategy |
| :--- | :--- | :--- |
| **Network Offline** | NWPathMonitor or API Timeout. | Suppress remote errors, show only Local/Trie/FTS results. |
| **Out of Order Responses** | Request N-1 arrives after N. | UI filters out responses where `response.reqId != currentReqId`. |
| **Massive Offline Catalog** | > 50MB payload. | Switch to remote-only or enforce pagination on the download itself. |

## Trade-off Analysis
| Decision | Option A | Option B | Chosen | Why |
| :--- | :--- | :--- | :--- | :--- |
| **Pagination** | Offset | Cursor | **Cursor** | Prevents missing/duplicate items if search index mutates between requests. |
| **Local Indexing** | In-Memory Trie | SQLite FTS5 | **Both** | Trie for small datasets (Recent Searches, O(m) speed). FTS5 for larger offline catalogs (100k+ rows) to preserve memory. |

## Observability & Metrics
- **Autocomplete Latency**: Track time from keystroke to UI render (p50/p95/p99).
- **Zero-Result Rate**: Percentage of queries returning no results (signals poor relevance or catalog gaps).
- **Conversion Rate**: Search to Tap to Purchase/Play funnel.
- **Offline Index Freshness**: How old the local catalog is relative to the server.

## Production Benchmarks Reference
| Metric | Benchmark | Source |
| :--- | :--- | :--- |
| **Debounce Window** | ~300ms | Google Search / Network Inspector |
| **Autocomplete p99** | < 200ms | Google Internal Standard |
| **SQLite FTS5 Perf** | sub-10ms for 1M records | Empirical via iPhone 12 |
| **Recent Searches** | Max 10 entries | Google/Spotify Standard UX |

## Interview Tips
- ❌ **Common Mistake:** Missing the debounce. Fetching on every keystroke is an immediate red flag.
- ❌ **Common Mistake:** Suggesting offset pagination for dynamic search results.
- ❌ **Common Mistake:** Loading the entire offline catalog array into memory. Emphasize SQLite FTS.
- **Bonus:** Discuss how to handle typos. FTS5 handles this moderately well, but for Tries, you'd need to discuss Levenshtein distance algorithms.
- **Bonus:** Address the race condition explicitly (stale response overwriting fresh response) using Request IDs.
