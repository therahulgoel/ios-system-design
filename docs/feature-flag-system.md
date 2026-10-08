# Feature Flag & Experimentation SDK: Production System Design & Whiteboard Master Guide

## 1. Interview Context & Problem Statement

In mobile system design interviews at top tech companies (Uber, Meta, Airbnb, Google, Stripe, Apple), candidates are asked to design an infrastructure-grade **Feature Flag and Experimentation SDK**.

### The Exact Interview Prompt:
> *"Design a generic, extensible Feature Flag SDK in iOS that can be embedded across multiple mobile apps. The SDK must support dynamic endpoint URLs and query parameters configured by the host app, guarantee synchronous O(1) evaluation without blocking the UI, support a resilient multi-tier fallback chain, handle A/B test impression tracking, and adhere strictly to the Open/Closed Principle without relying on a rigid, hardcoded singleton."*

---

## 📋 2. Whiteboard Canvas (What You Actually Draw in an Interview)

This is the exact, unified whiteboard layout that a Senior Engineer, Staff Architect, or Engineering Manager draws on the board during a 45-minute virtual or on-site system design session:

```ascii
+-----------------------------------------------------------------------------------------------------------------------------------------------+
|                                                FEATURE FLAG SDK: WHITEBOARD DESIGN CANVAS                                                     |
+-----------------------------------------------------------------------------------------------------------------------------------------------+
| SECTION A: REQUIREMENTS & SLAS                | SECTION B: END-TO-END WHITEBOARD ARCHITECTURE                                                 |
|                                               |                                                                                               |
| [FUNCTIONAL REQUIREMENTS - FR]                |   [HOST APPLICATION TIER]                                                                     |
| 1. Synchronous O(1) typed reads (Bool, Int,   |   +----------------------------------------------------------------------------------------+  |
|    String, JSON) in UI code without await.    |   | SwiftUI Views / UIKit Controllers / ViewModels / Feature Modules                       |  |
| 2. Dynamic Config: Host app passes target URL |   +-------------------------------------------+--------------------------------------------+  |
|    and params (userId, country, appVersion).  |                                               |                                               |
| 3. Multi-tier fallback chain (Zero crash).    |                                               | 1. value(for: .newCheckout) [Sync O(1)]       |
| 4. Deduplicated A/B test impression tracking. |                                               v                                               |
| 5. Emergency Sev-1 kill switch (< 5 mins).    |   [FEATURE FLAG CLIENT SDK BOUNDARY]                                                          |
|                                               |   +----------------------------------------------------------------------------------------+  |
| [NON-FUNCTIONAL REQUIREMENTS - NFR]           |   | <<Protocol>> FeatureFlagProviding                                                      |  |
| - Read Latency   : < 0.1ms (in-memory lock)   |   | CompositeFeatureFlagService (Orchestrator - Closed for Modification)                   |  |
| - Launch Timeout : 1.5s strict SLA            |   | - Coordinates priority chain under NSLock thread safety                                |  |
| - Memory Footprint: < 5MB resident RAM        |   | - Session Impression Deduplicator (Set<String> prevents over-counting)                  |  |
| - Disk Storage   : < 100KB atomic JSON file   |   +-------------------------------------------+--------------------------------------------+  |
| - Crash Budget   : 0% unhandled errors        |                                               |                                               |
|                                               |                                               | 2. Evaluate in Priority Order (P0->P1->P2)     |
| [OUT OF SCOPE]                                |                                               v                                               |
| - Server-side ML experimentation models       |   [PLUGGABLE SOURCE PROVIDER CHAIN (OPEN FOR EXTENSION)]                                      |
| - Web-based flag admin management dashboard   |   +----------------------------------------------------------------------------------------+  |
|                                               |   | <<Protocol>> FeatureFlagSourceProvider                                                 |  |
|                                               |   |                                                                                        |  |
|                                               |   |  +-------------------+  +--------------------+  +-------------------+  +------------+  |  |
|                                               |   |  | DebugOverride     |  | RemoteConfigStore  |  | BundledDefaults   |  | MDM/Custom |  |  |
|                                               |   |  | Provider (P0)     |  | Provider (P1)      |  | Provider (P2)     |  | Provider   |  |  |
|                                               |   |  | (Local QA menu)   |  | (Network/Disk)     |  | (defaults.json)   |  | (P3 - OCP) |  |  |
|                                               |   |  +-------------------+  +---------+----------+  +-------------------+  +------------+  |  |
|                                               |   +-----------------------------------|----------------------------------------------------+  |
|                                               |                                       |                                                       |
|                                               |             +-------------------------+-------------------------+                             |
|                                               |             | 3. Dynamic Fetch Request (URL, params, keys)      | 4. Log Exposure             |
|                                               |             v                                                   v                             |
|                                               |   +-----------------------------------+               +------------------------------------+  |
|                                               |   | ConfigFetcher Engine              |               | Analytics & Impression Tracker     |  |
|                                               |   | - Injected Base URL               |               | - Dispatches exposure events       |  |
|                                               |   | - Injected Query Params (userId..) |               | - Integrates with Analytics SDK    |  |
|                                               |   | - Injected Key Subset (Optional)  |               +------------------+-----------------+  |
|                                               |   | - Strict 1.5s launch timeout SLA  |                                  |                    |
|                                               |   +-----------------+-----------------+                                  |                    |
|                                               |                     |                                                    | 6. Batch Events    |
|                                               |                     | 3b. HTTP GET (ETag)                                |                    |
|                                               |                     v                                                    v                    |
|                                               |   [EDGE & CLOUD INFRASTRUCTURE]                       [DATA PIPELINE TIER]                    |
|                                               |   +-----------------------------------+               +------------------------------------+  |
|                                               |   | Cloudflare CDN / Envoy Gateway    |               | Kafka Stream -> ClickHouse DW      |  |
|                                               |   | - Edge ETag / 304 validation      |               | (A/B Test Variant Analysis)        |  |
|                                               |   +-----------------+-----------------+               +------------------------------------+  |
|                                               |                     |                                                                         |
|                                               |                     v                                                                         |
|                                               |   +-----------------------------------+               [EMERGENCY KILL SWITCH]                 |
|                                               |   | Remote Config Microservice        |               +------------------------------------+  |
|                                               |   | - Evaluates segmentation rules    |               | APNs High-Priority Silent Push     |  |
|                                               |   | - Returns evaluated JSON flat map |               | - Dispatches to client in < 5 mins |  |
|                                               |   +-----------------------------------+               +------------------------------------+  |
+-----------------------------------------------------------------------------------------------------------------------------------------------+
```

