<div align="center">

![Distributed systems and mobile architecture](assets/banner.jpg)

# System Design & Engineering Leadership

### Backend correctness. Mobile architecture. Engineering judgment.

A domain-based preparation library for senior iOS engineers, staff engineers, Engineering Managers and Software Development Managers.

[Explore domains](#explore-by-industry-and-domain) · [Choose your role](#choose-your-preparation-track) · [Practice backend design](docs/backend-system-design-casebook.md) · [Prepare leadership stories](docs/behavioral-engineering-manager-staff-guide.md)

</div>

---

## What makes this repository useful

The distinguishing feature is the connection between **client behavior, backend correctness and engineering leadership**. Follow a payment from a disconnected phone to an ambiguous provider outcome, a message from local persistence to durable acceptance, or a streaming decision from device constraints to service reliability and cost.

| What you can practice here | Where the depth comes from |
| :--- | :--- |
| Client-to-service architecture | Mobile contracts, offline state, retries, compatibility and backend acknowledgement boundaries |
| Correctness under failure | Explicit invariants, transaction boundaries, duplicate events, stale workers and recovery drills |
| Domain-specific trade-offs | Payments, streaming, commerce, messaging, search, analytics and AI each have different failure consequences |
| Staff and EM perspectives | Implementation and cross-team adoption alongside ownership, staffing, delivery and incident leadership |
| Evidence-based communication | Primary references, metric definitions and a resume-based example of separating personal ownership from product scale |

These are concrete features of this checkout, not a claim that competing repositories lack them. The value comes from defending decisions and failure behavior, rather than memorizing a technology list.

## Choose your preparation track

| Your target | Start here | What to demonstrate |
| :--- | :--- | :--- |
| Senior iOS / mobile frontend | Pick a client design in your domain, then use the [cheatsheet](docs/cheatsheet.md) | State, concurrency, networking, persistence, performance and debugging |
| Staff / principal mobile | [Mobile platform guide](docs/mobile-platform-engineering-em.md) and [modularization](docs/app-modularization.md) | Technical depth, migration, cross-team adoption and durable architecture decisions |
| Backend EM / Amazon SDM | [Backend leadership guide](docs/backend-engineering-manager-guide.md) and [behavioral guide](docs/behavioral-engineering-manager-staff-guide.md) | Correctness, operations, people development and delivery judgment |
| Staff / principal backend | [Backend casebook](docs/backend-system-design-casebook.md) | APIs, schemas, concurrency, replay, failure recovery and technical influence |
| Director / engineering leadership | [Leadership guide](docs/behavioral-engineering-manager-staff-guide.md) | Actual multi-team scope, portfolio decisions, resource allocation and leadership development |

For a worked preparation path grounded in the author's experience, see [Rahul's resume-based plan](docs/rahul-backend-interview-plan.md). It identifies evidence already present and gaps that require real examples or hands-on work.

**Coverage boundary:** the frontend material focuses on iOS and mobile. Web frontend candidates need additional browser, JavaScript/TypeScript, accessibility and framework preparation. Backend candidates need implementation and operational practice beyond reading these documents.

## Explore by industry and domain

Product names in document titles identify familiar design problems. They do not imply access to those companies' internal architectures or private interview questions.

### Payments & financial workflows

**Central question:** how do you preserve a correct money movement when the client, service or provider can fail independently?

| Resource | Decisions to practice |
| :--- | :--- |
| [Payment checkout](docs/payment-checkout.md) | Stable request identity, pending outcomes, authentication challenges, persisted client state and reconciliation |
| [Authentication, OAuth and biometrics](docs/authentication-oauth-biometric.md) | Token lifecycle, credential storage and authentication recovery |
| [Mobile security and privacy](docs/mobile-security-privacy-engine.md) | Trust boundaries, key protection, encrypted storage and certificate rotation |

Pair these with the casebook's [checkout, payments and inventory exercise](docs/backend-system-design-casebook.md#1-checkout-payments-and-inventory). Be ready to explain why a timeout is not proof of failure and where duplicate-effect protection actually lives.

### Streaming, media & live experiences

**Central question:** how do you sustain playback quality across device constraints, variable networks and service failures?

| Resource | Decisions to practice |
| :--- | :--- |
| [Long-form video player](docs/video-streaming-player.md) | Playback lifecycle, adaptive streaming, DRM and downloads |
| [Short-form video feed](docs/video-feed-streaming.md) | Player reuse, prefetching, cancellation and memory pressure |
| [Audio player and offline mode](docs/spotify-audio-player.md) | Playback queues, background audio, system integration and offline media |
| [Video calling and WebRTC](docs/google-meet-webrtc.md) | Connection establishment, relay fallback, media sessions and thermal constraints |

