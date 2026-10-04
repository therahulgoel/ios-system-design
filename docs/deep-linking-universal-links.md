Design Deep Linking & Universal Links System for iOS
## Overview
Designing a deep linking and Universal Links system is a critical infrastructure problem for any consumer iOS application. It involves routing incoming URLs (from web, emails, social media) to the correct in-app screen, handling deferred deep links for uninstalled apps, and ensuring security against URL hijacking. It is frequently asked at FAANG because it touches OS-level APIs, complex state management, routing architectures, and strict security requirements.

## Target Companies & Frequency
| Company | Why They Ask | Frequency (★ rating) |
| :--- | :--- | :--- |
| Meta | Cross-app navigation (IG to FB), ad attribution, heavy reliance on deferred links | ★★★★★ |
| Airbnb | Complex booking flows, referral links, sharing listings | ★★★★☆ |
| Spotify | Sharing playlists/songs, email campaign integrations | ★★★★☆ |
| Uber | Rider-to-driver web links, receipt emails, promotional codes | ★★★★☆ |
| Google | Inter-app navigation (Maps to Search to YouTube) | ★★★★☆ |

## Scope Definition

### In Scope
- Custom URL Schemes vs. Universal Links
- `apple-app-site-association` (AASA) hosting and validation
- In-app URL routing and parameter extraction (Coordinator pattern)
- Deferred deep linking architecture (post-install routing)
- Cold-start race conditions and state restoration
- Security considerations (parameter validation, scheme checks)

### Out of Scope
- Push notification delivery mechanisms
- Designing the UI for the target screens
- Backend implementation of the attribution matching algorithm
- Android App Links (Android equivalent)

## Requirements

### Functional Requirements
1. The app must handle both legacy custom URL schemes (`myapp://`) and Universal Links (`https://myapp.com/`).
2. Unrecognized or invalid paths must gracefully degrade to the app's home screen.
3. The system must route parameterized URLs (e.g., `/profile/{id}`) to the correct screen with parameters injected.
4. Deferred deep links must survive the App Store installation process and route the user upon first launch.
5. The app must track link attribution for marketing analytics.

### Non-Functional Requirements
| Requirement | Target | Source |
| :--- | :--- | :--- |
| Cold-start Routing | Queue link if launch < 500ms | Industry standard for initial navigation |
| Deferred Link Window | 72 hours max expiry | AppsFlyer / Branch standard |
| AASA File Size | < 128KB | Apple official requirement |
| Open Rate | 25-40% engagement | Industry average |
| Crash-free rate | > 99.9% on link parsing | Standard SLA |

## High-Level Architecture (HLD)

### Component Diagram
```text
[Marketing Ad / Email] -> (Taps Link: https://myapp.com/sale)
         |
         v
    [iOS System]
         |-- (App Installed?) -- YES --> [UIApplicationDelegate / SceneDelegate]
         |                                         |
         NO                                        v
         |                                  [DeepLinkRouter]
         v                                         |-- 1. Parse URL & Match Pattern
    [Safari / Web]                                 |-- 2. Extract Parameters
         |                                         |-- 3. Security/Validation
         |-- (Deferred Link Flow)                  v
         v                                  [AppCoordinator]
    [App Store]                                    |-- Push/Modal target screen
         |                                         v
         v                                  [Target UI (e.g., SaleView)]
    [First Launch] -> [DeferredLinkFetcher] -> (Matches device fingerprint with Backend)
```

### Component Responsibilities
| Component | Responsibility | iOS Implementation |
| :--- | :--- | :--- |
| AASA Host | Serves the domain ownership verification file | HTTPS server (`/.well-known/apple-app-site-association`) |
| SceneDelegate | OS entry point for link events | `scene(_:continue:)` / `onOpenURL` |
| DeepLinkRouter | Pattern matching and URL parameter extraction | Singleton or Dependency Injected Router class |
| AppCoordinator | Translates matched routes into navigation actions | Navigation controller / SwiftUI NavigationStack |
| DeferredLinkFetcher | Retrieves pending deep link on first app install | Async networking class querying backend |