---

## 🔄 3. The 4 Core Whiteboard Execution Flows

When presenting your whiteboard in an interview, walk the interviewer through these **4 numbered flows** in order:

### Flow 1: Synchronous Hot Path Read (`< 0.1ms`)
1. App code (SwiftUI `body` or ViewModel) calls `featureFlags.value(for: .newCheckout)`.
2. `CompositeFeatureFlagService` acquires an in-memory `NSLock` and queries the registered provider list in priority order:
   - **P0: DebugOverrideProvider**: Returns developer/QA overrides if set; otherwise `nil`.
   - **P1: RemoteConfigStoreProvider**: Returns the downloaded and cached flag from memory; otherwise `nil`.
   - **P2: BundledDefaultsProvider**: Returns factory defaults shipped in the app bundle (`defaults.json`).
   - **Fallback**: If all providers return `nil`, the SDK returns the in-code `defaultValue` defined on the `Flag<T>` token.
3. The method returns immediately on the main thread without requiring `await`.

### Flow 2: Dynamic Cold-Start Fetch (`1.5s SLA Timeout`)
1. On app launch (`didFinishLaunchingWithOptions`), the host app instantiates a `ConfigFetchRequest` passing:
   - Target Base URL (e.g., `https://api.mycompany.com/v1/config/resolve`)
   - Contextual targeting parameters: `["userId": "usr_102", "country": "US", "appVersion": "5.4.0", "tier": "premium"]`
   - Optional requested flag key subset: `["checkout_v2_enabled", "cart_max_limit"]`
   - Custom session/auth headers and a strict **1.5-second timeout**.
