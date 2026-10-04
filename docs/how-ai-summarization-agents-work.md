# How AI Summarization Systems Work

This guide separates model computation from application orchestration. A summarization call does not automatically constitute an autonomous agent. This is educational architecture, not a claimed production implementation.

## Model computation

A tokenizer converts text into model-specific token IDs. Segmentation, vocabulary, token counts and IDs depend on the exact tokenizer. Verify its actual output; no invented mapping or universal word-to-token ratio is used here.

Token IDs select learned representations. Those token representations are not interchangeable with document embeddings from a retrieval model. Contextual representations depend on model computation, and an embedding distance is not a factual-truth score.

Transformer attention combines queries, keys and values:

$$\operatorname{Attention}(Q,K,V)=\operatorname{softmax}(QK^T/\sqrt{d_k})V$$

The original [Transformer paper](https://arxiv.org/abs/1706.03762) describes scaled dot-product attention and masking. A causal decoder attends only to allowed preceding positions. Attention is computed over token representations, and an attention weight is not an authoritative explanation of a generated claim.

An autoregressive decoder predicts successive tokens conditioned on context. Decoding policy changes output distribution; a plausible sentence can still be unsupported. Lowering temperature does not provide a factual correctness guarantee.

KV-caching reuses keys and values from earlier positions during incremental generation. It increases memory demand with context and active sequences. It is an execution optimization within decoding, not a separate reasoning stage performed after a completed answer.

## Application architecture

```mermaid
flowchart LR
    I[Authorized source documents] --> N[Parse and normalize]
    N --> P[Prompt and context selection]
    P --> M[Model generation]
    M --> V[Validate output and source support]
    V --> O[Display or persist summary]
    V --> F[Bounded repair or explicit failure]
```

Define document access, maximum input, retained provenance, output schema, cancellation and timeout behavior. Treat document content as untrusted input, including instructions embedded in it. Model output cannot grant itself tool or data privileges.

For short documents, a direct call may be enough. For long documents, compare supported context with retrieval, chunking or hierarchical summarization. Chunk boundaries can lose references and global relationships. Hierarchical compression can omit minority evidence and compound errors; overlapping chunks do not eliminate these risks.

A chunked pipeline should retain source identity, location and version, intermediate results, completion state and retry identity. Resume failed work without duplicating external effects. Bound parallelism and preserve a useful end-to-end deadline.

## Source-grounded evaluation

Use actual authorized source documents and observed results. Assess:

- Whether each factual summary claim is supported by the source.
- Whether material findings, exceptions and disagreements are omitted.
- Whether quotations and references preserve their actual meaning.
- Whether numeric values, dates and entities are preserved correctly.
- Whether sensitive content is exposed beyond the intended audience.
- Whether the output meets schema and length requirements.

Keep source, model, prompt and evaluation versions traceable. A model judging another model can be useful evidence, but should be validated against an appropriate human-reviewed sample rather than treated as unquestionable truth.

## Backend and client responsibilities

**Backend:** authorize document access, persist job identity, enforce quotas, schedule work, handle retries, propagate deletion, store permitted artifacts and monitor provider failures.

**Client:** represent queued, streaming, completed, cancelled and failed states; prevent stale responses from overwriting new user work; provide provenance where available. Use SwiftUI and an ObservableObject ViewModel with injected services for app/UI implementations.

**EM:** establish ownership of quality, security, cost and availability. Define release criteria and incident response for a quality regression as well as an outage.

**Staff:** defend job state, replay behavior, cancellation, context selection and evaluation reproducibility through concrete implementation detail.

## Practice follow-ups

- What happens when generation finishes but persisting its result fails?
- How does document deletion reach intermediate summaries and caches?
- How do you prevent prompt content from authorizing a tool action?
- How do you compare models on the same versioned task set?
- How does the system expose an unsupported or incomplete summary?

Further reading: [ReAct](https://arxiv.org/abs/2210.03629) for an approach combining reasoning and actions; [backend inference exercise](backend-system-design-casebook.md#12-ai-inference-gateway-and-evaluation-platform); [local inference architecture](on-device-llm-ai-engine.md).
