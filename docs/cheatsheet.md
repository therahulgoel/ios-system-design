# Mobile System Design — Master Cheatsheet
### One-page reference for Staff & EM interviews. All numbers are real and sourced.

---

## The Universal 45-Minute Framework

```
0–5 min   → CLARIFY:    Scope (in/out), scale (DAU), offline?, platform?
5–15 min  → HLD:        4-layer diagram + data flow (CDN → API → Cache → UI)
15–25 min → DATA/API:   Entities, endpoints, cursor pagination, payload format
25–40 min → DEEP DIVE:  2-3 hardest subsystems (you choose which ones)
40–45 min → OPS:        Failure modes, metrics, rollout strategy, A/B gates
```

**Staff/EM signal**: State your agenda at the start. *"I'll spend 5 minutes on scope, then walk through the full architecture, then deep-dive the sync engine and the offline queue. Does that work?"*

---

## Storage Decision Tree

| Use Case | Solution | Key Config |
| :--- | :--- | :--- |
| Structured data, complex queries | SQLite (WAL mode) | `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;` |
| Object graph, Apple ecosystem | Core Data | NSPersistentContainer with background context for writes |
| Secrets, tokens, keys | Keychain | `kSecAttrAccessibleAfterFirstUnlock` for background access |
| Simple preferences | UserDefaults | Non-sensitive only; do NOT store tokens here |
| Large binary / media | FileManager `/Caches` | OS can purge; use `/Application Support` for user data |
| In-session, auto-evict | NSCache | Responds to `didReceiveMemoryWarningNotification` automatically |
| Concurrent in-session | Actor (Swift 5.5+) | Compile-time data race protection |