2. `RemoteConfigFetcher` executes the HTTP GET request with an `If-None-Match` ETag header.
3. If the server responds with HTTP 304 Not Modified, the SDK retains the current cache.
4. If HTTP 200 OK arrives before the launch timeout, the SDK updates the in-memory cache and writes the new configuration atomically to `/Library/Application Support/cached_flags.json`.
5. If the request times out ($> 1.5	ext{ s}$) or encounters a network error, the SDK fails silently and uses the cached disk configuration.

### Flow 3: A/B Test Impression Tracking (Exposure Deduplication)
1. When a user navigates to a screen that reads an experimentation flag (e.g., `new_search_algorithm`), the composite service checks an in-memory `Set<String>` of already-tracked keys for the current session.
2. If the key has not been seen this session, the SDK records the key in the set and dispatches an exposure event to `ImpressionTracking`:
   `analytics.logExposure(flagKey: "new_search_algorithm", value: "variant_b")`.
3. If the flag is read 100 times during scrolling or list recycling, subsequent calls are deduplicated, preventing phantom analytics events.

### Flow 4: Severity-1 Emergency Kill Switch (`< 5 Minutes`)
1. If a newly released feature causes crash loops in production, operators toggle the flag to `false` in the backend dashboard.
2. The backend sends an APNs high-priority silent push payload: `{"action": "kill_flag", "key": "new_checkout_enabled"}`.
3. The host app's background push delegate forwards the payload to `RemoteConfigStoreProvider`, which immediately updates the in-memory dictionary and writes `false` to disk.
4. The feature is deactivated globally across active devices within 5 minutes without requiring an app relaunch.

---

## 🛠️ 4. Low-Level Design (LLD): Class Architecture & Swift Implementation

### 1. Mermaid Class & Interface Diagram

```mermaid
classDiagram
    class FeatureFlagProviding {
        <<protocol>>
        +value(flag) T
    }

    class FeatureFlagSourceProvider {
        <<protocol>>
        +name String
        +value(key) Any
    }

    class ImpressionTracking {
        <<protocol>>
        +logExposure(flagKey, value)
    }

    class ConfigFetching {
        <<protocol>>
        +fetchConfiguration(request, completion)
    }

    class CompositeFeatureFlagService {
        -providers: Array~FeatureFlagSourceProvider~
        -impressionTracker: ImpressionTracking
        -trackedImpressions: Set~String~
        -lock: NSLock
        +value(flag) T
    }

    class ConfigFetchRequest {
        +endpointURL: URL
        +queryParams: Dictionary
        +requestedKeys: Array
        +headers: Dictionary
        +timeoutInterval: TimeInterval
    }

    class RemoteConfigFetcher {
        -urlSession: URLSession
        +fetchConfiguration(request, completion)
    }

    class DebugOverrideProvider {
        -overrides: Dictionary
        -lock: NSLock
        +setOverride(value, key)
        +value(key) Any
    }

    class RemoteConfigStoreProvider {
        -memoryCache: Dictionary
        -storageURL: URL
        -lock: NSLock
        -fetcher: ConfigFetching
        +refresh(request, completion)
        +value(key) Any
    }

    class BundledDefaultsProvider {
        -defaults: Dictionary
        +value(key) Any
    }

    class MDMManagedConfigProvider {
        +value(key) Any
    }

    FeatureFlagProviding <|.. CompositeFeatureFlagService
    CompositeFeatureFlagService --> FeatureFlagSourceProvider : evaluates in priority order
    CompositeFeatureFlagService --> ImpressionTracking : tracks exposure
    FeatureFlagSourceProvider <|.. DebugOverrideProvider
    FeatureFlagSourceProvider <|.. RemoteConfigStoreProvider
    FeatureFlagSourceProvider <|.. BundledDefaultsProvider
    FeatureFlagSourceProvider <|.. MDMManagedConfigProvider
    RemoteConfigStoreProvider --> ConfigFetching : delegates network calls
    ConfigFetching <|.. RemoteConfigFetcher
    RemoteConfigFetcher ..> ConfigFetchRequest : executes
```

