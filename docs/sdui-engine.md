Server-Driven UI (SDUI) Engine & Dynamic Layout Framework
## Overview
Server-Driven UI (SDUI) allows backend services to dictate the UI structure, layout, and content without requiring app updates. It is heavily asked in FAANG/Top-tier interviews because it tests complex state management, generic parsing, fallback strategies, and component registries while keeping the client lightweight and robust.

## Target Companies & Frequency
| Company | Why They Ask | Frequency |
|---------|--------------|-----------|
| Uber | Core to their dynamic home feed and ride-booking flows. | ★★★★★ |
| Meta | Used heavily in Instagram Shop and Facebook Feed. | ★★★★★ |
| Google | Used in Google Pay (Tez) and Play Store. | ★★★★☆ |
| Grab | Central to their super-app modularity. | ★★★★★ |

## Scope Definition

### In Scope
- SDUI component schema design (JSON contract with versioning).
- Dynamic ComponentRegistry mapping string types to native SwiftUI views.
- LayoutResolver for handling flex/stack configurations from the server.
- FallbackEngine for offline support using disk caching.
- ActionHandler for deep links, native routing, and web fallbacks.
- Schema versioning strategy and compatibility checks.
- Analytics injection via server-defined payload.
- Caching strategy with TTL and force-refresh mechanisms.

### Out of Scope
- Backend implementation details of the CMS generating the SDUI.
- Complex nested list pagination within a single SDUI component (handled by standard pagination).
- Full declarative language execution on client (e.g., executing JavaScript inside SDUI).

## Requirements

### Functional Requirements
1. Client must fetch and render UI dynamically based on server JSON schema.
2. Unrecognized components must be safely ignored without crashing the app.
3. App must gracefully handle network failures by displaying a cached layout.
4. UI components must trigger native or web actions as specified by the server.
5. Client must enforce schema version compatibility (skip unsupported major versions).

### Non-Functional Requirements
| Requirement | Target | Source |
|-------------|--------|--------|
| Schema Parsing | < 16ms (avoid frame drop) | Apple WWDC Core Animation |
| Cache Retrieval | < 50ms | Uber SDUI Blog |
| Component Render | < 8ms per cell | Meta Feed Optimizations |
| Crash-free Sessions | > 99.9% | Firebase Crashlytics standard |
| Payload Size | < 50KB gzip | Industry average |

## High-Level Architecture (HLD)

### Component Diagram
```text
[ SDUI Backend / CMS ]
         | (JSON Schema over HTTPS)
         v
[ API Gateway & CDN ]
         |
         v
+-----------------------------------------------------------+
| iOS Client                                                |
|                                                           |
|  [ Network Layer ] <---> [ FallbackEngine / DiskCache ]   |
|         |                                                 |
|         v                                                 |
|  [ Schema Parser ] ---> [ Version Compatibility Check ]   |
|         |                                                 |
|         v                                                 |
|  [ SDUI ViewModel ]                                       |
|         |                                                 |
|         +---> [ ComponentRegistry ]                       |
|         |                                                 |
|         +---> [ LayoutResolver ]                          |
|         |                                                 |
|         v                                                 |
|  [ SwiftUI Views ] ---> [ ActionHandler & Analytics ]     |
+-----------------------------------------------------------+
```

### Component Responsibilities
| Component | Responsibility | iOS Implementation |
|-----------|----------------|--------------------|
| Network Layer | Fetch JSON payload, handle headers, caching | URLSession, Combine/async-await |
| FallbackEngine | Store and retrieve last-known-good schema | FileManager, SQLite/CoreData |
| Parser | Decode JSON to Swift structures | JSONDecoder |
| ComponentRegistry | Map component type to native view | Dictionary of Type -> AnyView builder |
| ActionHandler | Route interactions (deeplink, API call) | URLRouter, NotificationCenter |

### Data Flow
1. **User opens app**: SDUI ViewModel requests screen payload from Network Layer.
2. **Network request**: Network layer fetches data, respecting HTTP caching/TTL. If offline, FallbackEngine loads from disk.
3. **Parsing**: JSONDecoder decodes payload into generic `SDUIComponent` tree.
4. **Validation**: Version checker verifies major version compatibility.
5. **Rendering**: ViewModel iterates through components, asking ComponentRegistry for SwiftUI views. LayoutResolver wraps them in Stacks/Grids.
6. **Interaction**: User taps a component, triggering ActionHandler. ActionHandler fires analytics event and executes routing.

## Data Models

