# Backend Interview Track: Fundamentals to Complete App Designs

A progressive study path for senior backend, staff and EM / SDM interviews. Focus on understanding, diagrams, spoken answers and follow-up reasoning. This track adds no implementation assignment. It cannot cover every specialty; use the actual role description to identify additional depth.

Start with the first stage you cannot explain confidently. Advance by defending the exit question, not by marking a page as read. Proposed answers below are rehearsal material, not claimed production experience. Use measured or interviewer-provided inputs instead of inventing traffic or outcomes.

## The full path

| Stage | Understand | Demonstrate before moving on |
| :--- | :--- | :--- |
| 1 | Requests, networks and server execution | Trace a request and explain a timeout |
| 2 | APIs, identity and authorization | Define an accepted operation and secure resource access |
| 3 | Data models, indexes and transactions | Enforce an invariant under concurrent requests |
| 4 | Caches and replication | Explain stale state and failed dependencies |
| 5 | Queues, workers and event streams | Explain acknowledgement, replay and ordering |
| 6 | Distributed correctness | Defend consistency, leases and failover |
| 7 | Capacity, latency and overload | Derive demand and protect useful work |
| 8 | Operations and change | Detect, mitigate, migrate and recover |
| 9 | Complete app designs | Join the previous stages into one defensible system |
| 10 | Seniority and leadership | Add implementation, influence or management depth |

Primary reading for technical behavior is collected at the end. The explanations here are a learning sequence, not a company's hiring rubric.

## 1. Start with one request

**Client:** the caller initiating an operation. **Server:** the process handling it. **DNS:** maps names to records used to find services. **TLS:** protects transport and authenticates the peer under its trust model. **HTTP:** defines request/response semantics. **Load balancer:** distributes traffic across eligible destinations; its behavior depends on configuration.

Trace name resolution, connection establishment, TLS, ingress, authorization, application work, database access and response. Connections may be reused, and a proxy can terminate TLS before a separate internal connection. Explain where measurement starts and ends.

A process holds state and resources. Threads or asynchronous tasks allow overlapping work, but blocked downstream operations still consume bounded resources. Concurrency is overlapping work; parallelism is simultaneous execution. More workers cannot remove a saturated database or CPU bottleneck.

**Practice question:** the app receives no response. Did the server perform the action?

> I cannot infer the business outcome from the client timeout. I would locate the request identity and the operation's durable state. The response may have been lost after commit, so retry safety depends on the operation contract.

**Exit:** draw the request path and identify failures before receipt, during processing and after commit. Distinguish transport success, HTTP status and business success.

## 2. APIs, identity and security

A useful API defines actors, resources, methods, validation, authorization, success/error semantics, pagination, compatibility and retry behavior. REST, GraphQL and gRPC are choices with different contracts and tooling; none provides business correctness by itself.

Authentication establishes identity. Authorization decides whether that identity may perform the action on this resource. Encryption does not replace either. Tenant identity supplied by the client must be verified against trusted context.

Idempotency means repeated application of an operation has the intended repeat-safe effect within its contract. For a business API, define identity scope, request fingerprint, concurrent execution, durable result and retention. A randomly generated key has no effect unless the server enforces it.

**Practice question:** how do you make a retried checkout safe?

> I would reuse the same operation identity and atomically bind it to the caller and request. A repeated request observes the durable operation state; a different payload conflicts. External payment outcome still needs provider cooperation and reconciliation.

**Exit:** explain an asynchronous accepted response, status lookup, duplicate request, unauthorized object lookup and schema change for old clients.