---

### 2. Production Swift Implementation (Clean, Robust, No Sendable)

#### Step 1: Dynamic Request Model & Network Fetcher
```swift
import Foundation

// Injected dynamically from outside by the host application
public struct ConfigFetchRequest {
    public let endpointURL: URL
    public let queryParams: [String: String]
    public let requestedKeys: [String]? // Optional: filter subset of flags
    public let headers: [String: String]
    public let timeoutInterval: TimeInterval

    public init(
        endpointURL: URL,
        queryParams: [String: String] = [:],
        requestedKeys: [String]? = nil,
        headers: [String: String] = [:],
        timeoutInterval: TimeInterval = 1.5
    ) {
        self.endpointURL = endpointURL
        self.queryParams = queryParams
        self.requestedKeys = requestedKeys
        self.headers = headers
        self.timeoutInterval = timeoutInterval
    }
}

public protocol ConfigFetching {
    func fetchConfiguration(
        request: ConfigFetchRequest,
        completion: @escaping (Result<[String: Any], Error>) -> Void
    )
}

public final class RemoteConfigFetcher: ConfigFetching {
    private let urlSession: URLSession

    public init(urlSession: URLSession = .shared) {
        self.urlSession = urlSession
    }

    public func fetchConfiguration(
        request: ConfigFetchRequest,
        completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        guard var components = URLComponents(url: request.endpointURL, resolvingAgainstBaseURL: false) else {
            completion(.failure(URLError(.badURL)))
            return
        }

        var queryItems = request.queryParams.map { URLQueryItem(name: $0.key, value: $0.value) }
        if let keys = request.requestedKeys, !keys.isEmpty {
            queryItems.append(URLQueryItem(name: "keys", value: keys.joined(separator: ",")))
        }
        components.queryItems = queryItems.isEmpty ? nil : queryItems

        guard let finalURL = components.url else {
            completion(.failure(URLError(.badURL)))
            return
        }

        var urlRequest = URLRequest(url: finalURL)
        urlRequest.httpMethod = "GET"
        urlRequest.timeoutInterval = request.timeoutInterval
        for (headerKey, headerValue) in request.headers {
            urlRequest.setValue(headerValue, forHTTPHeaderField: headerKey)
        }

        let task = urlSession.dataTask(with: urlRequest) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let data = data,
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                completion(.failure(URLError(.cannotParseResponse)))
                return
            }

            completion(.success(json))
        }
        task.resume()
    }
}
```

---

#### Step 2: Strongly-Typed Flag Descriptor & Protocols
```swift
// Strongly-typed flag token preventing string typo bugs
public struct Flag<T> {
    public let key: String
    public let defaultValue: T

    public init(key: String, defaultValue: T) {
        self.key = key
        self.defaultValue = defaultValue
    }
}

// Common flag definitions
public extension Flag where T == Bool {
    static let newCheckout = Flag<Bool>(key: "checkout_v2_enabled", defaultValue: false)
    static let biometricAuth = Flag<Bool>(key: "biometric_quick_login", defaultValue: true)
}

public extension Flag where T == Int {
    static let maxCartItems = Flag<Int>(key: "cart_max_limit", defaultValue: 50)
}

public protocol FeatureFlagProviding {
    func value<T>(for flag: Flag<T>) -> T
}

public protocol FeatureFlagSourceProvider {
    var name: String { get }
    func value(forKey key: String) -> Any?
}

public protocol ImpressionTracking {
    func logExposure(flagKey: String, value: String)
}
```

---

