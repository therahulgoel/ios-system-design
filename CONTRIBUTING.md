# Contributing

Keep the material technically defensible and useful for practice. Read [AGENTS.md](AGENTS.md), [REPO_SPEC.md](REPO_SPEC.md), and [the evidence standard](docs/evidence-and-sources.md).

## Evidence requirements

Use primary documentation, standards, papers or attributable engineering publications. Place the exact source beside the claim and retain the applicable version, units and context. Do not label a tuning choice an industry benchmark.

Do not add dummy production data, fabricated benchmark results, invented career stories, interview-frequency ratings or unverified private hiring rubrics. Keep practice prompts explicitly identified as authored exercises. Describe missing inputs rather than inventing workload or staffing numbers.

Resume claims remain candidate-reported until the measurement method and personal ownership are established. Never convert product-wide usage into an individual's service throughput.

## Architecture and examples

Follow MVVM for app/UI examples as specified in [REPO_SPEC.md](REPO_SPEC.md). Backend design is governed by explicit APIs, data models, invariants and failure semantics; MVVM does not govern server architecture.

Identify incomplete snippets as sketches. To claim runnable code, provide a buildable target, actual dependencies, platform/toolchain versions and relevant execution checks. Never claim a code snippet alone is production-certified.

For each design, include requirements, authoritative state, invariant, API semantics, concurrency, retry and replay behavior, overload, recovery, authorization, migration and observability. Add the leadership lens where relevant.

Use standard ASCII hyphens. Use clear Markdown links and fenced blocks. Mermaid diagrams should show trust, persistence and acknowledgement boundaries where useful.

## Review workflow

1. Make the change in a focused branch.
2. Cite added or changed factual claims and explain measurement limitations.
3. Run `python3 scripts/check_docs.py` and relevant implementation checks when there is executable code.
4. Review diagrams and documentation for consistency and scope.
5. Open a pull request describing the concrete improvement and actual validation.

No review turnaround or hiring outcome is guaranteed. Share public preparation guidance without disclosing confidential interview or employer information.
