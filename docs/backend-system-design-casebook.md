# Backend System Design Casebook

Use this with the [backend guide](backend-engineering-manager-guide.md). These are authored practice exercises, not claims about questions asked by a particular company. No production workload is invented. Use actual measurements or prompt-provided constraints; otherwise keep capacity symbolic.

For each exercise, produce an API contract, data model, architecture, invariant, crash walkthrough, capacity model, operational plan, and role-specific explanation. Practice describing one normal request and one ambiguous failure before expanding the architecture.

## 1. Checkout, payments and inventory

**Problem:** accept an order, reserve inventory, request payment, and give the customer a recoverable status across retries.

**Clarify:** one merchant or marketplace? Authorization versus capture? Can orders partially fulfill? What is the reservation policy? Who owns refunds? What happens when payment confirms after expiry?

**Invariant:** an accepted operation identity must not produce duplicate business effects; inventory allocation must not exceed available stock.

**API and data:** separate order identity from payment-attempt identity. Specify a status endpoint, caller-scoped idempotency key and payload fingerprint. Model orders, line items, reservations, attempts, provider event identities and outbox records. State which unique constraints and transaction enforce each invariant.

**Baseline:** transactionally create the order and reservation with an outbox event. A worker requests payment using stable identity. Persist unknown outcomes for reconciliation. Verify provider callbacks and deduplicate them. Keep state transitions monotonic where appropriate, with explicit terminal and recovery states.

**Failure drills:** concurrent same-key calls; changed payload; process crash after provider acceptance; duplicate callback; reservation expiry; stalled outbox; refund failure; regional failover with missing acknowledged data.

**Defend:** why an outbox does not guarantee atomicity with a bank; why a saga compensation is not a database rollback; when a manual exception queue is necessary. Identify who owns reconciliation and customer communication.

**Role follow-up:** EM explains release sequencing and operational ownership. Staff explains atomic claims, isolation and callback races. Leadership explains loss tolerance, fraud and revenue risk, and dependency investment.