#### Step 3: Pluggable Source Providers (Open for Extension)
```swift
// P0: Local Debug Overrides (QA & Developer Menu)
public final class DebugOverrideProvider: FeatureFlagSourceProvider {
    public let name = "DebugOverride"
    private var overrides: [String: Any] = [:]
    private let lock = NSLock()

    public init() {}

    public func setOverride<T>(value: T?, for key: String) {
        lock.lock()
        defer { lock.unlock() }
        overrides[key] = value
    }

    public func clearAll() {
        lock.lock()
        defer { lock.unlock() }
        overrides.removeAll()
    }

    public func value(forKey key: String) -> Any? {
        lock.lock()
        defer { lock.unlock() }
        return overrides[key]
    }
}

// P1: Remote Config & Disk Storage Provider
public final class RemoteConfigStoreProvider: FeatureFlagSourceProvider {
    public let name = "RemoteConfig"
    private var memoryCache: [String: Any] = [:]
    private let lock = NSLock()
    private let storageURL: URL
    private let fetcher: ConfigFetching

    public init(storageURL: URL, fetcher: ConfigFetching = RemoteConfigFetcher()) {
        self.storageURL = storageURL
        self.fetcher = fetcher
        loadFromDisk()
    }

    public func value(forKey key: String) -> Any? {
        lock.lock()
        defer { lock.unlock() }
        return memoryCache[key]
    }

    public func refresh(request: ConfigFetchRequest, completion: ((Bool) -> Void)? = nil) {
        fetcher.fetchConfiguration(request: request) { [weak self] result in
            guard let self = self else { return }
            switch result {
            case .success(let newFlags):
                self.lock.lock()
                for (key, val) in newFlags {
                    self.memoryCache[key] = val
                }
                let snapshot = self.memoryCache
                self.lock.unlock()

                // Persist asynchronously to disk with atomic write
                DispatchQueue.global(qos: .utility).async {
                    if let data = try? JSONSerialization.data(withJSONObject: snapshot) {
                        try? data.write(to: self.storageURL, options: .atomic)
                    }
                }
                completion?(true)

            case .failure:
                completion?(false)
            }
        }
    }

    private func loadFromDisk() {
        guard let data = try? Data(contentsOf: storageURL),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return }
        self.memoryCache = json
    }
}

// P2: Bundled Defaults Provider (Factory JSON shipped in IPA)
public final class BundledDefaultsProvider: FeatureFlagSourceProvider {
    public let name = "BundledDefaults"
    private let defaults: [String: Any]

    public init(bundle: Bundle = .main, resourceName: String = "FeatureFlagDefaults") {
        if let url = bundle.url(forResource: resourceName, withExtension: "json"),
           let data = try? Data(contentsOf: url),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            self.defaults = json
        } else {
            self.defaults = [:]
        }
    }

    public func value(forKey key: String) -> Any? {
        defaults[key]
    }
}
```

---

#### Step 4: Composite Orchestrator (`CompositeFeatureFlagService`)
```swift
public final class CompositeFeatureFlagService: FeatureFlagProviding {
    private let providers: [FeatureFlagSourceProvider]
    private let impressionTracker: ImpressionTracking?
    private var trackedImpressions: Set<String> = []
    private let lock = NSLock()

    public init(
        providers: [FeatureFlagSourceProvider],
        impressionTracker: ImpressionTracking? = nil
    ) {
        self.providers = providers
        self.impressionTracker = impressionTracker
    }

    public func value<T>(for flag: Flag<T>) -> T {
        for provider in providers {
            if let rawValue = provider.value(forKey: flag.key),
               let castedValue = rawValue as? T {
                trackImpressionIfNeeded(for: flag.key, value: castedValue)
                return castedValue
            }
        }

        trackImpressionIfNeeded(for: flag.key, value: flag.defaultValue)
        return flag.defaultValue
    }

    private func trackImpressionIfNeeded<T>(for key: String, value: T) {
        guard let impressionTracker = impressionTracker else { return }

        lock.lock()
        let alreadyTracked = trackedImpressions.contains(key)
        if !alreadyTracked {
            trackedImpressions.insert(key)
        }
        lock.unlock()

        if !alreadyTracked {
            impressionTracker.logExposure(flagKey: key, value: String(describing: value))
        }
    }
}
```