### Core Entities
```swift
import Foundation

/// Represents the top-level SDUI Response
struct SDUIScreenResponse: Codable {
    let screenId: String
    let version: Int
    let refreshTtl: TimeInterval
    let layout: SDUILayout
}

/// Layout definitions
struct SDUILayout: Codable {
    let type: String // e.g., "v_stack", "h_stack", "grid"
    let spacing: CGFloat?
    let children: [SDUIComponent]
}

/// Generic component definition
struct SDUIComponent: Codable, Identifiable {
    let id: String
    let type: String
    let props: SDUIProps
    let action: SDUIAction?
    let analytics: [String: String]?
}

/// Type-erased properties allowing flexible JSON decoding
struct SDUIProps: Codable {
    let title: String?
    let subtitle: String?
    let imageUrl: String?
    let textColor: String?
    // Decoding dynamic keys omitted for brevity (Custom init with Decoder)
}

struct SDUIAction: Codable {
    let type: String // "deeplink", "api_call", "web"
    let url: String
}
```

### Database Schema
```sql
-- For FallbackEngine Disk Cache
CREATE TABLE IF NOT EXISTS sdui_cache (
    screen_id TEXT PRIMARY KEY,
    payload BLOB NOT NULL,
    version INTEGER NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ttl INTEGER NOT NULL
);

CREATE INDEX idx_screen_id ON sdui_cache(screen_id);
```

## API Design

### Endpoints
**GET /v1/screens/{screenId}**
Fetches the UI schema.

**Headers:**
- `Client-Version: 2.1.0`
- `Accept: application/json`

**Response Body (200 OK):**
```json
{
  "screen_id": "home_main",
  "version": 2,
  "refresh_ttl": 3600,
  "layout": {
    "type": "v_stack",
    "spacing": 16,
    "children": [
      {
        "id": "hero_1",
        "type": "hero_banner",
        "props": {
          "title": "Welcome to Pro",
          "image_url": "https://cdn.example.com/hero.jpg"
        },
        "action": {
          "type": "deeplink",
          "url": "app://upgrade"
        },
        "analytics": {
          "event_name": "hero_banner_impression",
          "campaign": "q3_pro_upgrade"
        }
      },
      {
        "id": "grid_actions_1",
        "type": "quick_actions_grid",
        "props": {
          "items": [
            {"icon": "wallet", "label": "Send Money"},
            {"icon": "scan", "label": "Scan QR"}
          ]
        }
      }
    ]
  }
}
```

### Pagination Strategy
Typically, SDUI top-level screens are not paginated, but lists *inside* SDUI are.
```json
{
  "type": "infinite_list",
  "action": {
    "type": "fetch_more",
    "url": "/v1/components/feed?cursor=abcd"
  }
}
```

## Client Architecture Deep-Dives

### Component Registry (The Hardest Part)
The core pattern is avoiding crashes on unknown types while maintaining a clean SwiftUI integration.

```swift
import SwiftUI

class ComponentRegistry {
    static let shared = ComponentRegistry()
    
    // Maps component string identifier to a view builder
    private var registeredComponents: [String: (SDUIComponent) -> AnyView] = [:]
    
    private init() {
        registerDefaultComponents()
    }
    
    func register(type: String, builder: @escaping (SDUIComponent) -> AnyView) {
        registeredComponents[type] = builder
    }
    
    func view(for component: SDUIComponent) -> AnyView {
        guard let builder = registeredComponents[component.type] else {
            // Unrecognized type = skip and log, never crash
            print("⚠️ Unknown component type: \(component.type)")
            return AnyView(EmptyView())
        }
        return builder(component)
    }
    
    private func registerDefaultComponents() {
        register(type: "hero_banner") { component in
            AnyView(HeroBannerView(props: component.props))
        }
        
        register(type: "quick_actions_grid") { component in
            AnyView(QuickActionsGridView(props: component.props))
        }
    }
}
```

### Fallback Engine & Caching
Ensures high availability even on flakey networks.

```swift
class FallbackEngine {
    private let db: DatabaseManager // Abstracted SQLite wrapper
    
    func saveLayout(screenId: String, data: Data, version: Int, ttl: TimeInterval) {
        let query = """
            INSERT OR REPLACE INTO sdui_cache (screen_id, payload, version, ttl)
            VALUES (?, ?, ?, ?)
        """
        db.execute(query, arguments: [screenId, data, version, ttl])
    }
    
    func loadCachedLayout(screenId: String) -> Data? {
        let query = "SELECT payload, updated_at, ttl FROM sdui_cache WHERE screen_id = ?"
        guard let result = db.fetchOne(query, arguments: [screenId]) else { return nil }
        
        // TTL Check
        let updatedAt = result["updated_at"] as! Date
        let ttl = result["ttl"] as! TimeInterval
        
        if Date().timeIntervalSince(updatedAt) > ttl {
            // Cache expired, but might still use as stale-while-revalidate fallback
            print("Cache expired, but returning stale data as fallback")
        }
        
        return result["payload"] as? Data
    }
}
```

### SDUI ViewModel & LayoutResolver
Drives the SwiftUI rendering tree.