Sources: [Stripe idempotency](https://docs.stripe.com/api/idempotent_requests), [AWS outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html), [AWS saga](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html).

## 2. Booking exclusive inventory

**Problem:** reserve a unique room, appointment or seat without double-booking while clients disconnect and retry.

**Clarify:** discrete slots versus overlapping intervals? Hold versus committed booking? Who determines expiry? Cancellation rules? Do inventory and booking live in one database?

**Invariant:** conflicting committed bookings cannot coexist for the same resource and interval.

**API and data:** model inventory identity, time interval, reservation state, expiry and version. Use an exclusion or uniqueness constraint where the data model permits it, or another concurrency control mechanism whose isolation you can prove. Check authorization on both creation and cancellation.

**Baseline:** a transaction atomically verifies and allocates inventory. A hold is a state with defined expiry and a recovery path. A worker releasing expired holds must not release a subsequently confirmed booking. Use compare-and-set state transitions rather than an unconditional delete.

**Failure drills:** simultaneous allocation; confirmation races with expiry; server clock disagreement; a stale worker resumes; failover during acknowledgement; a customer retries cancellation.

**Defend:** why "check availability then insert" races; why a Redis lock alone is not the authoritative booking invariant; whether the system rejects writes during a partition.

**Role follow-up:** EM defines conflict-handling experience and support ownership. Staff explains database isolation and stale-owner rejection. Leadership chooses availability versus booking correctness explicitly.

Source: [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html).

## 3. Durable messaging and offline synchronization

**Problem:** support messages, reconnect, multiple devices, read state and authorization changes.

**Clarify:** direct or group messages? Ordering per conversation? Edit and delete semantics? End-to-end encryption? Membership history? Retention? Delivery versus read receipts?

**Invariant:** acknowledged accepted messages can be recovered within the agreed durability model; retries do not create duplicate messages; unauthorized members cannot read history outside their policy.

**API and data:** stable client message identity, conversation sequence or explicit ordering rule, accepted timestamp, membership version, per-device sync cursor and read watermark. Define message acceptance separately from recipient delivery.

**Baseline:** persist before acknowledgement. A gateway delivers online hints; clients fetch durable history after reconnect. Presence is ephemeral and approximate. Read watermarks should not regress when an old device reconnects. Design deletion propagation and cursor expiry.

**Failure drills:** gateway crash after acceptance; reconnect to a different gateway; duplicate send; missed realtime hint; group membership change; old cursor after retention expiry; hot group saturates one partition.

**Defend:** why WebSocket delivery is not durable storage; why client clock order is insufficient; how sequence allocation and partitioning interact.

**Role follow-up:** EM owns availability and abuse response. Staff traces ordering and replay. Leadership decides privacy and retention policy with appropriate stakeholders.

Source: [Kafka ordering and delivery boundaries](https://kafka.apache.org/41/design/design/).

## 4. Social feed and recommendations

**Problem:** deliver a personalized feed with stable navigation and bounded serving cost.

**Clarify:** freshness, ranking changes, following graph, celebrity fan-out, blocked content, ad insertion, and acceptable fallback behavior?

**Invariant:** access control and deletion rules must hold even when feed membership is cached or materialized.

**API and data:** source posts, audience rules, materialized candidates and versioned ranking state. Pagination needs a total order or a feed session; record how changing ranking affects already-issued cursors.

**Baseline:** compare fan-out-on-write, fan-out-on-read and hybrid approaches against the actual graph distribution. Cache candidate sets or results only within a defined authorization and freshness policy. Add retrieval and ranking only when the prompt needs them. Set a deadline and a permitted fallback for missing ranking dependencies.

**Failure drills:** popular account creates a burst; stale block list; deletion replay; ranking timeout; cache outage; a user scrolls while rankings change.

**Defend:** which data is authoritative, why partition skew matters, how fan-out cost is measured, and why a vector database is not automatically required.

**Role follow-up:** EM coordinates ranking and platform contracts. Staff details pagination and invalidation. Leadership ties serving cost and recommendation quality to a measured experiment.

Related client material: [social feed](social-feed.md), [video feed](video-feed-streaming.md).

## 5. Search and autocomplete

**Problem:** index authoritative records and serve permitted results while updates and deletions continue.

**Clarify:** text versus semantic search? Index freshness? Typo tolerance? Tenant filtering? Query rate and payload? Privacy and retention?

**Invariant:** derived state must not resurrect deleted records or expose unauthorized objects after replay.

**API and data:** query filters, stable result identity, document version, tombstone, index schema version and ingestion checkpoint. Define search freshness and document lookup semantics separately.

**Baseline:** database changes flow through CDC or an outbox to the index. Take a consistent snapshot and establish the stream boundary. Apply updates using version checks. Rebuild into a new index, compare, then switch the read alias.

**Failure drills:** replication slot retains WAL; index unavailable; older update follows deletion; poison record; connector restart; mapping migration; full reindex during live writes.

**Defend:** how snapshot and stream avoid gaps, how lag affects users, and how failed records are repaired without silently discarding them.

**Role follow-up:** EM assigns ingestion and query ownership. Staff explains versioning and checkpointing. Leadership chooses freshness and cost trade-offs.

Source: [Debezium PostgreSQL connector](https://debezium.io/documentation/reference/stable/connectors/postgresql.html).

## 6. Analytics and telemetry ingestion

**Problem:** accept events, retain them, compute aggregates and support replay and deletion.

**Clarify:** operational versus financial analytics? Event uniqueness? Offline delay? Consent? Schema evolution? Retention? Late-event handling? Required accuracy?

**Invariant:** aggregation and deduplication semantics are explicit, with deletion and authorization reaching derived datasets.

**API and data:** event identity, producer identity, event time, ingestion time, schema version, consent context and bounded payload. Specify which events may be dropped under pressure and which require a durable acknowledgement.

**Baseline:** durable ingestion log, schema validation, dead-letter recovery, stream or batch transformations, and serving stores chosen for access paths. Preserve raw data only within policy. Event-time windows require a declared lateness and correction strategy.

**Failure drills:** duplicate client batch; delayed offline events; schema incompatibility; partition skew; consumer lag; sink write succeeds but offset commit fails; replay doubles an aggregate; consent withdrawal.

**Defend:** approximate versus exact distinct counts, acknowledgement boundary, sampling bias, replay idempotency, and end-to-end freshness.

**Role follow-up:** EM owns data contracts and incident repair. Staff details windowing and sink semantics. Leadership defines which analytics are decision-worthy and worth retaining.

Sources: [Kafka design](https://kafka.apache.org/41/design/design/), [analytics client guide](user-analytics-event-pipeline.md).

## 7. Notification delivery

**Problem:** send permitted notifications across providers, time zones, retries and device churn.

**Clarify:** transactional versus marketing priority? Is timeliness or completeness dominant? User preferences? Expiry? Multiple devices? Sensitive payloads?

**Invariant:** notification intent and preference decisions are traceable; provider acceptance is not claimed as device delivery.

**API and data:** durable intent, recipient, channel, deduplication identity, expiry, priority, preference version, provider attempt and token registration identity. Schedule from actual user time-zone rules rather than fixed UTC offsets.

**Baseline:** durable queue, bounded worker concurrency, provider-specific retry classification, preference check near send time, quiet-hour scheduling and delivery telemetry where available. APNs 400 `BadDeviceToken` differs from 410 `Unregistered`. Cleanup must account for newer registrations.

**Failure drills:** provider throttling; accepted send followed by worker crash; stale token response; user disables marketing after scheduling; time-zone change; backlog extends beyond expiry.

**Defend:** why retries can duplicate external notifications, how collapse semantics differ from durable deduplication, and which messages can be discarded after expiry.

**Role follow-up:** EM coordinates preferences and provider operations. Staff models retry and token races. Leadership governs notification value, abuse and user trust.

Source: [Apple APNs responses](https://developer.apple.com/documentation/usernotifications/handling-notification-responses-from-apns).

## 8. Streaming platform and live-event control plane

**Problem:** serve authorized playback during a live event and recover from origin or control-plane failures.

**Clarify:** live versus VOD? Content rights and geography? Entitlement? DRM? DVR? Concurrent streams? Manifest freshness? Ad insertion? CDN contracts?

**Invariant:** playback authorization is enforced while manifest and segment delivery obey defined freshness and retention policies.

**API and data:** playback session, entitlement, signed content access, asset metadata, manifest identity, regional policy and quality telemetry. Distinguish the media data plane from metadata, entitlement and configuration control planes.

**Baseline:** object and segment delivery through appropriate caches; a control path for session authorization and playback metadata. Bound dependency timeouts and define permitted fallback. Avoid putting every segment request through a heavyweight personalization service.

**Failure drills:** popular event begins; origin unavailable; stale manifest; entitlement store failure; key-service timeout; CDN switching; telemetry unavailable; retry storm on client reconnect.

**Defend:** why concurrent viewers do not equal API QPS, where media cost is incurred, what cache keys include, and how you distinguish server health from playback success.

**Role follow-up:** EM explains rehearsal and incident ownership. Staff separates data-plane and control-plane failure handling. Leadership connects rights, customer experience and capacity spending.

Rahul evidence anchor: Sharechat streaming optimization and SonyLiv concurrency planning, with exact ownership established from [the resume plan](rahul-backend-interview-plan.md).

## 9. Multi-tenant CSAT and reporting platform

**Problem:** collect feedback, serve reporting and protect tenant and user data.

**Clarify:** internal roles or external tenants? Ingestion sources? PII? Report freshness? Export sizes? Deletion requirements? Administrative access?

**Invariant:** every read, write, export, cache and background job is authorized for the correct tenant and role.

**API and data:** feedback records, source identity, consent or retention policy, role bindings, report job, export object and audit trail. Make tenant context trusted server-side state, not a freely accepted client field.

**Baseline:** transactional ingestion and indexed queries. Queue expensive reports; expose job status and authorized download. Evaluate a separate analytical store only when measured query pressure warrants it. Encrypt and expire exports according to policy.

**Failure drills:** user guesses another report ID; shared-cache key lacks tenant; export worker runs with excessive privilege; report retry duplicates results; malformed input; deletion misses an export; long query blocks writes.

**Defend:** authorization through all alternate paths, operational versus analytical queries, report snapshot consistency and backup restoration.

**Role follow-up:** EM defines stakeholder outcomes and data ownership. Staff explains schema and query plans. Leadership chooses investment scope and privacy obligations.

Rahul evidence anchor: the actual SonyLiv CSAT platform. Reconstruct it before presenting this practice architecture as past work.

## 10. Distributed scheduler and work execution

**Problem:** schedule and execute jobs despite worker crashes, leadership changes and delayed clocks.

**Clarify:** one-time or recurring schedules? User time zones? Deadline? Duplicate side effects permitted? Cancellation? Retry and priority policy?

**Invariant:** an accepted job remains recoverable; duplicate attempts do not violate destination invariants.

**API and data:** job identity, schedule, execution state, attempt identity, lease expiry, cancellation version and durable outcome. Define calendar recurrence separately from elapsed intervals.

**Baseline:** durable job registry; atomic claim or queue; lease renewal; retry with bounded policy; destination idempotency or fencing where required. Store scheduling state independently from ephemeral worker memory.

**Failure drills:** worker pauses beyond lease; stale worker resumes; process crashes after side effect; schedule changes mid-flight; cancellation races with execution; retry backlog starves fresh jobs.

**Defend:** why a lease does not imply exactly-once execution, how stale owners are rejected and how terminal failed work is surfaced.

**Role follow-up:** EM owns service contracts and fairness. Staff details leasing and fencing. Leadership selects reliability versus operational complexity.

## 11. Regional failure and data recovery

**Problem:** keep a service recoverable through zone or regional loss without corrupting state.

**Clarify:** RPO, RTO, data residency, acceptable write unavailability, and whether dependencies also survive the failure?

**Invariant:** the stated durability and single-writer rules survive the failover process.

**API and data:** write ownership, replication acknowledgement, recovery checkpoints, backup location, routing and dependency map. Declare what happens to requests acknowledged just before failure.

**Baseline:** choose topology from the recovery objectives. Exercise restoration and dependency readiness. Fence old writers before accepting writes elsewhere. Restore with auditable verification and a failback plan.

**Failure drills:** replication lag at regional loss; old leader recovers; partial DNS propagation; empty caches in the survivor; backup is corrupt; identity or secrets service exists only in the failed region.

**Defend:** difference between replication and backup, acknowledged-write loss exposure, and why active-active needs a conflict or coordination model.

**Role follow-up:** EM coordinates recovery exercises. Staff details fencing and consistency. Leadership agrees business loss and recovery priorities.

Source: [PostgreSQL replication](https://www.postgresql.org/docs/current/warm-standby.html).

## 12. AI inference gateway and evaluation platform

**Problem:** serve model requests with bounded cost, fair admission and reproducible quality evaluation.

**Clarify:** model ownership versus external provider? Streaming? Tenant quotas? Context length? Tool execution? Sensitive inputs? Safety review? Evaluation criteria?

**Invariant:** request authorization and tool permissions hold across model versions; generated content cannot confer privileges to itself.

**API and data:** model/version, request identity, token accounting, cancellation, evaluation dataset version, deployment version and auditable tool actions. Distinguish time to first token from complete-response latency and throughput.

**Baseline:** validate and authorize, enforce budgets, queue only within deadlines, route to compatible serving capacity, stream with cancellation propagation, and record versioned outcomes. Separate model-quality evaluation from availability and latency monitoring.

**Failure drills:** provider throttles; long requests consume capacity; client disconnects; partial output; unsafe tool proposal; evaluation dataset leakage; new model improves speed but regresses task quality.

**Defend:** prefill versus decoding, batch throughput versus queue delay, cache privacy, tenant fairness, and tool-call idempotency. Quantify hardware or model behavior only from actual measurements or published evidence for that exact configuration.

**Role follow-up:** EM aligns researchers, platform and product. Staff details admission and cancellation. Leadership evaluates safety, quality, cost and operational readiness before launch.

This is infrastructure practice. It does not establish research engineering or model-training experience.

## Mock review protocol

For each case, have a reviewer introduce a race, a stalled dependency, and a changed business constraint. Record the unsupported claim or incorrect boundary, repair the design, then repeat that failure walkthrough.

A useful mock result is a concrete correction: which transaction races, which event can replay, which metric lacks a denominator, which authorization path is missing, or which recovery claim is unproven. Do not substitute a memorized component diagram for that analysis.