Read [the answer playbook](interview-answer-playbook.md#2-worked-design-response-payment-timeout) and [identity guidance](backend-engineering-manager-guide.md#9-security-and-multi-tenancy).

## 3. Databases: access paths before product names

A schema represents entities, relationships and constraints. A primary key identifies a row; a uniqueness constraint enforces uniqueness in its declared scope. An index supports particular access paths, with storage and write costs. An execution plan reveals how a query runs.

A transaction groups database operations into a commit/rollback boundary. Isolation determines what concurrent transactions can observe and which anomalies are possible. Durability depends on the actual persistence and acknowledgement configuration. ACID is not an automatic guarantee across independent services and external providers.

Explain lost update, write skew, lock contention, deadlock and retry. Optimistic concurrency checks a version; pessimistic coordination locks appropriate state. The chosen mechanism must cover every writer.

**Practice question:** two customers try to book the same resource.

> Checking availability before inserting is insufficient because both callers may observe it as free. I would enforce the allocation invariant through a suitable constraint or transaction and define the losing request's conflict response. The design depends on discrete slots versus overlapping intervals.

**Exit:** name the invariant, index, constraint, transaction and retry behavior. Explain why an external side effect cannot be rolled back by rolling back the local transaction.

Practice [booking](backend-system-design-casebook.md#2-booking-exclusive-inventory) and [multi-tenant reporting](backend-system-design-casebook.md#9-multi-tenant-csat-and-reporting-platform).

## 4. Caching, replicas and stale observations

A cache holds derived or reusable state to reduce work. A replica maintains a copy under its replication protocol. Neither necessarily provides the newest acknowledged state.

Cache-aside reads the cache, fills on a miss and needs an update/invalidation policy. Explain a stale fill racing with a write, a hot key expiring, negative caching after object creation, and loss of cache capacity. TTL alone does not coordinate concurrent writers.

Read-your-writes is a session guarantee, not simply "use replicas." Route to authoritative state or use a freshness mechanism the storage system can actually enforce. A fixed wait or pinning duration does not prove that lag has ended.

**Practice question:** the cache is unavailable.

> I would protect the database with bounded concurrency and an explicit degradation policy. For eligible data I may serve a permitted stale value; for authoritative payment or access decisions I need the defined correctness policy. Falling through every request to storage can turn a cache outage into a database outage.

**Exit:** distinguish freshness, availability and latency; explain a fill race and one replica-lag failure.

## 5. Queues, workers and event streams

A durable queue or log separates acceptance from processing. A worker claims work and produces an effect. An acknowledgement or offset identifies progress under the chosen protocol. Backpressure limits producers or consumers when capacity is insufficient.

At-least-once delivery permits duplicates. At-most-once behavior can lose work. Exactly-once claims need an explicit boundary and participating components. Kafka ordering is per partition; increasing consumers does not parallelize an ordered partition without changing the processing model.

The outbox commits business state and an event record locally; publication can replay. A dead-letter path requires diagnosis and repair, not silent abandonment. Event-time processing must account for delayed records and corrections.

**Practice question:** the worker commits its effect and crashes before acknowledgement.

> The work can replay. I would make the effect and deduplication atomic where possible, or use the destination's operation identity and reconciliation contract. A broker alone cannot make an arbitrary external action repeat-safe.

**Exit:** explain crash before commit, crash after effect, poison work, lag, partition skew and bounded recovery.

Practice [analytics](backend-system-design-casebook.md#6-analytics-and-telemetry-ingestion), [notifications](backend-system-design-casebook.md#7-notification-delivery) and [scheduling](backend-system-design-casebook.md#10-distributed-scheduler-and-work-execution).

## 6. Distributed correctness

Linearizability respects real-time ordering of operations. Serializability gives a transaction outcome equivalent to a serial execution. Eventual convergence requires an actual conflict and propagation mechanism. Do not confuse these guarantees.

A network partition prevents communication. Keeping strong correctness can require refusing operations rather than accepting conflicting writes. A consensus protocol coordinates agreement under a stated failure model; adding a replica count is not a substitute for understanding that protocol.

A lease permits ownership for a period but a paused worker can resume after expiry. Fencing requires the protected resource to reject stale owners. Sharding changes routing, locality and transaction boundaries; resharding needs a migration protocol.

A saga coordinates local transactions and compensating business operations. Intermediate state and failed compensation must be handled. Refunds and cancellation are new effects, not erasure of history.

**Practice question:** the old regional writer comes back after failover.

> I would ensure it cannot resume authoritative writes before traffic is accepted in the replacement region. Routing changes alone do not fence it. I would also state which acknowledged writes survived under the replication policy and how recovery is verified.

**Exit:** explain split brain, stale ownership, replication loss exposure, compensation and RPO/RTO.

Use [the fundamentals section](backend-engineering-manager-guide.md#4-distributed-systems-fundamentals-to-explain-without-slogans) and [regional recovery](backend-system-design-casebook.md#11-regional-failure-and-data-recovery).

## 7. Capacity, latency and overload

Separate throughput, concurrency, latency and backlog. State units and use a consistent measurement boundary.

- Request rate = requests in an observation window divided by its duration.
- In a stable system, mean in-flight work relates to arrival rate multiplied by mean time in the system.
- Queue drain time requires processing rate greater than continuing incoming rate.
- Storage depends on measured record size, retention, indexes, replication and backups.
- Fleet sizing needs safe measured capacity and the required capacity after failures.

Do not invent a peak multiplier, container throughput or universal price. Do not add component p99 values as though they produce the end-to-end p99. Fan-out and retries can amplify demand and tail latency.

**Practice question:** traffic grows and requests queue up.

> I would find the saturated resource and bound admission and queueing within useful deadlines. I would prioritize critical operations, limit retries and degrade eligible work. Scaling application workers helps only if the downstream bottleneck can support the additional load.

**Exit:** explain deadlines, jitter, retry budgets, bulkheads, load shedding, cache warming and hot partitions.

## 8. Operate and change the system

Define user outcomes, eligible requests and observation windows before setting SLOs. Track latency distributions, errors, saturation, queue age, freshness and unresolved business operations. Logs, metrics and traces have different roles; correlate with safe identities and control sensitive data and metric cardinality.

For incidents, choose a safe mitigation, coordinate responsibilities and verify recovery. A rollback may be incompatible with changed data. Expand-contract helps compatibility, but DDL can still lock. Backfills need checkpoints, throttling and concurrent-write reconciliation.

Replication is not an independent backup. Exercise restoration and inspect dependency readiness. Separate availability recovery from repairing inconsistent business state.

**Practice question:** how do you change a large table while the service runs?

> I would review the actual DDL lock behavior, bound lock waits, introduce compatible structures, backfill resumably and compare representations. I would switch reads only after validation and retire old paths after dependencies and recovery needs are resolved.

**Exit:** explain an SLI denominator, alert response, migration race, canary validation and restored-data verification.

## 9. From fundamentals to complete apps

These are familiar product-domain exercises, not verified internal architectures. Build one end-to-end answer at a time.

| App type | Put these concepts together | Required failure walkthrough |
| :--- | :--- | :--- |
| Commerce / checkout | APIs, inventory transaction, payment attempt, outbox, status | Provider accepts while the response is lost |
| Booking | Resource/time model, allocation invariant, hold expiry | Confirmation races with expiration |
| Chat | Durable acceptance, conversation ordering, realtime hints, sync | Gateway dies after accepting a message |
| Feed | Candidate generation, access rules, caching, pagination | Deletion or blocked content remains in derived state |
| Search | Snapshot, CDC, index versions, query serving | Old replay tries to resurrect a deletion |
| Analytics | Durable ingestion, schema, deduplication, windows, storage | A sink succeeds before its offset is committed |
| Notifications | Intent, preferences, expiry, provider worker, token version | Old provider feedback arrives after registration changes |
| Streaming | Entitlement, session, licensing, media/CDN, ad decisions | Paid playback fails while segments remain reachable |
| Reporting platform | Tenant isolation, queries, export jobs, retention | Export authorization bypasses the UI checks |
| AI gateway | Authorization, admission, cancellation, versioned evaluation | Client disconnects but expensive work continues |

Use [all twelve backend cases](backend-system-design-casebook.md) and [streaming failure walkthroughs](streaming-business-and-architecture.md). Each answer should identify the source of truth, acceptance boundary, invariant, failure policy and customer consequence.

### Assemble an answer for a streaming app

Start with catalog discovery and the user's access policy. Trace session creation, entitlement decision, manifest access, DRM license acquisition and media delivery. Add renewal, revocation and advertising only with explicit policies. Keep media delivery separate from control dependencies.

Then introduce failures: stale entitlement, licensing outage, ad-decision timeout, stale live manifest and overloaded backup CDN. Explain persisted state, bounded retries, permitted continuation and the condition requiring playback to stop. Finally discuss rehearsals, metrics, domain ownership and cost.

That is a complete app conversation built from basics; a diagram containing many products is not sufficient.

## 10. Adapt the same design to your role

| Role | Add to the technical answer |
| :--- | :--- |
| Senior backend | Concrete access paths, request lifecycle, error handling and operational reasoning |
| Staff / principal | Protocol depth, failure boundaries, migrations and cross-team adoption |
| EM / SDM | Ownership, people development, staffing, delivery and incident mechanisms |
| Broader leadership | Portfolio choices, dependency investment, business risk and leadership development |

For Rahul, use [the resume evidence plan](rahul-backend-interview-plan.md). Streaming and CSAT are actual project anchors; reconstruct personal server-side ownership before presenting a practice design as work you delivered.

## Reading map and readiness

| Need | Primary source |
| :--- | :--- |
| Request and method semantics | [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html) |
| Identity security | [OAuth security BCP](https://www.rfc-editor.org/rfc/rfc9700) |
| Isolation and concurrency | [PostgreSQL isolation](https://www.postgresql.org/docs/current/transaction-iso.html) |
| Replication and failover | [PostgreSQL replication](https://www.postgresql.org/docs/current/warm-standby.html) |
| Ordering and replay | [Kafka design](https://kafka.apache.org/41/design/design/) |
| Atomic local event publication | [AWS outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) |
| Distributed compensation | [AWS saga orchestration](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-orchestration.html) |
| Overload and operational objectives | [Google SRE overload](https://sre.google/sre-book/handling-overload/), [SLOs](https://sre.google/sre-book/service-level-objectives/) |
| Safe DDL | [PostgreSQL ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html) |

You are ready to advance when you can explain the concept simply, apply it to an app, defend a changed constraint and walk through a failure. Use [the answer playbook](interview-answer-playbook.md) to practice aloud and [the master guide](backend-engineering-manager-guide.md) to deepen a weak topic. Coding requirements vary by role; this interview track emphasizes reasoning and explanation rather than adding code.