### Data Flow
1. User taps `https://myapp.com/profile/123`.
2. OS checks if `myapp.com` is verified via cached AASA file.
3. If verified, OS opens the app and passes the `NSUserActivity` containing the URL to `SceneDelegate`.
4. `SceneDelegate` passes the URL to `DeepLinkRouter`.
5. `DeepLinkRouter` matches `/profile/{id}`, extracts `id = 123`.
6. Router generates a strongly typed `Route` enum and passes it to `AppCoordinator`.
7. `AppCoordinator` constructs `ProfileViewModel(userId: "123")` and pushes `ProfileView`.

## Data Models

### Core Entities
```swift
import Foundation

/// Represents a matched and validated deep link route.
enum AppRoute: Equatable {
    case home
    case profile(userId: String)
    case product(productId: String, promoCode: String?)
    case unknown
}

/// The AASA file structure (Server-side model)
struct AppleAppSiteAssociation: Codable {
    struct AppLinks: Codable {
        struct Details: Codable {
            let appID: String
            let paths: [String]
        }
        let apps: [String]
        let details: [Details]
    }
    let applinks: AppLinks
}
```

### Database Schema
Used for local storage of attribution data (SQLite).
```sql
CREATE TABLE attribution_data (
    id TEXT PRIMARY KEY,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    install_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_install_time ON attribution_data(install_timestamp);
```

## API Design

### Endpoints
**1. Fetch Deferred Deep Link (GET /v1/deep-link/deferred)**
Called on the first app launch to check if the user arrived via a tracked link.
- **Headers:** `Authorization: Bearer <token>`
- **Query Params:**
  - `fingerprint`: `String` (hash of IP, user agent, OS version)
  - `idfa`: `String?` (if available via AppTrackingTransparency)
- **Response:**
  ```json
  {
    "deep_link": "https://myapp.com/sale?code=SUMMER20",
    "confidence_score": 0.85,
    "expires_at": "2023-12-01T12:00:00Z"
  }
  ```

### Pagination Strategy
Not strictly applicable for deep link routing, but if fetching a list of dynamic link rules from a CMS, cursor-based pagination would be used: `GET /v1/deep-link/rules?cursor=encoded_timestamp`.

## Client Architecture Deep-Dives

### Subsystem 1: Deep Link Router & Coordinator
The router parses the URL, extracts parameters using wildcards, and delegates navigation.

```swift
import Foundation

class DeepLinkRouter {
    typealias RouteHandler = ([String: String]) -> AppRoute?
    private var routes: [String: RouteHandler] = [:]
    
    // Register a pattern like "/profile/{userId}"
    func register(pattern: String, handler: @escaping RouteHandler) {
        routes[pattern] = handler
    }
    
    func handle(url: URL) -> AppRoute {
        guard let components = URLComponents(url: url, resolvingAgainstBaseURL: true) else {
            return .unknown
        }
        
        let path = components.path
        let queryItems = components.queryItems?.reduce(into: [String: String]()) { $0[$1.name] = $1.value } ?? [:]
        
        for (pattern, handler) in routes {
            if let pathParams = match(pattern: pattern, path: path) {
                var allParams = pathParams
                allParams.merge(queryItems) { current, _ in current }
                if let route = handler(allParams) {
                    return route
                }
            }
        }
        return .unknown
    }
    
    private func match(pattern: String, path: String) -> [String: String]? {
        // Simplified matching: splits by "/" and extracts {param}
        let patternParts = pattern.split(separator: "/")
        let pathParts = path.split(separator: "/")
        
        guard patternParts.count == pathParts.count else { return nil }
        
        var params: [String: String] = [:]
        for (idx, pPart) in patternParts.enumerated() {
            if pPart.hasPrefix("{") && pPart.hasSuffix("}") {
                let key = String(pPart.dropFirst().dropLast())
                params[key] = String(pathParts[idx])
            } else if pPart != pathParts[idx] {
                return nil
            }
        }
        return params
    }
}
```

### Subsystem 2: Deferred Deep Linking & Cold Start Race Condition
If an app is cold-launched via a URL, the URL event might arrive before the UI hierarchy is fully setup.

