<div align="center">

# 📱 iOS Mobile System Design

### The most comprehensive system design resource for senior iOS engineers.
### Built for Engineering Manager & Staff Engineer interviews at Google, Uber, Meta, Apple & FAANG+.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/therahulgoel/ios-system-design/pulls)
[![Stars](https://img.shields.io/github/stars/therahulgoel/ios-system-design?style=social)](https://github.com/therahulgoel/ios-system-design/stargazers)

**If this helps you land your dream role — give it a ⭐ so others can find it too.**

[📖 Browse All 15 Specs](#-complete-problem-catalog) · [🚀 Interview Framework](#-the-45-minute-interview-framework) · [📊 Benchmarks](#-production-benchmarks-cheatsheet) · [👤 Author](#-about-the-author)

</div>

---

## 🎯 Who Is This For?

You are a **senior iOS or mobile engineer** with 7–15 years of experience preparing for:

- **Engineering Manager (EM)** interviews at Google, Uber, Meta, Apple, or equivalent  
- **Staff / Principal Engineer** interviews at FAANG-tier companies  
- Roles requiring mobile system design depth at **100M+ user scale**

This is **not** a LeetCode repo. This is the resource that teaches you to architect production systems on iOS — the way interviewers at top companies actually expect you to.

---

## ⚡ Why This Repository Is Different

Most system design resources are backend-focused. This one is built from the ground up for **client-side mobile architecture**.

| What most resources cover | What this covers |
| :--- | :--- |
| Database sharding & load balancing | AVPlayer pooling & adaptive bitrate |
| Distributed consensus (Raft/Paxos) | Operational Transformation & CRDTs |
| Horizontal server scaling | Memory pressure, OOM, and LRU eviction |
| API gateway design | Certificate pinning & token refresh interceptors |
| MapReduce pipelines | Offline-first sync with BGTaskScheduler |
| Message queues (Kafka) | WebSocket lifecycle, heartbeat & reconnect strategy |

Every spec in this repository is written with:
- ✅ **Real production numbers** (not estimates — from Netflix, Uber, Firebase, Apple WWDC, OWASP)
- ✅ **Swift 5.9+ code sketches** (async/await, Actors, SwiftUI + MVVM)
- ✅ **Actual SQLite schemas** and **API contracts** with request/response examples
- ✅ **Trade-off tables** with defended decisions (the #1 signal at Staff/EM level)
- ✅ **Interview tips** specific to each problem

---

## 🗂 Complete Problem Catalog

**15 production-grade system design specs** organized by domain.

### 🎬 Streaming Domain
*Video-on-demand, live sports, podcast platforms*

| Problem | Key Concepts | Target Companies |
| :--- | :--- | :--- |
| [📺 Long-form Video Streaming Player](docs/video-streaming-player.md) | HLS/DASH, AVPlayer, adaptive bitrate, FairPlay DRM, offline download | Google, Apple, Netflix-tier |
| [🎞 Short-form Video Feed](docs/video-feed-streaming.md) | AVPlayer pool (3-item), prefetch engine, low-bandwidth 240p, memory guard | Google, Meta, Snap |

### 💬 Messaging & Collaboration Domain
*Real-time communication, document sync, collaborative tools*

| Problem | Key Concepts | Target Companies |
| :--- | :--- | :--- |
| [💬 Instant Messaging & Chat](docs/messaging-chat.md) | SQLite WAL, message state machine, E2EE (Signal protocol), offline queue | Meta, Slack, Google |
| [📝 Collaborative Document Editor](docs/collaborative-editor.md) | Operational Transformation vs CRDTs, delta sync, presence/cursors, op log | Google, Notion, Dropbox |

### 📡 Real-Time & Geospatial Domain
*Location tracking, live data feeds, geospatial systems*

| Problem | Key Concepts | Target Companies |
| :--- | :--- | :--- |
| [🗺 Real-Time Location & Ride Tracking](docs/realtime-location-tracking.md) | WebSocket, Kalman filter, GPS batching, map delta rendering, battery guard | Uber, Lyft, DoorDash |

### 🏦 Payments & Dynamic UI Domain
*Fintech, e-commerce, server-controlled interfaces*

| Problem | Key Concepts | Target Companies |
| :--- | :--- | :--- |
| [🖥 Server-Driven UI (SDUI) Engine](docs/sdui-engine.md) | Component registry, schema versioning, fallback engine, analytics injection | Uber, Meta, Google |
| [💳 Payment Checkout Flow](docs/payment-checkout.md) | Tokenization, idempotency keys, payment state machine, PCI DSS, 3DS | Google Pay, Stripe, Square |
| [🛍 Product Catalog & Discovery Feed](docs/e-commerce-catalog.md) | Image-heavy grid, cursor pagination, cart sync, wishlist offline queue | Amazon, Shopify, Etsy |

### 🌐 Social & Feed Domain
*News feeds, content discovery, social interactions*

| Problem | Key Concepts | Target Companies |
| :--- | :--- | :--- |
| [📰 Infinite Social Feed](docs/social-feed.md) | Cursor-based pagination, image pipeline, offline feed (200 items), impression tracking | Meta, Twitter/X, LinkedIn |

### 🔧 Infrastructure & SDK Domain
*Client-side libraries, platform tooling, developer infrastructure*

| Problem | Key Concepts | Target Companies |
| :--- | :--- | :--- |
| [🖼 Image Loading Library](docs/image-loading-library.md) | 3-tier cache (NSCache → Disk → Network), downsampling, request deduplication, cancellation | Any image-heavy app |
| [🌐 Networking Layer / HTTP Client SDK](docs/networking-layer.md) | Protocol-based endpoints, auth interceptor, atomic token refresh, SPKI pinning | Any company |
| [📊 Mobile Analytics & Telemetry SDK](docs/analytics-sdk.md) | Ring buffer, SQLite journal, battery-aware batching, crash recovery, sampling | Uber, Meta, Google |
| [🚩 Feature Flag & Experimentation System](docs/feature-flag-system.md) | Fallback chain, synchronous local evaluation, kill switch (<5min), A/B tracking | Uber, Airbnb, Meta |
| [🔄 Offline-First Data Sync Engine](docs/offline-sync-engine.md) | Local-first architecture, dirty-flag sync, LWW conflict resolution, BGTaskScheduler | Google, Apple, Dropbox |
| [🧩 App Modularization & DI System](docs/app-modularization.md) | Module hierarchy, interface modules, DI (Needle pattern), build time, SPM | Uber, Google, Grab |

---

## 🏗 The 45-Minute Interview Framework

Walk into any mobile system design interview with this structure. Drive it yourself — do not wait to be guided.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Phase             │  Time      │  What You Must Achieve             │
├─────────────────────────────────────────────────────────────────────┤
│  1. Clarify        │  0–5 min   │  Define scope, scale, constraints  │
│  2. HLD            │  5–15 min  │  Draw full client-server component map │
│  3. Data & API     │  15–25 min │  Entities, endpoints, pagination   │
│  4. Deep Dives     │  25–40 min │  Own 2–3 hardest subsystems        │
│  5. Ops & Scale    │  40–45 min │  Failures, metrics, rollout        │
└─────────────────────────────────────────────────────────────────────┘
```

### The 4-Layer Client Architecture (Use This Every Time)

```
┌──────────────────────────────────────────────────────────────┐
│  View Layer         (SwiftUI — zero business logic)           │
├──────────────────────────────────────────────────────────────┤
│  Presentation Layer (ViewModel — state, user events)          │
├──────────────────────────────────────────────────────────────┤
│  Domain / Use Case  (Business rules, repository protocols)    │
├──────────────────────────────────────────────────────────────┤
│  Data Layer         (Repository: Remote Source + Local Source)│
│     ├── Remote  → URLSession / gRPC / WebSocket               │
│     └── Local   → SQLite / CoreData / NSCache / Keychain      │
└──────────────────────────────────────────────────────────────┘
```

---

## 📊 Production Benchmarks Cheatsheet

Quote these numbers in interviews. Every figure is sourced from public engineering data.

| Metric | Target | Source |
| :--- | :--- | :--- |
| Cold start (p50 device) | `< 1.2s` | Apple HIG, Uber Engineering |
| Warm start | `< 400ms` | Google Play Vitals |
| UI frame budget (60fps) | `16.6ms` | CoreAnimation |
| UI frame budget (120Hz ProMotion) | `8.3ms` | ProMotion / CADisplayLink |
| Memory before OOM warning | `~250MB` | WWDC 2018 — iOS Memory Deep Dive |
| Hard OOM crash threshold | `~350–400MB` | iOS crash telemetry |
| Decoded image footprint | `width × height × 4 bytes` | UIImage ARGB8888 |
| Feed page payload | `< 15KB compressed` | Instagram/Facebook Newsfeed engineering |
| API p99 latency target | `< 200ms` client-side | Uber API design principles |
| Search debounce | `300ms` | Apple Human Interface Guidelines |
| WebSocket heartbeat | `30s` | RFC 6455, Uber production |
| SQLite WAL checkpoint | Every `1,000 writes` or `5s` | SQLite documentation |
| Analytics flush | `30s` or `100 events` | Firebase Analytics production behavior |
| HLS segment size | `6s` | Apple HLS Authoring Spec |
| Video pre-buffer target | `10s` within `3s` of play start | Netflix Tech Blog |
| AVPlayer instance overhead | `~15MB` | Measured AVFoundation profiling |
| Cert pinning rotation | Every `60 days` | OWASP Mobile Security Standard |
| BGAppRefreshTask window | Max `30s` runtime | Apple Background Tasks |
| Crash-free session target | `> 99.9%` | Firebase Crashlytics baseline |

---

## 🔑 Core Technical Decision Reference

### When to Use Which Storage

| Data Type | Solution | Why |
| :--- | :--- | :--- |
| Structured / relational | SQLite (WAL mode) | Concurrent reads, fast writes, indexed queries |
| Graph / object graph | Core Data | Apple-native, relationship traversal |
| Secrets / tokens | Keychain | Hardware-backed encryption, survives app reinstall |
| User preferences | UserDefaults | Fast synchronous reads, small data only |
| Large media / files | FileManager (`/Caches` or `/Application Support`) | Managed by OS, not in DB |
| In-session objects | NSCache | Auto-evicts under memory pressure |

### Real-Time Transport Selection

| Protocol | Choose When | iOS API |
| :--- | :--- | :--- |
| **WebSocket** | Bidirectional, low-latency (chat, location) | `URLSessionWebSocketTask` |
| **Server-Sent Events** | One-way server push, simpler than WS | `URLSession` streaming |
| **gRPC Streaming** | High-frequency, strongly typed, internal | `gRPC-Swift` |
| **APNs Push** | App backgrounded, infrequent alerts | `UserNotifications` |
| **HTTP/2** | Multiple concurrent API requests | `URLSession` (automatic) |

### Pagination: Always Cursor-Based for Feeds

```
✅  Cursor-based:  GET /feed?after_cursor=eyJpZCI6MTIzfQ==&limit=20
    → Stable during inserts | O(1) server cost | No duplicates

❌  Offset-based:  GET /feed?page=5&limit=20
    → Items shift on insert | O(n) server scan | Duplicates on fast-moving feeds
```

---

## 📁 Repository Structure

```
ios-system-design/
├── README.md                          ← You are here
├── REPO_SPEC.md                       ← Architecture conventions (MVVM, URLSession, SwiftUI)
└── docs/
    ├── Streaming
    │   ├── video-streaming-player.md  ← Long-form VOD (HLS, ABR, Offline Download)
    │   └── video-feed-streaming.md   ← Short-form Feed (AVPlayer Pool, Prefetch)
    ├── Messaging & Collaboration
    │   ├── messaging-chat.md          ← Chat (SQLite, E2EE, WebSocket, Offline Queue)
    │   └── collaborative-editor.md   ← Docs (OT vs CRDTs, Delta Sync, Presence)
    ├── Real-Time & Geospatial
    │   └── realtime-location-tracking.md ← Ride Tracking (Kalman, WebSocket, Map Delta)
    ├── Payments & Dynamic UI
    │   ├── sdui-engine.md             ← Server-Driven UI (Schema, Registry, Fallback)
    │   ├── payment-checkout.md        ← Payments (Idempotency, 3DS, State Machine)
    │   └── e-commerce-catalog.md     ← Catalog (Grid, Cart, Wishlist, Image Pipeline)
    ├── Social & Feed
    │   └── social-feed.md             ← Feed (Cursor Pagination, Offline, Impressions)
    └── Infrastructure & SDK
        ├── image-loading-library.md   ← Image Loader (3-tier Cache, Dedup, Cancellation)
        ├── networking-layer.md        ← HTTP SDK (Auth Interceptor, Pinning, Retry)
        ├── analytics-sdk.md           ← Telemetry SDK (Ring Buffer, Battery-aware)
        ├── feature-flag-system.md     ← Feature Flags (Kill Switch, A/B, Local Eval)
        ├── offline-sync-engine.md     ← Offline Sync (Dirty Flag, LWW, BGTask)
        └── app-modularization.md     ← Modularization (DI, Interface Modules, SPM)
```

---

## 🧠 What Makes a Staff/EM Answer Different

The same question gets different ratings at different levels. Here's what separates L5 from L6/L7:

| Dimension | Senior (L5) | Staff / EM (L6/L7) |
| :--- | :--- | :--- |
| **Scope** | Designs what's asked | Explicitly defines in-scope AND out-of-scope |
| **Numbers** | "We'll use a cache" | "L1 NSCache 50MB, 7-day TTL on disk, evict on `didReceiveMemoryWarning`" |
| **Trade-offs** | Lists options | Defends a choice with cost/complexity/team reasoning |
| **Failure modes** | Mentions errors | Proactively covers stale cache, offline fallback, circuit breaker |
| **Observability** | "We'd add logging" | Names specific metrics: p99 render time, OOM rate, crash-free sessions |
| **API design** | Shows endpoint paths | Defines cursor pagination, field masking, versioning, idempotency |
| **Drive** | Answers questions | Owns the interview, states agenda, moves through phases themselves |

---

## 🤝 Contributing

Found an issue, want to add a new problem, or have a better approach for a subsystem?  
**PRs are welcome.** Please follow the spec format in [REPO_SPEC.md](REPO_SPEC.md).

---

## 👤 About the Author

Built by a mobile engineering leader with **12+ years** of experience scaling iOS apps to **100M+ users** across streaming, social, payments, and e-commerce.

Connect on LinkedIn: **[linkedin.com/in/therahulgoel](https://www.linkedin.com/in/therahulgoel/)**

If this repository helped you level up or land an offer — a ⭐ star takes one second and helps this reach the engineers who need it most.

---

<div align="center">

**📱 iOS System Design · Built for Staff & EM interviews · 15 Production-Grade Specs**

[⭐ Star this repo](https://github.com/therahulgoel/ios-system-design) · [🔗 Share on LinkedIn](https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/therahulgoel/ios-system-design) · [🐦 Share on Twitter](https://twitter.com/intent/tweet?text=The+most+comprehensive+iOS+mobile+system+design+resource+for+Staff+%26+EM+interviews+at+FAANG%2B.+15+production-grade+specs+with+real+numbers.&url=https://github.com/therahulgoel/ios-system-design)

</div>