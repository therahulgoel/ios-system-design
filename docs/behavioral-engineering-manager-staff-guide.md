# Engineering Leadership and Behavioral Interview Guide

Use real career evidence. This guide supplies rehearsal questions and an evaluation method; it does not attribute them to private company interviews or supply invented first-person stories. For Rahul-specific anchors, see [the evidence plan](rahul-backend-interview-plan.md).

## 1. Build a defensible story

Use Situation, Task, Action and Result, then add reflection. State context briefly, your responsibility precisely, the decision and alternatives, your personal actions, the observed outcome, and what you learned.

Distinguish "I" for your decisions from "we" for shared delivery. Give credit clearly. Quantification helps only when the metric, denominator, time window and attribution can be explained. A qualitative result with documented evidence is preferable to an invented percentage.

For each story, retain a private evidence note: approximate date, ownership, stakeholders, decision artifact, measurement method, counterfactual, downside and unresolved questions. Use only information you are authorized to discuss.

## 2. Story bank by competency

These are practice prompts authored for this repository, not purported leaked interview questions.

| Competency | Practice prompt | Follow-up that tests depth |
| :--- | :--- | :--- |
| Ownership | Describe a customer problem that crossed your formal scope | Which action was yours, and where did another team remain accountable? |
| Technical judgment | Describe a consequential architecture decision | Which alternative did you reject and what evidence would change your mind? |
| Incident leadership | Describe a production incident you helped resolve | What was known at the time, what mitigation was safe, and how was recovery verified? |
| Cost judgment | Describe a cost reduction with acceptable quality | Which cost category changed, how was it measured, and what reliability risk remained? |
| People development | Describe someone you coached toward independent ownership | What was the diagnosed gap, intervention and observed progress? |
| Performance management | Describe difficult feedback and a fair follow-through | Were expectations clear, support appropriate, and decisions consistent with policy? |
| Hiring | Describe a hiring or team-composition decision | What capability was missing and how did you evaluate it? |
| Conflict | Describe a disagreement with a technical or product partner | How did you test competing claims and execute after the decision? |
| Failure | Describe a decision that failed | What did you personally get wrong and what mechanism changed afterward? |
| Strategy | Describe a bet made under uncertainty | Which options, milestones, exit criteria and opportunity costs did you consider? |
| Influence | Describe adoption across teams you did not manage | Why did others adopt it and what support did it require? |
| Organizational leadership | Describe a resource or portfolio trade-off | What did you stop, who owned the decision, and how did business outcomes change? |

If a people or organizational example is absent, mark the gap. Do not transform an SDK implementation into a manager-development story.

## 3. Role-specific depth

**EM / SDM:** prepare actual hiring, feedback, coaching, delivery and incident examples. Describe the mechanisms you established and their outcomes, while retaining enough architecture detail to defend technical choices.

**Staff / principal:** prepare ambiguous technical work, implementation depth, migration and adoption. Explain how you influenced teams, developed other engineers, and handled decisions when you lacked reporting authority.

**Director / leadership:** establish multi-team remit, portfolio allocation, succession and leadership development. Explain how the organization functioned without requiring you to make every decision. Team size and title alone do not establish this scope.

## 4. Rahul's first stories to reconstruct

| Resume anchor | Supported starting point | Details still to recover |
| :--- | :--- | :--- |
| SonyLiv crash-free improvement | A candidate-reported reliability outcome | Failure diagnosis, your decisions, rollout, cohort comparison and sustained result |
| Sharechat streaming costs | A candidate-reported cost and playback outcome | Baseline billing, ownership, trade-offs, experiment and actual versus annualized savings |
| SonyLiv team leadership | Hiring, development and roadmap responsibilities are listed | A specific coaching, hiring and prioritization example with outcomes |
| Groupon event analytics | Batching, retries, offline queueing and event volume are listed | Acceptance boundary, loss and replay behavior, client versus server scope |
| Paytm SDK and SDUI | Reusable payments and configuration work are listed | Ambiguous timeout, compatibility decisions, adoption and rejected alternatives |
| SonyLiv CSAT platform | Portal, APIs, database and reporting are listed | Backend design, stakeholder decision, permissions and customer benefit |
| SonyLiv AI workflows | Cross-team tooling adoption is listed | Evaluation, quality safeguards, data access and observed developer outcomes |

