# Rahul Goel: Backend EM, Staff & Leadership Preparation Plan

Reviewed on 4 October 2026 against [Rahul's public resume](https://therahulgoel.github.io/Rahul_Goel_Resume.pdf). Resume statements below are candidate-reported claims, not independently audited employer metrics. Contact information is intentionally omitted.

## 1. Positioning supported by the resume

Your strongest current narrative is an engineering manager with client-platform depth and experience at the boundary of streaming, payments, reliability, and backend APIs. The resume also names an end-to-end internal CSAT platform. This provides a concrete backend discussion entry point, but the resume does not describe its server stack, workload, authorization model, or operational results.

Use the platform experience to establish judgment and leadership, then demonstrate backend correctness separately. Employer-wide usage is context; it is not proof that you owned every service supporting those users.

| Track | Evidence currently present | Evidence still needed |
| :--- | :--- | :--- |
| Platform / product backend EM | SonyLiv leadership of 15 engineers, roadmaps and hiring; streaming, payments and CSAT work | Backend decisions you personally owned, production incidents, database and deployment ownership, individual people examples |
| Staff backend IC | Architecture, performance, SDKs, analytics, mentorship | Server implementation, transaction and concurrency depth, storage and distributed operations, cross-team backend adoption |
| Senior EM / director | Cross-functional execution and platform leadership | Exact multi-team remit, manager development, hiring outcomes, budget authority, portfolio decisions and organizational change |
| AI infrastructure engineering / EM | AI-assisted workflows and internal analytics platform | Model-serving or data-platform ownership, evaluation and safety mechanisms, reproducible performance evidence |
| ML research-oriented roles | No research or model-training evidence in this resume | Relevant ML, mathematical, experimental and research evidence required by the actual role |

These are preparation gaps identified from the document, not conclusions about experience omitted from it. Do not treat titles or company levels as equivalent.

## 2. Evidence bank from your actual work

Prepare a diagram and a concise account for each project. Retrieve evidence you are authorized to use; anonymize private customer and employee information.

| Resume anchor | Candidate-reported evidence | Follow-ups to answer before using it |
| :--- | :--- | :--- |
| SonyLiv people leadership | Team of 15; hiring, career development, roadmap and cross-functional execution | Direct reports versus broader team? Which hiring decisions? Which coaching intervention? How did you resolve an execution conflict? |
| SonyLiv reliability | Crash-free sessions increased from 97.5% to 99.9% | Same denominator, cohorts and window? Which failures? What did instrumentation reveal? What portion of change can be attributed to each intervention? |
| SonyLiv CSAT platform | Portal, APIs, database and reporting delivered | Language, schema, tenant and role model, retention, query paths, deployment, backups, traffic and ownership? |
| SonyLiv AI workflows | Kiro, MCP and design-to-code workflows introduced across teams | How was benefit measured? What access controls, review gates and failure handling existed? What remained manual? |
| Sharechat / Moj streaming | Six engineers; 25% cost reduction, $1M+ annual savings; 99.8% playback success | Cost baseline and window? Actual versus annualized savings? Player versus CDN responsibilities? Definition and denominator of playback success? |
| Sharechat codec and quality work | 30% data reduction and 18% fps improvement | Which devices, networks, codec-compatible cohorts and experiment? How were regressions prevented? |
| Groupon analytics | 10M+ daily events; batching, retry and offline queueing | Client events emitted versus backend events accepted? Unique IDs, acknowledgement boundary, loss and replay behavior? |
| Paytm payments and SDUI | Payments SDK and server-driven UI; company context of 100M+ monthly transactions | What did you own? Which server contracts? What happened after an ambiguous payment timeout? How did schema compatibility work? |
| Myntra / Jabong sessions | Session management supporting 5M+ concurrent users during EORS | Definition of concurrent user? Which components and code did you own? Server authorization or client lifecycle? Evidence for the stated availability? |

For the SonyLiv crash-free claim, 97.5% to 99.9% is a 2.4 percentage-point improvement. The implied crash-session fraction changes from 2.5% to 0.1%, a 96% relative decrease if the measurements are comparable. This arithmetic is derived from your resume, not independent validation or proof of causation.

Do not add MAU across employers, convert MAU into peak QPS, describe platform-wide transactions as your SDK's measured throughput, or call crash-free sessions backend availability.

## 3. A truthful introductory narrative

A supported starting point:

> I lead Apps Platform engineering at SonyLiv, where my resume records responsibility for a team of 15 engineers and reliability improvement from 97.5% to 99.9% crash-free sessions. My background spans streaming performance, payment SDKs, analytics and platform architecture. I also delivered an internal CSAT platform covering the portal, APIs, database and reporting. I am targeting roles where that platform leadership and client-to-service understanding are relevant, and I can discuss my precise ownership and the evidence behind the results.

Adapt this to the actual job. For a backend-heavy interview, open the CSAT architecture and discuss real server decisions. For staff interviews, emphasize your implementation and influence. For broader leadership, supply real organizational examples beyond this introduction.

Do not claim ownership of Kafka clusters, payment ledgers, GPU serving, flight software, or management of managers unless you actually held it.

## 4. Resume corrections to prepare

Keep your original resume unchanged until the underlying evidence is established. The following edits are priorities for a future version:

1. **Separate context from ownership.** State employer or product scale explicitly as context, followed by the subsystem you owned.
2. **Clarify streaming infrastructure.** Identify client player, caching, backend, CDN or end-to-end remit. The existing wording permits several interpretations.
3. **Make the CSAT backend concrete.** Add the actual language, storage, authentication, deployment and customer outcome once verified. Avoid filling these from a preferred technology list.
4. **Qualify cost claims.** Identify cost category, baseline period, attributable change, and whether savings were observed or annualized.
5. **Define reliability measures.** Replace the aggregate "99.5%+ reliability" wording with specific, comparable service or client measures supported by data.
6. **Show management outcomes.** Include a real hiring, coaching, career-development or planning outcome if you can substantiate it. Team size alone does not show management effectiveness.
7. **Show backend depth selectively.** Include backend technologies only when you can explain actual implementation and operations. Coursework and lab work belong in their own category.

## 5. Company-specific preparation

Company process information was checked on 4 October 2026. Open positions and interview expectations change. Obtain the actual job description and recruiter guidance before tailoring your final practice.

### Amazon

The official [SDM preparation page](https://amazon.jobs/content/en/how-we-hire/sdm-interview-prep) includes system design, management, operational and behavioral competencies, and a writing assessment. Prepare a clear decision memo and real examples mapped to the [Leadership Principles](https://www.amazon.jobs/content/en/our-workplace/leadership-principles). Use streaming cost work for cost judgment and reliability work for operational depth only to the extent your actual actions support those competencies.

Practice: defend a durable checkout workflow, explain a customer-impacting incident, and show how you developed an engineer. These are repository practice prompts, not purported leaked Amazon questions.

### Google

Use [Google's hiring process](https://www.google.com/about/careers/applications/how-we-hire/) and the actual job specification. Do not assume a mobile EM title establishes a Google level. Prepare coding in the permitted language, backend design, and cross-team influence where the role requires them.

Practice: explain a migration with competing stakeholder goals, correctness under replication lag, and your personal technical contribution. The emphasis here is preparation advice, not a claim about Google's private scoring.

### Google DeepMind

The official [careers page](https://deepmind.google/careers/) distinguishes software engineering from research engineering and research science, and describes a role-specific interview process. Its [interview guide](https://storage.googleapis.com/deepmind-media/DeepMind.com/Assets/Docs/interviewing-at-google-deepmind.pdf) recommends concrete competency examples.

Your AI tooling work supports a developer-productivity story. It does not establish ML research or distributed-training expertise. Assess software/platform roles against the actual requirements. For infrastructure preparation, study inference admission control, model and dataset versioning, evaluation, reproducibility and safe rollout; build and measure a lab implementation before claiming proficiency.

### SpaceX / Starlink

Select a specific role from [SpaceX careers](https://www.spacex.com/careers/). Product/backend services, network infrastructure, embedded systems and flight software require different preparation. No exact SpaceX loop, current opening, eligibility determination, or level match is asserted here.

For the actual posting, verify location, work authorization, export-control conditions, security requirements, language, operating-systems depth and on-site expectations. For network/backend infrastructure practice, prepare telemetry ingestion, degraded connectivity, deployment failure and observability. For flight or embedded roles, this repository alone does not provide the required real-time and hardware depth.

## 6. Preparation sequence with observable exits

Advance when the output can withstand questioning. The sequence is a recommended curriculum, not a prediction of hiring readiness after a fixed duration.

| Stage | Work | Required output and exit condition |
| :--- | :--- | :--- |
| Evidence | Reconstruct streaming, reliability, payments, analytics and CSAT decisions | Every claim has a defined metric, ownership boundary and explainable mechanism; unknowns are identified |
| Backend fundamentals | Transactions, isolation, indexing, replication, protocol semantics, queue delivery | Explain concurrent writes, timeout ambiguity and replay without slogans |
| Correctness | Checkout, booking, messaging and outbox | Draw state transitions and defend every crash boundary |
| Scale and operations | Cache failure, hotspots, overload, CDC and regional recovery | Show measured-input capacity model, safe degradation and recovery |
| Implementation | Build a backend lab in a language appropriate to the target role | Working API, durable state, atomic idempotency, authorization and reproducible failure checks |
| Leadership | Coaching, hiring, prioritization, conflict, incident and strategy | Actual examples survive questions about personal actions, alternatives and evidence |
| Company adaptation | Read actual postings and recruiter packet | One evidence-to-requirement map per selected role |
| Mock loops | Design, coding, behavioral and writing as applicable | External feedback identifies no unresolved correctness or evidence gaps |

### Backend lab specification

Build a local order service using a transactional database. This is a future practice assignment, not an implementation delivered by this documentation change. Use your own authorized workload measurements; do not populate a claimed production dataset with synthetic records.

Required behavior: authenticated caller scope; request fingerprint; atomic idempotency claim; durable order state; outbox relay; replay-safe consumer; status lookup; migration; structured observability; recovery after restart. Start without a payment provider and do not claim real charges. If a provider sandbox is later used, label its results as sandbox evidence.

Check races and failure boundaries: concurrent same-key calls, conflicting payload, crash after commit, duplicate event, stale worker, interrupted backfill, slow consumer and tenant boundary violation. Record the actual outcomes, runtime, configuration and limitations. This supplies lab evidence rather than retroactive production experience.

### Coding and debugging

Your resume reports 350+ LeetCode problems in Swift. Confirm permitted languages and role expectations. Practice clean implementation, complexity explanation, edge cases, concurrency and debugging. For backend roles, additionally explain HTTP errors, database transactions, resource cleanup, timeouts and cancellation. Do not assume EM interviews never involve coding.

## 7. Readiness review

Before applying to each role, answer:

- Can I identify the role's actual mandatory requirements and which are evidenced?
- Can I defend one architecture from my own work through API, schema, failure and rollout details?
- Can I explain at least one failed decision and what I changed afterward?
- Can I discuss people leadership with real observations and interventions?
- Can I separate my work, my team's work and employer-wide scale?
- Can I solve the role's coding or debugging exercise under its stated constraints?
- Can I show backend lab results without presenting them as production experience?
- For director scope, can I establish multi-team leadership and portfolio accountability?

Use [the behavioral guide](behavioral-engineering-manager-staff-guide.md) and [casebook](backend-system-design-casebook.md) to close the specific gaps.