Pair client behavior with the [live-event backend exercise](docs/backend-system-design-casebook.md#8-streaming-platform-and-live-event-control-plane). Separate media delivery from entitlement and metadata, and distinguish playback success from server request success.

### E-commerce, marketplaces & booking

**Central question:** how do you keep discovery responsive while inventory and order state remain correct?

| Resource | Decisions to practice |
| :--- | :--- |
| [Product catalog and discovery](docs/e-commerce-catalog.md) | Pagination, image-heavy screens and local cart state |
| [Property search and booking](docs/airbnb-search-booking.md) | Search coordination, reservations and booking state |
| [Search and autocomplete](docs/search-autocomplete.md) | Debounce, cancellation, stale results and local search |
| [Server-driven UI](docs/sdui-engine.md) | Schema compatibility, component registration and safe fallback |
| [Image loading library](docs/image-loading-library.md) | Caching, downsampling, request coalescing and cancellation |

Extend the client specifications with [exclusive inventory booking](docs/backend-system-design-casebook.md#2-booking-exclusive-inventory) and [search indexing](docs/backend-system-design-casebook.md#5-search-and-autocomplete). Defend concurrent allocation, index lag and old-client compatibility.

### Messaging, collaboration & productivity

**Central question:** what does an acknowledgement mean, and how do multiple devices recover a consistent view?

| Resource | Decisions to practice |
| :--- | :--- |
| [Messaging and chat](docs/messaging-chat.md) | Pending sends, ordering, receipts, reconnection and durable history |
| [Multi-workspace channel sync](docs/slack-channel-sync.md) | Workspace isolation, unread state and connection lifecycle |
| [Collaborative editor](docs/collaborative-editor.md) | Concurrent editing, operation models and convergence |
| [Offline-first sync](docs/offline-sync-engine.md) | Local persistence, conflict handling, replay and resynchronization |
| [Calendar client](docs/google-calendar.md) | Recurrence, time zones, range queries and synchronized state |

Practice [durable messaging](docs/backend-system-design-casebook.md#3-durable-messaging-and-offline-synchronization) and [distributed scheduling](docs/backend-system-design-casebook.md#10-distributed-scheduler-and-work-execution). Explain acceptance versus delivery, cursor expiry and stale worker ownership.

### Mobility, delivery & real-time tracking

**Central question:** how do you keep a useful live view when updates are delayed, devices sleep or connectivity disappears?

| Resource | Decisions to practice |
| :--- | :--- |
| [Geospatial tracking](docs/realtime-location-tracking.md) | Location updates, transport lifecycle, interpolation and battery use |
| [Delivery order tracking](docs/doordash-delivery-tracker.md) | Order transitions, realtime updates and Live Activities |
| [Push notification system](docs/push-notification-system.md) | Device registration, provider responses and background update limits |
| [Deep linking and universal links](docs/deep-linking-universal-links.md) | Routing, cold starts, domain association and authorization |

Use the [notification backend exercise](docs/backend-system-design-casebook.md#7-notification-delivery) to defend preference checks, expiry, retries and token cleanup. Provider acceptance is not proof that the device received or displayed a message.

### Social feeds, growth & analytics

**Central question:** how do you deliver relevant content and derive trustworthy measurements without losing control of freshness, privacy or cost?

| Resource | Decisions to practice |
| :--- | :--- |
| [Social feed](docs/social-feed.md) | Pagination, optimistic state and impression tracking |
| [User analytics event pipeline](docs/user-analytics-event-pipeline.md) | Event contracts, identity, aggregation and retention |
| [Analytics SDK](docs/analytics-sdk.md) | Durable collection, batching, retries and lifecycle constraints |
| [Feature flags](docs/feature-flag-system.md) | Local evaluation, defaults, configuration updates and recovery |
| [A/B testing SDK](docs/ab-testing-experimentation-sdk.md) | Assignment, exposure tracking and experiment compatibility |

Pair these with [feed and recommendation design](docs/backend-system-design-casebook.md#4-social-feed-and-recommendations) and [telemetry ingestion](docs/backend-system-design-casebook.md#6-analytics-and-telemetry-ingestion). Discuss late events, replay, sampling and deletion before trusting the resulting metric.

### Backend platforms & distributed systems

**Central question:** which invariants survive concurrency, overload, replication lag and regional failure?

| Resource | What it provides |
| :--- | :--- |
| [Backend EM, staff and leadership master guide](docs/backend-engineering-manager-guide.md) | Consistency, transactions, caching, CDC, security, capacity, migrations and organizational ownership |
| [Backend system design casebook](docs/backend-system-design-casebook.md) | Twelve authored exercises with data-model questions, failure drills and role-specific follow-ups |
| [Networking layer](docs/networking-layer.md) | The client side of API contracts, credential refresh, request handling and recovery |

The casebook also includes [multi-tenant reporting](docs/backend-system-design-casebook.md#9-multi-tenant-csat-and-reporting-platform) and [regional recovery](docs/backend-system-design-casebook.md#11-regional-failure-and-data-recovery). Start with authoritative state and access paths; add infrastructure only when its purpose and failure consequences are clear.

### AI applications & inference

**Central question:** how do you make model-backed features measurable, authorized and recoverable?

| Resource | Decisions to practice |
| :--- | :--- |
| [On-device AI architecture](docs/on-device-llm-ai-engine.md) | Runtime choice, weight and working memory, cancellation, retrieval and cloud routing |
| [Summarization systems](docs/how-ai-summarization-agents-work.md) | Tokenization, generation, context selection, provenance and output evaluation |
| [Primary AI reading map](docs/history-of-agentic-loops.md) | Distinguishing training, inference, search and tool orchestration through published research |

Practice the [AI inference gateway](docs/backend-system-design-casebook.md#12-ai-inference-gateway-and-evaluation-platform). Evaluate task quality separately from availability and speed. This material does not substitute for ML research or distributed-training expertise.

### Developer platforms, reliability & release engineering

**Central question:** how do you improve delivery while making failures easier to detect, contain and recover from?

| Resource | Decisions to practice |
| :--- | :--- |
| [Mobile platform leadership](docs/mobile-platform-engineering-em.md) | Module ownership, release coordination and incident response |
| [App modularization and dependency injection](docs/app-modularization.md) | Dependency boundaries, interfaces and adoption |
| [Mobile CI/CD](docs/mobile-ci-cd-pipeline.md) | Build pipelines, signing, validation and distribution |
| [App performance monitoring](docs/app-performance-monitoring.md) | Startup, responsiveness, resource usage and metric definitions |
| [Crash reporting and observability](docs/crash-reporting-sdk.md) | Diagnostics, breadcrumbs and abnormal termination analysis |

Connect these to the [backend guide's reliability and release sections](docs/backend-engineering-manager-guide.md). A backend rollback, an App Store rollout pause and a remote feature flag have different recovery capabilities.

### Leadership, behavioral preparation & reference

| Resource | How to use it |
| :--- | :--- |
| [Leadership and behavioral guide](docs/behavioral-engineering-manager-staff-guide.md) | Reconstruct actual decisions, people outcomes, conflicts, failures and learning |
| [Rahul's preparation plan](docs/rahul-backend-interview-plan.md) | See a resume-grounded evidence bank, scope assessment and preparation sequence |
| [Client architecture cheatsheet](docs/cheatsheet.md) | Recall patterns after studying their constraints |
| [Generic mobile problems](docs/generic-mobile-problems.md) | Practice cross-cutting client design |
| [Evidence standard and sources](docs/evidence-and-sources.md) | Check published behavior and distinguish measurements from proposed targets |
| [Repository review record](docs/repository-review.md) | Understand repairs, validation scope and remaining limitations |

## Turn reading into interview practice

1. **Choose a domain and role.** Read one client specification and its corresponding backend exercise.
2. **State the invariant.** Identify what must remain correct and which component enforces it.
3. **Draw the normal path.** Include APIs, authoritative data, persistence and acknowledgement boundaries.
4. **Inject a failure.** Try a timeout, concurrent request, duplicate event, stale worker or unavailable dependency.
5. **Defend the trade-off.** Explain the customer consequence, recovery, operational burden and cost using traceable inputs.
6. **Add your role's evidence.** Staff: implementation and influence. EM: people, ownership and execution. Leadership: portfolio and organizational decisions.
7. **Get feedback.** Record the incorrect assumption or unsupported claim, repair it and repeat the walkthrough.

Practice prompts are authored exercises, not leaked company questions. Use the actual posting and recruiter packet to decide which coding, design, management and writing rounds to rehearse.

Official preparation references: [Amazon SDM](https://amazon.jobs/content/en/how-we-hire/sdm-interview-prep), [Google hiring](https://www.google.com/about/careers/applications/how-we-hire/), [Google DeepMind](https://deepmind.google/careers/) and [SpaceX careers](https://www.spacex.com/careers/).

## Evidence, verification & contribution

This is a study library. Embedded client snippets are incomplete sketches rather than a compiled application, and remaining tuning choices require actual measurements. Resume results are candidate-reported. No hiring outcome, company level equivalence or universal production benchmark is promised.

Run the documentation check from the repository root:

```sh
python3 scripts/check_docs.py
```

It checks local links and anchors, code-fence balance, the ASCII hyphen rule and coverage of every document in this README. It does not compile Swift, benchmark systems or certify all technical claims.

Contribute a better failure walkthrough, a substantiated correction or a complete verified implementation. Follow [CONTRIBUTING.md](CONTRIBUTING.md), [REPO_SPEC.md](REPO_SPEC.md) and the [evidence standard](docs/evidence-and-sources.md).

## Author & license

Maintained by **Rahul Goel**. [Resume](https://therahulgoel.github.io/Rahul_Goel_Resume.pdf) · [GitHub](https://github.com/therahulgoel)

Licensed under [MIT](LICENSE).