The resume does not document an outage, a failed strategic bet, a performance-management case, or a manager-development outcome. Retrieve real examples from your career if they exist.

## 5. Drill through five layers

1. **Context:** what was happening, what was at risk, and what was your authority?
2. **Decision:** what options existed and why did you choose this one?
3. **Execution:** what did you personally do, and how did others contribute?
4. **Evidence:** how was impact measured and what other causes could explain it?
5. **Reflection:** what failed, what would you change, and what durable mechanism remained?

Practice concise opening answers, then expand only where the interviewer probes. Do not memorize scripts that cannot adapt to a changed question.

## 6. Difficult people conversations

Describe observed behavior and role expectations rather than labeling a person. Check for unclear goals, workload, skill gaps, missing support and relevant accommodations. Give specific feedback, agree observable goals, and follow the applicable company and HR process.

Preserve confidentiality. Explain the decision and your own conduct without exposing personal circumstances. Do not claim a universal performance-improvement policy, forced exit timeline, or company-wide employment rule from a culture slogan.

## 7. Company adaptation with official sources

Amazon's [SDM guidance](https://amazon.jobs/content/en/how-we-hire/sdm-interview-prep) describes technical and management preparation. Map real examples to its published [Leadership Principles](https://www.amazon.jobs/content/en/our-workplace/leadership-principles), including people development and customer outcomes. Do not reduce preparation to a few slogans.