**SQLite WAL numbers**: 2–3x faster writes than DELETE journal mode. Checkpoint every 1,000 writes or 5s. Supports concurrent readers + one writer. Source: [sqlite.org/wal.html](https://sqlite.org/wal.html)

---

## Caching Policy Reference

| Data Type | L1 (Memory) | L2 (Disk) | TTL | Eviction | Write Policy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Feed items | 50MB NSCache | 100MB | 5 min | LRU | Write-through |
| Images (decoded) | 50MB NSCache | 500MB | 7 days | LRU + memory pressure | Write-around |
| Auth tokens | Keychain only | Keychain | Manual revoke | Never auto-evict | Write-through |
| User profile | 10MB NSCache | SQLite | No TTL | Manual invalidate | Write-back |
| Search results | 20MB NSCache | SQLite | 10 min | LRU (100 queries) | Write-through |
| Feature flags | NSDictionary | UserDefaults + SQLite | Server-defined | On config refresh | Write-through |
| API responses | URLCache | URLCache disk | ETag-based | LRU | Conditional GET |

**Image memory math**: `width × height × 4 bytes` (ARGB8888). A 1000×1000px image = **4MB decoded**. Always downsample to display size before caching. Source: UIImage ARGB8888 pixel format.

---

## Real-Time Transport Selection

| Protocol | Choose When | Avoid When | iOS API | Real Usage |
| :--- | :--- | :--- | :--- | :--- |
| **WebSocket** | Bidirectional, low-latency | One-way, infrequent | `URLSessionWebSocketTask` | Chat, location tracking |
| **gRPC Streaming** | High-frequency, typed, internal services | Public/browser APIs | `gRPC-Swift` | Internal microservices |
| **SSE** | One-way server push | Bidirectional needed | `URLSession` stream | Live scores, notifications |
| **Long Polling** | WebSocket not available | High frequency | `URLSession` | Fallback only |
| **APNs** | App backgrounded | Foreground real-time | `UserNotifications` | Push alerts |
| **HTTP/2** | Multiple concurrent requests | Single large download | `URLSession` (auto) | All REST APIs |

**WebSocket heartbeat**: 30s ping/pong to detect zombie connections (RFC 6455 recommendation, confirmed by Uber Engineering production config).

**Reconnect backoff**: `delay = min(base × 2^attempt, maxDelay) × (1 ± jitter)` — base: 1s, max: 60s, jitter: ±30%. Jitter prevents thundering herd after server restart.

---

## Pagination Patterns

```swift
// ✅ ALWAYS USE THIS for feeds, timelines, any ordered content
GET /v1/feed?after_cursor=eyJpZCI6MTIzfQ==&limit=20
// → cursor is server-generated opaque token (base64 JSON or UUID)
// → O(1) server cost at any depth
// → Stable during concurrent inserts (no item duplication or skipping)

// ❌ NEVER USE THIS for dynamic content
GET /v1/feed?page=5&limit=20
// → New items inserted between requests = items skipped or duplicated
// → O(n) server scan for deep pages (page 500 = scan 10,000 rows)
// → Only acceptable for: static data, search results with fixed ranking
```

---

## API Design Principles (Staff-Level Signal)

```
Field masking:     GET /v1/posts?fields=id,title,thumbnail    → 40-60% payload reduction
Versioning:        /v2/ for breaking changes; header for non-breaking
Idempotency:       Idempotency-Key: <UUID> header for mutations (payments, messages)
Compression:       Accept-Encoding: gzip → 60-70% smaller JSON payloads
Cursor in body:    POST for complex search queries with filters; GET for simple feeds
gRPC vs REST:      Protobuf payload ~5x smaller, ~3x faster serialization than JSON
Batch endpoint:    POST /v1/batch for multiple operations in one RTT
```

---

## Concurrency Patterns

```swift
// ✅ Swift Concurrency — thread-safe shared state
actor ImageCache {
    private var store: [URL: UIImage] = [:]
    func image(for url: URL) -> UIImage? { store[url] }
    func store(_ image: UIImage, for url: URL) { store[url] = image }
}

// ✅ GCD — background DB writes (never on main thread)
let dbWriteQueue = DispatchQueue(label: "com.app.db.write", qos: .utility)
let dbReadQueue  = DispatchQueue(label: "com.app.db.read", attributes: .concurrent)

// ✅ Async/await on ViewModel
@MainActor
class FeedViewModel: ObservableObject {
    @Published var items: [FeedItem] = []
    func loadFeed() async { items = await repository.fetchFeed() }
}

// ❌ Never do this — main thread DB read blocks UI
let results = db.query("SELECT * FROM messages") // ON MAIN THREAD
```

---

## Offline-First Pattern (Universal)

```
All WRITES:
  UI action → ViewModel → SQLite (immediate) → mark dirty=1 → return to UI
  Background SyncEngine polls dirty=1 → POST to server → mark dirty=0

All READS:
  Always from SQLite — UI never waits for network

Conflict resolution:
  Last-Write-Wins (LWW)   → server timestamp wins; simple, use for most entities
  Operational Transform   → server authority; use for text documents (Google Docs)
  CRDTs                   → peer merge, no authority; use for true offline-first (Figma, Notion)
  Manual merge UI         → surface conflict to user; use when data loss is unacceptable
```

---

## Image Pipeline (Universal — Used in 80% of Specs)

```
imageView.load(url, targetSize: imageView.bounds.size × UIScreen.scale)
    ↓
L1: NSCache (key: url+targetSize) → HIT: return UIImage (decoded, display-ready)
    ↓ MISS
L2: DiskCache (key: SHA256(url)) → HIT: decode async on background queue → store L1
    ↓ MISS
Dedup check: in-flight request for same URL? → YES: add completion to observer set
    ↓ NO
URLSession fetch on background queue
    → Decode JPEG/PNG (background thread, never main)
    → Downsample to targetSize (CGImageSourceCreateThumbnailAtIndex — key API)
    → Store L1 + L2
    → Notify all observers
```

**Critical**: `CGImageSourceCreateThumbnailAtIndex` with `kCGImageSourceThumbnailMaxPixelSize` decodes directly at the target size — avoids allocating full-resolution bitmap. This is the single biggest memory optimization in image loading.

---

## Security Checklist (Fintech / Healthcare / Enterprise)

| Concern | Solution | Standard |
| :--- | :--- | :--- |
| Secrets at rest | Keychain with `kSecAttrAccessibleAfterFirstUnlock` | Apple Security Framework |
| Data at rest (files) | `FileProtectionType.completeUnlessOpen` | iOS Data Protection |
| Data in transit | TLS 1.3, HSTS | RFC 8446 |
| Certificate validation | Public key pinning (SPKI SHA-256), rotate every 60 days | OWASP MASTG |
| Token storage | Keychain (never UserDefaults, never NSCache) | OWASP MASTG |
| PAN / card numbers | Never touch raw PANs; tokenize via PCI DSS certified SDK | PCI DSS |
| Biometric auth | Secure Enclave via LocalAuthentication framework | Apple CryptoKit |
| API attestation | DCAppAttestService proves legitimate app binary to server | Apple DeviceCheck |
| Debug logging | Never log tokens, PIIs, or payment data in any build | OWASP MASTG |

---

## Production Benchmarks — Complete Reference

| Metric | Target | Source |
| :--- | :--- | :--- |
| Cold start (p50) | < 1.2s | Apple HIG; WWDC 2019 Session 423 |
| Warm start | < 400ms | Google Play Vitals thresholds |
| UI frame budget (60fps) | 16.6ms | CoreAnimation CADisplayLink |
| UI frame budget (120Hz) | 8.3ms | ProMotion — CADisplayLink |
| OOM warning (iPhone 12 class) | ~250MB | WWDC 2018 — iOS Memory Deep Dive |
| Hard OOM crash | ~350–400MB | Measured crash telemetry |
| Image memory | width × height × 4 bytes | UIImage ARGB8888 pixel format |
| Feed page payload | < 15KB compressed | Instagram/Facebook Newsfeed Engineering |
| API p99 latency (client budget) | < 200ms | Uber API Design Principles |
| Search debounce | 300ms | Apple HIG search patterns |
| WebSocket heartbeat | 30s | RFC 6455 §5.5.2; Uber production |
| Reconnect backoff (max) | 60s | Industry standard; AWS SDK reference |
| HLS segment duration | 6s | Apple HLS Authoring Specification |
| Video pre-buffer target | 10s within 3s | Netflix Tech Blog |
| AVPlayer instance overhead | ~15MB | AVFoundation profiling, Instruments |
| SQLite WAL checkpoint | Every 1,000 writes or 5s | SQLite WAL documentation |
| Analytics flush trigger | 30s or 100 events | Firebase Analytics production behavior |
| Analytics event size | ~200–500 bytes JSON | Firebase Analytics |
| BGAppRefreshTask runtime | Max 30s | Apple Background Tasks WWDC 2019 |
| Cert pinning rotation | Every 60 days | OWASP Mobile Security Testing Guide |
| Crash-free session target | > 99.9% | Firebase Crashlytics industry baseline |
| ANR / Hang rate target | < 0.1% sessions | Google Play Vitals P1 threshold |
| Feature flag kill switch | < 5 min to 100% users | Uber/Airbnb feature flag SLA |
| Token bucket refill (search) | 2 tokens/second, max 10 | Standard rate limit for search APIs |

---

## Common Mistakes by Problem Type

### Feed Design
- ❌ Using offset pagination (`page=5`) on a live feed → duplicates on fast inserts  
- ✅ Cursor-based (`after_cursor=...`) — O(1), stable

### Image Loading
- ❌ Decoding full-resolution image (4K) and scaling with UIImageView.contentMode  
- ✅ Decode directly at display size using `CGImageSourceCreateThumbnailAtIndex`

### Messaging
- ❌ Generating new message ID on retry → server creates duplicate message  
- ✅ UUID generated once on `Send` tap, used as idempotency key on all retries

### Collaborative Editor
- ❌ Last-write-wins (timestamp) for text documents → data loss on concurrent edits  
- ✅ Operational Transformation (OT) — server transforms concurrent ops

### Payment
- ❌ Showing error on network timeout during payment  
- ✅ Poll `/status` endpoint every 5s for up to 5 minutes — never assume failure

### Real-Time Location
- ❌ Raw GPS coordinates every 1s → battery drain + network noise  
- ✅ Kalman filter on device + batch 3-5 positions per frame + distanceFilter: 10m

### Offline Sync
- ❌ Blocking UI on network sync result  
- ✅ Write to SQLite immediately, sync in background, UI never waits for network

### Auth Token Refresh
- ❌ Multiple concurrent 401 responses each trigger a token refresh → race condition  
- ✅ Atomic token refresh with request queue — one refresh, pending requests wait

---

## Related Specs Map

```
Image Loading Library ←─── Social Feed
                      ←─── E-commerce Catalog
                      ←─── Short-form Video Feed

Networking Layer ←──────── All 15 specs (foundation)

Offline Sync Engine ←────── Messaging Chat (pending message queue)
                    ←────── Collaborative Editor (op log)
                    ←────── E-commerce Catalog (cart/wishlist)

Analytics SDK ←──────────── Feature Flag System (impression tracking)
              ←──────────── SDUI Engine (component events)
              ←──────────── Social Feed (impression events)

Feature Flag System ←─────── All specs (kill switch for every major feature)

SDUI Engine ←────────────── E-commerce Catalog (home screen cards)
            ←────────────── Payment Checkout (dynamic payment methods)
```

---

*This cheatsheet is a companion to the 15 full specs in `docs/`. For deep dives, API contracts, and Swift code, read the individual spec files.*
