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
| In-session, auto-evict | NSCache / LRUCache | Responds to `didReceiveMemoryWarningNotification` or max cost bounds |
| Concurrent in-session | Actor (Swift 5.5+) | Compile-time data race protection |

**LRU Cache Implementation Math & Design**:
- **Data Structure**: `DoublyLinkedList` + `Dictionary<Key, Node>` $\rightarrow$ $O(1)$ lookup, $O(1)$ insertion, $O(1)$ eviction.
- **Thread Safety**: Wrap inside a Swift `actor` or `NSLock` for concurrent access.
- **Cost-Based Eviction**: Track total byte cost (`width * height * 4` for images) and auto-evict least recently used node when exceeding max cost (e.g., 50MB).

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

## 🤖 AI, LLM & Mobile AI Tech Stack Reference

### 1. Core Terms & Architecture Checklist
| Concept | Definition & Mobile Context | Key Equation / Reference |
| :--- | :--- | :--- |
| **Token** | Chunks of characters processed by LLMs | $1\text{ token} \approx 0.75\text{ words}$ (English) |
| **Context Window** | Max token limit per prompt + completion | $2,048 - 4,096$ tokens on-device |
| **Quantization** | Weight compression from FP16 (16-bit) to INT4 (4-bit) | FP16: $6\text{GB} \rightarrow$ INT4: $1.5\text{GB}$ file / $\le 500\text{MB}$ RAM |
| **RAG** | Retrieval-Augmented Generation via local vector search | Cosine Similarity $\ge 0.80$ match |
| **MCP** | Model Context Protocol — JSON-RPC 2.0 tool calling protocol | Host $\leftrightarrow$ MCP Client $\leftrightarrow$ Native iOS Tools |
| **KV-Cache** | Pre-computed Key-Value attention states stored in RAM | $\text{KV Cache RAM} \approx 2 \cdot L \cdot H \cdot D \cdot S \cdot \text{Bytes}$ |
| **Embeddings** | Dense vector numerical array representing text semantics | 384 dimensions (MobileBERT / MiniLM) |
| **Hardware Scheduling** | Execution dispatch across ANE, GPU, and CPU | ANE (Neural Engine) $\rightarrow$ Metal GPU $\rightarrow$ CPU fallback |

### 2. Internals & Memory Math (Quote in Interviews)
* **Model Weight Memory Equation**:
  $$\text{RAM Footprint} = \frac{\text{Parameter Count (Billions)} \times \text{Bits per weight}}{8}$$
  * **3B FP16**: $3 \times 2 = 6\text{ GB RAM}$ $\rightarrow$ **Fails on iOS (OOM crash)**
  * **3B INT4**: $3 \times 0.5 = 1.5\text{ GB File}$ $\rightarrow$ Memory-mapped (`mmap`) execution $\mathbf{\le 500\text{MB RAM}}$.
* **KV-Cache Memory Equation**:
  $$\text{KV Cache RAM (Bytes)} = 2 \times N_{\text{layers}} \times N_{\text{heads}} \times d_{\text{head}} \times N_{\text{seq}} \times \text{BytesPerElement}$$
  * *Example*: Llama-3-8B FP16 with 2048 sequence length $= 1.07\text{GB}$.
  * *On-Device Optimization*: Use **Grouped-Query Attention (GQA)** + **INT8 Quantized KV-Cache** $\rightarrow$ shrinks KV-Cache to **$\sim 128\text{MB}$**.

### 3. Model Context Protocol (MCP) Client Architecture
```ascii
+-------------------------------------------------------------------------+
|                              iOS Host App                               |
|                                                                         |
|  +--------------------+   JSON-RPC 2.0   +---------------------------+  |
|  | Local LLM (CoreML) | <---------------> | MCP Client Coordinator    |  |
|  +--------------------+                   +-------------+-------------+  |
|                                                         |                |
|                                           Dispatches    v                |
|                                           +---------------------------+  |
|                                           | Native iOS Tool Handlers  |  |
|                                           |  - SQLite Database Tool   |  |
|                                           |  - Event Calendar Tool    |  |
|                                           |  - Location Service Tool  |  |
|                                           +---------------------------+  |
+-------------------------------------------------------------------------+
```

### 4. On-Device Hardware Execution Decision Tree
```
Is Apple Neural Engine (ANE) available & model in CoreML format?
├── YES ──> Dispatch to ANE (Zero CPU usage, max power efficiency, TTFT < 100ms)
└── NO  ──> Is Metal Performance Shaders (MPS) GPU runtime available?
             ├── YES ──> Dispatch to Metal GPU (ExecuTorch / llama.cpp MPS backend)
             └── NO  ──> Fallback to Multi-threaded CPU (High thermal wear, battery drain)
```

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
| On-Device LLM Model RAM Budget | $\le 500\text{MB}$ RAM (INT4 3B model) | Apple WWDC 2024 / Meta ExecuTorch |
| LLM Time to First Token (TTFT) | $< 100\text{ms}$ (Local NPU) | Apple Neural Engine / Snapdragon NPU Benchmark |
| Local Vector Search Latency | $< 15\text{ms}$ for 10,000 vectors | USearch / HNSW C++ Benchmark |
| Mobile CI Clean Build Budget | $< 6\text{ minutes}$ | Bazel / Tuist Remote Cache Benchmark |
| Secure Enclave Key Generation | $< 80\text{ms}$ | Apple Secure Enclave Hardware Spec |

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

### On-Device AI / LLM
- ❌ Loading unquantized 16-bit FP weights directly into RAM (`Data(contentsOf: url)`).  
- ✅ Memory-map INT4 4-bit weights (`mmap`) & limit model execution memory to $< 500\text{MB}$.

---

## Related Specs Map

```
On-Device LLM & AI Engine ←─── Local Vector DB (SQLite VSS / USearch)
                           ←─── Streaming UI (AsyncSequence)
                           ←─── Hybrid Cloud Fallback Router

Mobile Security Engine    ←─── Secure Enclave Hardware Key Derivation
                           ←─── App Attest (Apple DeviceCheck)
                           ←─── SPKI TLS 1.3 Pinning & SQLCipher

Mobile Platform Eng (EM)   ←─── Module Interface vs Implementation Graph
                           ←─── Core Release Train & Canary Rollout (1% -> 100%)
                           ←─── Sev-1 Incident Triage & Kill Switches

Image Loading Library      ←─── Social Feed, E-commerce Catalog, Video Feed
Networking Layer           ←─── All specs (foundation)
Offline Sync Engine        ←─── Messaging Chat, Collaborative Editor, Catalog
```

---

*This cheatsheet is a companion to the full production specs in `docs/`. For deep dives, API contracts, and Swift code, read the individual spec files.*