Use [Google's hiring information](https://www.google.com/about/careers/applications/how-we-hire/) and recruiter-specific guidance. The rubric here is a rehearsal tool and does not claim to reproduce Google's hiring criteria.

Google DeepMind's [official interview guide](https://storage.googleapis.com/deepmind-media/DeepMind.com/Assets/Docs/interviewing-at-google-deepmind.pdf) recommends concrete competency examples and role-specific preparation. Prepare evidence of collaboration and rigorous evaluation relevant to the actual role.

For SpaceX, use the selected posting on [its careers site](https://www.spacex.com/careers/) and recruiter instructions. No private interview process or culture-based hiring shortcut is asserted here.

## 8. Writing and executive communication

Prepare a decision memo from an actual project:

- Customer problem and evidence.
- Decision required and accountable owner.
- Options considered, including keeping the current system.
- Technical risks, cost, dependencies and organizational capacity.
- Chosen direction, sequencing, success measures and stop criteria.
- Rollout, recovery, and open questions.

For Rahul, streaming cost optimization or the CSAT platform are supported project anchors. Use real facts and identify missing measurements. Do not turn inferred savings into observed business results.

## 9. Practice assessment

Record each dimension as missing, partially supported, or defended under follow-up. This is not a company hiring scorecard.

| Dimension | Evidence to look for |
| :--- | :--- |
| Ownership | Clear personal responsibility and accurate attribution |
| Judgment | Alternatives, constraints, decision and downside |
| Depth | Concrete technical or management mechanism |
| Impact | Defined outcome with a credible measurement method |
| Collaboration | Fair representation of disagreement and others' contribution |
| Learning | A mistake or limitation followed by an observable change |
| Scope | Evidence matches the role being sought |

A successful rehearsal reveals both the strongest evidence and remaining gaps. Repair the gap with actual experience, documentation or relevant practice; never invent a story to complete the matrix.

## Worked preparation: turn a project into a defensible answer

The earlier version contained long first-person stories with invented team sizes and outcomes. The useful part was their depth of probing. The method below restores that depth using the actual SonyLiv CSAT project named in Rahul's resume. It does not fill in missing career facts.

### Technical ownership: CSAT platform

**Question:** "Tell me about a system you designed or drove end to end."

Open with the project's user problem and your actual remit. Then draw the implemented feedback-to-report path from memory. Name which APIs, persistence, queries and delivery decisions you personally owned, and where another person made the decision. Reconstruct those details before claiming server-side expertise.

| Probe | What to explain in the answer | Evidence to recover |
| :--- | :--- | :--- |
| Why was the system needed? | The feedback/reporting problem and who used its output | Original requirement or stakeholder request |
| Why that data model? | Main entities, ingestion identity, report filters and access boundaries | Schema/API/design artifacts you are allowed to discuss |
| What was hard? | One actual race, slow query, security boundary or delivery constraint | The actual diagnosis and alternatives considered |
| What did you do? | A sequence of personal decisions and execution, giving others credit | Reviews, implementation ownership or decision record |
| How did it help? | Observed stakeholder/customer outcome and measurement method | Real usage, feedback or operational evidence |
| What would you change? | A real limitation and a justified next decision | An incident, unresolved risk or measured bottleneck |

**Weak:** "I built a scalable platform and improved customer experience."

**Stronger approach:** name the implemented request path, the actual constraint that determined your decision, the rejected option and the observed result. You do not need a dramatic metric to explain a consequential decision. If a field or outcome cannot be recalled, recover it rather than substituting a practice architecture.

### Cost judgment: streaming optimization

Use the Sharechat streaming work as a starting point. Separate encoding/packaging, origin requests, CDN delivery, wasted prefetch and client playback behavior. Those cost categories have different levers. Recover which category actually changed in your project.

The answer needs a causal chain: the observed source of waste, your intervention, its effect on the relevant bill or utilization measure, and the playback guardrail. Compare equivalent cohorts/windows and explain any traffic or pricing change. Annualized savings are an estimate; actual billed reduction is an observation. State which one the resume result represents.

**Probe:** "Could the cost fall simply because fewer people watched?" Explain the actual normalization and comparison used. **Probe:** "What downside did you accept?" Describe the real effect on quality, startup, bandwidth, operational effort or flexibility, rather than pretending the optimization was free.

### Developing an engineer: the management mechanism

Choose a real person and preserve confidentiality. Describe the observed capability gap, not a personality label. Distinguish insufficient skill from unclear remit, excessive load or missing support. Agree a goal visible in ordinary work, then choose a scoped responsibility that develops that capability.

Explain your intervention: how you reviewed reasoning, supplied feedback, arranged support and gradually reduced dependence on you. Describe what happened when progress or delivery slipped. The result must be the actual change in independent work or scope, not an assumed promotion.

| Follow-up | Depth expected |
| :--- | :--- |
| Why that assignment? | Connection between the diagnosed gap and the responsibility |
| Did you take over? | What remained the engineer's decision, and when escalation was necessary |
| How did you protect delivery? | Scope, support, checkpoints and explicit risk ownership |
| How did you know it worked? | Observed independent behavior and stakeholder evidence |
| What if it did not work? | Changed support/expectations and applicable performance process |

This restores the teaching from the old coaching story without inventing an employee, a timeline or a promotion.

### Disagreement: show the competing reasoning

Start with the actual decision, options and decision authority. Give the partner's strongest reason, not a caricature. Explain which evidence discriminated between options, how you gathered it and what trade-off remained uncertain. If the decision went against your recommendation, describe how you executed it and monitored the risk you raised.

The follow-up is often: "What would change your mind?" Name an observable condition, such as an access path that no longer meets requirements, rather than restating your preference. For staff, show adoption without reporting authority. For EM, show how team expectations and delivery changed after the decision.

### Failure and stopping work

A failure story needs a wrong decision or assumption you actually made. Explain what you knew at the time, why the option looked reasonable, what evidence disproved it, and how you repaired the customer/team consequence. The durable lesson is a changed review, rollout or ownership mechanism, not simply "we communicated better."

For a project stop decision, separate sunk effort from future value. Compare remaining investment, recoverable assets, future operating burden and alternatives. Explain who made the stop decision and how you supported the team afterward. Do not recycle a fictional cache project into your career history.

### Rehearse both the opening and the probe

Prepare a short opening containing context, your remit, decision, action and observed result. Then practice one branch at a time: technical mechanism, rejected option, conflicting stakeholder, evidence and reflection. The opening earns the follow-up; the detailed branch establishes that the story is yours.