```swift
import SwiftUI

@main
struct MyApp: App {
    @StateObject private var coordinator = AppCoordinator()
    @State private var pendingRoute: AppRoute?
    
    var body: some Scene {
        WindowGroup {
            RootView(coordinator: coordinator)
                .onOpenURL { url in
                    let route = router.handle(url: url)
                    if coordinator.isReady {
                        coordinator.navigate(to: route)
                    } else {
                        // Queue the route until coordinator is fully initialized
                        pendingRoute = route
                    }
                }
                .onReceive(coordinator.$isReady) { isReady in
                    if isReady, let route = pendingRoute {
                        coordinator.navigate(to: route)
                        pendingRoute = nil
                    }
                }
                .task {
                    // Check for deferred deep link on first launch
                    if isFirstLaunch() {
                        if let deferredURL = await fetchDeferredLink() {
                            let route = router.handle(url: deferredURL)
                            coordinator.navigate(to: route)
                        }
                    }
                }
        }
    }
}
```

### Subsystem 3: Security & Validations
Deep links are an attack vector. Never trust parameters for authentication.
```swift
func validateDeepLink(_ url: URL) -> Bool {
    // 1. Check scheme
    let allowedSchemes = ["https", "myapp"]
    guard let scheme = url.scheme, allowedSchemes.contains(scheme) else { return false }
    
    // 2. Protect sensitive actions (require confirmation)
    if url.path.contains("/payment/") {
        coordinator.showConfirmationDialog(for: url)
        return false // Wait for user confirmation
    }
    
    // 3. Prevent XSS/injection via encoding checks
    let absoluteString = url.absoluteString
    guard absoluteString == absoluteString.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) else {
        return false
    }
    
    return true
}
```

## Performance & Optimizations
| Optimization | Technique | Benchmark/Impact |
| :--- | :--- | :--- |
| AASA Hosting | Serve directly from origin, avoid aggressive CDN caching | Prevents multi-day delays in OS picking up AASA updates |
| Regex caching | Pre-compile URL matching regex at startup | Sub-millisecond URL parsing |
| Cold Start Queuing | Buffer URL intent until UI stack is ready | Eliminates 100% of dropped links on cold launch |

## Failure Modes & Fallbacks
| Failure Scenario | Detection | Fallback Strategy |
| :--- | :--- | :--- |
| AASA unverified by OS | Link opens in Safari instead of App | Web page displays a Smart App Banner to manually open the app |
| Unknown URL path | Router returns `.unknown` | Navigate to App Home screen, log metric |
| Deferred link fetch fails | Network timeout / 5xx | Treat as organic install, skip deep link navigation |

## Trade-off Analysis
| Decision | Option A | Option B | Chosen | Why |
| :--- | :--- | :--- | :--- | :--- |
| **Link Mechanism** | Custom URL Scheme | Universal Links | **Universal Links** | Native fallback to web, strong domain verification (no hijacking). Custom schemes used only as a backup. |
| **Routing Architecture** | View-layer parsing (`.onOpenURL`) | Centralized Router + Coordinator | **Central Router** | Decouples navigation from UI. Allows queueing links on cold start and easier unit testing. |
| **Deferred Links** | Build in-house | Use Branch/AppsFlyer | **Branch/AppsFlyer** | Device fingerprinting is extremely complex, error-prone, and requires constant maintenance for iOS privacy changes. |

## Observability & Metrics
- **Link Open Rate:** Percentage of clicks that successfully open the app (target: > 80% for installed users).
- **Unknown Route Hits:** Count of URLs that matched the domain but had unhandled paths (alerts if > 5%).
- **Deferred Link Match Rate:** Percentage of first launches successfully matched to a pending link click.
- **Routing Latency:** Time from `onOpenURL` to view appearing (target < 100ms).

## Production Benchmarks Reference
| Metric | Value | Source |
| :--- | :--- | :--- |
| AASA File Limit | < 128 KB | Apple Documentation |
| Deferred Link Expiry | 72 hours | Standard via AppsFlyer/Branch |
| AASA OS Cache TTL | ~24 hours | Apple OS behavior observation |
| Attribution Window | 30 days | Meta Ads default attribution |

## Interview Tips
- **Beware of CDNs:** Emphasize that caching the AASA file on a CDN can cause critical issues because iOS caches it aggressively. If the CDN returns a stale version, it can take days for the OS to request it again.
- **Security is paramount:** Explicitly mention that you should *never* use a deep link for auto-login (`?token=123`) or immediate destructive actions without user confirmation. Custom schemes are easily hijacked by malicious apps.
- **The Cold Start Problem:** Many candidates forget that clicking a link when the app is killed means the OS launches the app and passes the URL *before* the navigation stack exists. Mention queuing the deep link state until the UI is ready.