---

#### Step 5: How the Host App Wires the SDK from the Outside
```swift
// Host App Assembly (AppDelegate / AppLaunch)
let appSupportURL = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
let flagFile = appSupportURL.appendingPathComponent("cached_flags.json")

let debugProvider = DebugOverrideProvider()
let remoteStore = RemoteConfigStoreProvider(storageURL: flagFile)
let bundledDefaults = BundledDefaultsProvider()

let featureFlagService = CompositeFeatureFlagService(
    providers: [debugProvider, remoteStore, bundledDefaults]
)

// Dynamic Configuration injected from outside!
let request = ConfigFetchRequest(
    endpointURL: URL(string: "https://api.mycompany.com/v1/config/resolve")!,
    queryParams: [
        "userId": "usr_99182",
        "appVersion": "5.4.0",
        "country": "US",
        "tier": "enterprise"
    ],
    requestedKeys: ["checkout_v2_enabled", "cart_max_limit"],
    headers: ["Authorization": "Bearer session_token_xyz"],
    timeoutInterval: 1.5 // Strict 1.5s launch timeout
)

remoteStore.refresh(request: request) { success in
    print("Feature flags updated from remote: \(success)")
}
```

---

## ⚖️ 5. Why Avoiding Direct Singletons Wins in Staff & EM Interviews

| Dimension | Hardcoded Singleton (`FeatureFlag.shared`) | Interface-Driven Composite (Our Design) |
|:---|:---|:---|
| **Unit Testing** | Tests share global mutable state; parallel execution causes test flakiness. | **100% Isolated**: Inject `MockFeatureFlagService` per test. |
| **SwiftUI Previews** | Stuck on whatever state the singleton holds; cannot preview both variants. | **Instant Multi-Variant**: Inject different mocks into `#Preview`. |
| **Open/Closed Principle** | Modifying sources requires editing the core singleton class. | **Zero Edits**: Add any new source conforming to `FeatureFlagSourceProvider`. |
| **Scoping & Tenants** | Inability to support multi-account or guest vs logged-in flag sets. | **Scopeable**: Different containers can have distinct flag service instances. |

---

## 🔄 6. Critical Architectural Dilemmas to Defend

### 1. The Activation Dilemma: When Do New Flags Take Effect?
- **Immediate In-Flight Activation**: Network response updates memory cache immediately.
  - *Risk*: Jarring UI mutation. If a user is on Step 2 of checkout and the flag updates, Step 3 might switch to a new flow, causing state crashes or broken user experience.
- **Next-Launch Activation**: New flags are saved to disk but only promoted to active memory cache on next cold boot.
  - *Benefit*: Guaranteed session consistency.
  - *Tradeoff*: Takes two launches for a new feature to appear.
- **The Hybrid SLA Pattern (Recommended)**:
  - On launch, fetch with a strict **1.5s timeout**.
  - If received before splash dismisses, apply immediately.
  - If timed out, run on cached disk config, save the new payload to a `staged_flags` disk buffer, and promote on next launch.
  - **Exception**: Emergency kill switches bypass this rule and deactivate instantly.

### 2. Client vs Server-Side Rule Evaluation
- **Server-Side Evaluation**: Client sends attributes (`user_id`, `app_version`, `country`); server returns a pre-evaluated flat key-value map.
  - *Advantage*: Tiny client payload (< 50KB), zero client battery/CPU cost, business targeting rules stay private.
- **Client-Side Evaluation**: Server sends raw rule sets; client evaluates locally using MurmurHash3.
  - *Advantage*: Works offline; instant re-evaluation if user changes profile attributes.
  - *Tradeoff*: Large payload (> 500KB); exposes unreleased feature names and targeting rules in client JSON.

