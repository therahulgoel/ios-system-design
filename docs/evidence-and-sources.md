# Evidence Standard and Verified Sources

Reviewed on 4 October 2026. Distinguish a published protocol limit, a measurement for a particular system, a candidate-reported achievement, and a proposed architecture. They are different kinds of evidence.

## Rules for using this repository

- Cite a primary source beside a factual claim. The source must support the exact claim, including units, version and applicable context.
- A company's name or "industry standard" is not a source for a latency, memory or success-rate target.
- Set targets from actual user needs and workload evidence. When inputs are missing, identify the missing input or use a symbolic model.
- Treat resume results as candidate-reported until underlying definitions and evidence are established.
- Educational sketches cannot establish production throughput, reliability, company implementation or personal experience.
- Do not quote private hiring rubrics, exact interview questions or frequency ratings without attributable public evidence. Author practice questions as practice questions.
- Do not add dummy records or invented benchmark outcomes. Protocol and schema explanations should describe behavior without presenting invented payloads as data.

## Corrected technical claims

| Topic | Supported interpretation | Primary source |
| :--- | :--- | :--- |
| SQLite WAL | Readers can coexist with a writer; only one writer exists at a time. Checkpointing and durability settings matter. No universal write-speed multiplier. | [SQLite WAL](https://sqlite.org/wal.html) |
| WebSocket heartbeat | Ping/pong is defined; a heartbeat interval is a deployment choice, not an RFC-mandated constant. | [RFC 6455](https://www.rfc-editor.org/rfc/rfc6455) |
| Conditional HTTP | A 304 omits the representation body; traffic and latency still exist. | [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) |
| PKCE | The code verifier is 43 to 128 characters from the specified character set; other flow requirements still apply. | [RFC 7636](https://www.rfc-editor.org/rfc/rfc7636) |
| OAuth | Use the security BCP to evaluate flow, refresh-token and replay protections. | [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700) |
| Idempotency | Reuse stable identity for one operation; concurrency, persistence, scope and retention determine protection. | [Stripe contract](https://docs.stripe.com/api/idempotent_requests) |
| Outbox | Atomic business-state and outbox commit solves a local dual write; duplicate delivery and external effects need handling. | [AWS outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) |
| Database migration | Additive DDL may still acquire locks; verify the operation and version. | [PostgreSQL ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html) |
| Replica reads | Asynchronous replication can lag and may lose unreplicated writes on failure. | [PostgreSQL replication](https://www.postgresql.org/docs/current/warm-standby.html) |
| Kafka processing | Ordering and transactional guarantees have explicit boundaries; external side effects need destination cooperation. | [Kafka design](https://kafka.apache.org/41/design/design/) |
| AASA retrieval | Starting with iOS 14 and macOS 11, associated-domain retrieval uses an Apple-managed CDN. | [Apple associated domains](https://developer.apple.com/documentation/xcode/supporting-associated-domains) |
| Background push | Delivery and background execution are system-controlled and can be throttled; they are unsuitable as a guaranteed urgent sync mechanism. | [Apple background updates](https://developer.apple.com/documentation/usernotifications/pushing-background-updates-to-your-app) |
| APNs errors | Classify provider response status and reason; 400 BadDeviceToken differs from 410 Unregistered. | [Apple APNs responses](https://developer.apple.com/documentation/usernotifications/handling-notification-responses-from-apns) |
| Memory pressure | Use jetsam reports and device evidence instead of a universal app memory threshold. | [Apple jetsam analysis](https://developer.apple.com/documentation/xcode/identifying-high-memory-use-with-jetsam-event-reports) |
| Mobile phased release | Apple's automatic update schedule spans seven days. Users can manually download at any time. Pausing distribution does not replace installed binaries. | [Apple phased release](https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases) |
| Redis HyperLogLog | Approximate cardinality has documented memory and error behavior; verify suitability for the business metric. | [Redis HyperLogLog](https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/) |

## What to measure by domain

| Domain | Measurement and verification work |
| :--- | :--- |
| Streaming | Startup, stalls, success denominator, bytes, codec/device cohorts, rights and CDN costs |
| Messaging and sync | Acceptance durability, convergence, reconnect recovery, duplicate handling, ordering and battery impact |
| Payments and booking | Accepted operation identity, ambiguous outcomes, duplicate effects, reservation races and reconciliation age |
| Identity and security | Authorization paths, token lifecycle, tenant boundaries, abuse, revocation failure and secret rotation |
| Search and feeds | Freshness, query distribution, pagination stability, deletion, ranking fallback and hot partitions |
| SDKs and modularization | Initialization overhead, memory, dropped work, build distribution, adoption and dependency boundaries |
| Analytics | Event acceptance, replay, lateness, consent, deletion, sampling and aggregate accuracy |
| AI | Exact model/runtime, hardware, context, memory, latency distribution, quality evaluation and data permissions |
| Leadership | Personal scope, decision, alternatives, actual interventions, business outcomes and evidence of learning |

## Repository verification

Run `python3 scripts/check_docs.py` from the repository root. It checks local Markdown paths and anchors, fenced-block balance, forbidden long dashes, and README catalog coverage. It does not compile embedded Swift, render every diagram, verify external URLs, or certify technical statements. Review [the repair record](repository-review.md) for the actual audit scope.


## Learning first, verification second

Worked lessons must explain the request path, state, enforcement and failure recovery on the page. A source link or a command to "explain consistency" cannot replace that teaching. Read the conceptual walkthrough before consulting the source for exact platform/version behavior.

The repaired performance tables describe mechanisms and the observations needed to assess them. They do not supply fabricated measured gains. During an interview, derive estimates from given inputs and state missing measurements explicitly. Rehearsal designs must also remain distinct from career stories.