```swift
@MainActor
class SDUIViewModel: ObservableObject {
    @Published var layout: SDUILayout?
    @Published var isLoading = true
    
    private let networkLayer: NetworkService
    private let fallbackEngine: FallbackEngine
    
    init(networkLayer: NetworkService, fallbackEngine: FallbackEngine) {
        self.networkLayer = networkLayer
        self.fallbackEngine = fallbackEngine
    }
    
    func loadScreen(id: String) async {
        isLoading = true
        do {
            let data = try await networkLayer.fetchData(url: "/v1/screens/\(id)")
            let response = try JSONDecoder().decode(SDUIScreenResponse.self, from: data)
            
            // Major version check
            guard isVersionSupported(response.version) else {
                throw SDUIError.unsupportedVersion
            }
            
            self.layout = response.layout
            fallbackEngine.saveLayout(screenId: id, data: data, version: response.version, ttl: response.refreshTtl)
            
        } catch {
            // Fallback to disk
            if let cachedData = fallbackEngine.loadCachedLayout(screenId: id),
               let response = try? JSONDecoder().decode(SDUIScreenResponse.self, from: cachedData) {
                self.layout = response.layout
            }
        }
        isLoading = false
    }
    
    private func isVersionSupported(_ version: Int) -> Bool {
        let currentClientSDUIVersion = 2
        return version <= currentClientSDUIVersion
    }
}

// Layout Resolver View
struct SDUILayoutView: View {
    let layout: SDUILayout
    
    var body: some View {
        if layout.type == "v_stack" {
            VStack(spacing: layout.spacing ?? 8) {
                ForEach(layout.children) { component in
                    ComponentRegistry.shared.view(for: component)
                }
            }
        } else if layout.type == "h_stack" {
            HStack(spacing: layout.spacing ?? 8) {
                ForEach(layout.children) { component in
                    ComponentRegistry.shared.view(for: component)
                }
            }
        }
    }
}
```

## Performance & Optimizations
| Optimization | Technique | Benchmark/Impact |
|--------------|-----------|------------------|
| Payload Size | Protobuf vs JSON | Protobuf reduces payload size by ~40-50% (Uber engineering blog). JSON is easier for debugging, often gzip is sufficient. |
| Parse Time | Decodable vs Manual Parsing | `JSONDecoder` can be slow for massive trees. Avoid deeply nested AnyCodable/Type Erasures where possible. |
| Over-rendering | Equatable Views | Conform SwiftUIs `View` to `Equatable` so unaffected components don't redraw. |
| Cache Policy | Stale-while-revalidate | Show cached layout instantly (< 50ms), background fetch, update UI transparently. |

## Failure Modes & Fallbacks
| Failure Scenario | Detection | Fallback Strategy |
|------------------|-----------|-------------------|
| Network timeout | URLSession throws URLError.timedOut | Read from FallbackEngine (SQLite disk cache). |
| Unknown component type | Type not found in `ComponentRegistry` | Render `EmptyView()`, log to analytics/Crashlytics. Never crash. |
| Unsupported Schema Version | Server sends `version: 3`, client is `2` | Show cached version `2` or force app update prompt. |
| Missing properties | JSON decode fails for specific props | Provide default values in `SDUIProps` custom init. |

## Trade-off Analysis
| Decision | Option A | Option B | Chosen | Why |
|----------|----------|----------|--------|-----|
| Payload Format | JSON | Protobuf | **JSON** (usually) | Faster iteration, easier debugging. Use Protobuf only at massive scale (e.g., Uber/Meta) for performance. |
| Render Tech | SwiftUI | UIKit (UICollectionView) | **SwiftUI** | SDUI trees map 1:1 perfectly to SwiftUI declarative syntax. Code volume is 5x smaller. |
| Action Handling | Closures per component | Central Notification / Delegate | **Central Router** | Easier to inject global dependencies (analytics, navigation logic) than passing closures everywhere. |

## Observability & Metrics
- `sdui_schema_fetch_latency`: Target < 200ms.
- `sdui_cache_hit_rate`: Monitor offline/fast-load usage. Target > 60%.
- `sdui_unknown_component_rendered`: Tracks backend sending types iOS hasn't implemented. Should be 0 on stable releases.
- `sdui_render_time`: View rendering performance. Target < 16ms per screen update.

## Production Benchmarks Reference
| Metric | Value | Source |
|--------|-------|--------|
| Target Frame Render Time | < 16ms (60fps) | Apple WWDC |
| Protobuf Size Reduction | ~40-50% vs JSON | Uber Engineering Blog |
| Gzip JSON Reduction | ~60-70% | Common Web Standards |
| Crash-free sessions | 99.9% | Firebase Crashlytics |

## Interview Tips
- **Crucial Pattern**: Emphasize that the app should *never* crash when encountering a new, unrecognized string in `type`. The ComponentRegistry pattern skipping unknown types is the most critical feature.
- **Protocol versioning**: Interviewers want to know how you prevent a backend deploy from breaking old app versions. Discuss `min_supported_version` headers and payload version checks.
- **State Management**: Keep state local to components if possible. Only pass global state (like user login status) via `EnvironmentObject` in SwiftUI.
- **Analytics**: Don't hardcode event names. Show how `analytics: ["event_name": "hero_tapped"]` is passed back from the server so product managers can change tracking without app updates.