### 3. Impression Tracking: Exposure vs Evaluation
- **The Anti-Pattern**: Firing an analytics impression event every time `value(for:)` is called. If a list cell pre-fetches off-screen items, analytics records phantom impressions for features the user never saw, corrupting A/B test sample data.
- **The Solution**: 
  1. Separate **Evaluation** (getting the value for logic) from **Exposure** (user actually rendered the UI).
  2. Maintain an in-memory `Set<String>` per session to deduplicate impressions so repetitive calls in scroll views only emit a single exposure event.

---

## 👔 7. The EM Dimension: Governance & Operations

### 1. Preventing "Flag Rot" (Technical Debt Governance)
- **The Problem**: After 6-12 months, an enterprise codebase accumulates hundreds of dead feature flags. Engineers leave, nobody knows if a flag is safe to delete, and apps suffer from nested `if/else` complexity.
- **The EM Governance Framework**:
  1. **Flag Expiration Metadata**: Every flag created in the dashboard must specify an owner and a `sunset_date` (90 days maximum).
  2. **Automated CI Alerts**: CI scripts query flags at 100% rollout for over 30 days and automatically file Jira/GitHub cleanup tickets assigned to the author.
  3. **Linter Enforcement**: A custom SwiftLint rule flags deprecated feature tokens older than 2 release cycles.

### 2. Emergency Kill-Switch Strategy (Sev-1 Defense)
- If a flagged feature causes a crash loop or security vulnerability:
  1. Update flag to `false` in the backend dashboard.
  2. Dispatch a high-priority **APNs Silent Push** payload: `{"action": "kill_flag", "key": "checkout_v2_enabled"}`.
  3. The client's background push handler updates disk cache and memory cache immediately without requiring an app launch.
  4. Global fleet deactivation SLA: **< 5-10 minutes**.

---

## ❓ 8. Mock Interview Q&A (Staff & EM Level)

### Q1: What is the difference between your HLD and your LLD in this design?
**Answer**: Our HLD captures the end-to-end system topology: dividing the client device (host app, SDK memory cache, disk persistence) from the edge tier (CDN / ETag validation) and cloud infrastructure (remote rule microservice, Redis hot cache, APNs silent push gateway, and Kafka analytics pipeline). Our LLD zooms into the client SDK internals: defining the `FeatureFlagProviding` interface, the `FeatureFlagSourceProvider` chain conforming to the Open/Closed Principle, the dynamic `ConfigFetchRequest` injection, and `NSLock` thread safety for sub-0.1ms reads.

### Q2: Why should we avoid a direct singleton for the Feature Flag SDK?
**Answer**: A direct singleton couples calling code to global mutable state, making parallel unit testing impossible, breaking SwiftUI preview multi-variant isolation, and violating the Open/Closed Principle whenever a new source (like QA debug overrides or MDM profiles) is added. We replace it by defining an interface and a composite service that evaluates an array of providers.

### Q3: How do you support passing dynamic endpoints and targeting parameters from the outside?
**Answer**: We decouple the network engine using a `ConfigFetchRequest` model passed into `RemoteConfigStoreProvider.refresh(request:)`. The host application injects the base URL (allowing staging vs production switches), query parameters (userId, country, appVersion), and an optional subset of requested keys with a strict 1.5-second timeout.

### Q4: How do you prevent over-counting A/B test impressions?
**Answer**: We implement session-level impression deduplication inside the composite service using an in-memory `Set<String>`. Furthermore, we decouple evaluation from exposure: background pre-warming checks do not log impressions until the user actually renders the view displaying the feature.

---

## 🔗 Related Specs
| Spec | Description |
| :--- | :--- |
| [A/B Testing & Experimentation SDK](ab-testing-experimentation-sdk.md) | Deep dive into MurmurHash bucketing, variance analysis, and statistical significance. |
| [App Modularization & DI System](app-modularization.md) | How feature flags intersect with decoupled module builds and dependency injection. |
| [Mobile Security & Privacy Engine](mobile-security-privacy-engine.md) | Managing secure MDM configurations and enterprise policy enforcement. |
