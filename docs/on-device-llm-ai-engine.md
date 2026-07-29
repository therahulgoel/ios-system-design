# On-Device LLM & Mobile AI Assistant Engine

## Overview
With the advent of Apple Intelligence, Meta ExecuTorch, and Google Gemini Nano/AICore, mobile system design interviews for Staff, Principal, and AI/ML Mobile Engineers now frequently evaluate **On-Device LLM & Local AI Assistant Architecture**. This problem tests a candidate's ability to balance low-latency inference, extreme memory constraints (< 500MB RAM budget for models), battery/thermal throttling, local Vector DB indexing (On-Device RAG), streaming token UI generation, and seamless hybrid cloud fallbacks.

## Target Companies & Frequency
| Company | Why They Ask | Frequency |
| :--- | :--- | :--- |
| Apple | Core focus on Apple Intelligence, CoreML Neural Engine, and on-device privacy | ★★★★★ |
| Meta | Llama 3 / ExecuTorch mobile runtime deployment across WhatsApp, Instagram, Ray-Ban | ★★★★★ |
| Google | Gemini Nano, Android AICore, local embedding search in Pixel / Google Photos | ★★★★★ |
| Microsoft | Copilot mobile integration, ONNX Runtime Mobile, local context indexing | ★★★★☆ |
| Uber / Airbnb | Smart customer support assistants, local speech/text query parsing offline | ★★★★☆ |

---

## Scope Definition

### In Scope
- Quantized model loading (INT4 / FP16 CoreML / ExecuTorch / GGUF model formats).
- Strict memory management (< 500MB RAM budget for models, active weight unmapping under OS memory pressure).
- On-Device RAG pipeline (Local Vector Index using USearch/HNSW + SQLite VSS, local text embedding generation).
- Token Generation Streaming Architecture (`AsyncSequence` / SSE, KV-Cache sliding window management).
- Thermal, Battery & Hardware Throttling Guard (Metal Performance Shaders, Apple Neural Engine vs GPU vs CPU scheduling).
- Hybrid Inference Coordinator (Local execution first $\rightarrow$ fallback to Cloud LLM API when model capacity, battery, or complexity requires it).

### Out of Scope
- Full model training or fine-tuning pipelines (server-side GPUs).
- Quantization math algorithms (focus is on deploying & managing quantized weights on mobile).
- Custom hardware ASIC design.

---

## Requirements

### Functional Requirements
1. **Local Text & Speech Inference**: Generate answers to user prompts locally using an on-device 1B-3B parameter quantized LLM (e.g., Llama-3-8B-Instruct 4-bit, Phi-3-mini, or CoreML Apple Foundation Model).
2. **On-Device RAG Context Search**: Embed user personal data (notes, messages, app documents) locally and retrieve relevant context chunks using cosine similarity before prompt construction.
3. **Streaming Token Output**: Stream response tokens in real time to the UI with less than 100ms time-to-first-token (TTFT).
4. **Hybrid Cloud Router**: Automatically route complex prompts (> 2k token context or requiring heavy reasoning) to Cloud LLM API via secure SSE stream.
5. **Privacy Guard**: Sanitize and strip PII (Personally Identifiable Information) locally before sending any prompt to the cloud fallback.

### Non-Functional Requirements
| Requirement | Target | Source / Authoritative Benchmark |
| :--- | :--- | :--- |
| Model Memory Allocation | $\le 500\text{MB}$ RAM (INT4 3B model) | Apple WWDC 2024 Session 10159 / Meta ExecuTorch |
| Time to First Token (TTFT) | $< 100\text{ms}$ (Local NPU) | Apple Neural Engine / Snapdragon NPU Benchmark |
| Generation Speed | $\ge 25\text{ tokens/sec}$ | ExecuTorch 4-bit Llama-3 benchmark |
| Local Vector Search Latency | $< 15\text{ms}$ for $10,000$ vectors | USearch / HNSW C++ Benchmark on iOS |
| Thermal Throttling Action | Downscale / Fallback to Cloud @ `.serious` thermal state | iOS `ProcessInfo.thermalState` API |
| Battery Drain Protection | Pause background indexing when battery $< 20\%$ or Low Power Mode | `ProcessInfo.isLowPowerModeEnabled` |

---

## High-Level Architecture (HLD)

### Component Diagram

```ascii
+-----------------------------------------------------------------------------------+
|                                  iOS Client Application                           |
|                                                                                   |
|  +------------------+         +-----------------------+                           |
|  |   SwiftUI View   | <-----> |   Assistant ViewModel  |                           |
|  | (Token Streamer) |         | (State & Token Buffer)|                           |
|  +------------------+         +-----------+-----------+                           |
|                                           |                                       |
|                                           v                                       |
|                               +-----------------------+                           |
|                               |   Hybrid AI Router    |                           |
|                               +-----------+-----------+                           |
|                                           |                                       |
|                  +------------------------+------------------------+              |
|                  | (Local Eligible)                                | (Cloud Fallback)|
|                  v                                                 v              |
|  +-------------------------------+                 +---------------------------+  |
|  |     On-Device AI Engine       |                 |    Cloud API Gateway      |  |
|  |                               |                 | (gRPC / SSE TLS 1.3)     |  |
|  |  +-------------------------+  |                 +-------------+-------------+  |
|  |  | Local Vector Search (RAG)|  |                               |                |
|  |  | (SQLite VSS / USearch)  |  |                               v                |
|  |  +------------+------------+  |                 +---------------------------+  |
|  |               | Context       |                 |   Cloud LLM Cluster       |  |
|  |               v               |                 | (GPT-4o / Claude / Llama) |  |
|  |  +-------------------------+  |                 +---------------------------+  |
|  |  | CoreML / ExecuTorch     |  |                                                |
|  |  | Inference Runtime       |  |                                                |
|  |  | (ANE / MPS GPU / INT4)  |  |                                                |
|  |  +-------------------------+  |                                                |
|  +-------------------------------+                                                |
+-----------------------------------------------------------------------------------+
```

### Data Flow
1. **User Prompt Input**: User submits a query (e.g., *"Summarize my flight details from yesterday"*).
2. **Device State Check**: `HybridAIRouter` checks battery, `thermalState`, and model load state.
3. **Local Vector Search (RAG)**:
   - Query is embedded locally using a tiny model (e.g., MobileBERT / BGE-Micro $\sim 25\text{MB}$).
   - `VectorSearchEngine` queries SQLite VSS / USearch HNSW index for top-k relevant local chunks.
4. **Context Assembly & Tokenization**: Local context is inserted into prompt template.
5. **Inference Execution**:
   - If prompt context $\le 2048$ tokens and thermal state is `.nominal`, `LocalInferenceEngine` runs on Apple Neural Engine (ANE) via CoreML/ExecuTorch.
   - Tokens stream directly to `AssistantViewModel` via Swift `AsyncThrowingStream`.
   - If thermal state is `.serious` or prompt requires $> 2048$ tokens, request routes to Cloud API via SSE stream.

---

## Deep Dives

### Subsystem 1: Local Vector Database & On-Device RAG Engine

To enable privacy-preserving retrieval without cloud dependencies, document embeddings are indexed locally in SQLite using SQLite VSS or USearch (HNSW algorithm).

```
Document Text -> Chunking (512 tokens) -> MobileBERT Embedder -> 384-dim Vector -> USearch HNSW Index
```

#### SQLite Vector Index Schema (SQLite VSS)
```sql
-- SQLite VSS Vector Storage Schema
CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

-- Virtual Table for Vector Search (384 dimensions for MobileBERT/MiniLM)
CREATE VIRTUAL TABLE IF NOT EXISTS vss_document_embeddings USING vss0(
    embedding(384)
);
```

#### Swift Local RAG Pipeline Actor
```swift
import Foundation
import CoreML

public actor LocalRAGEngine {
    private let vectorIndex: VectorIndexManager
    private let embedder: LocalEmbedder
    
    public init(vectorIndex: VectorIndexManager, embedder: LocalEmbedder) {
        self.vectorIndex = vectorIndex
        self.embedder = embedder
    }
    
    /// Retrieves relevant context for a user prompt
    public func retrieveContext(for query: String, topK: Int = 3) async throws -> [String] {
        // 1. Generate query embedding (384 dimensions)
        let queryVector: [Float] = try await embedder.generateEmbedding(text: query)
        
        // 2. Search HNSW index in local vector DB
        let matchingIDs = try await vectorIndex.searchNearest(vector: queryVector, limit: topK)
        
        // 3. Fetch full text chunks from SQLite
        return try await vectorIndex.fetchChunkTexts(for: matchingIDs)
    }
}
```

---

### Subsystem 2: Quantized Model Loader & Memory Manager

An INT4 quantized 3-Billion parameter LLM consumes roughly $\sim 1.8\text{GB}$ of raw weight space. On iOS devices, an application allocating $> 1.5\text{GB}$ under memory pressure will suffer immediate Jetsam OOM termination.

#### Memory Optimization Strategy:
1. **Memory-Mapped Files (`mmap`)**: Model weights are mapped into virtual address space via `mmap` with `MAP_SHARED` so the OS can page out inactive weights dynamically.
2. **Weight Unmapping on Memory Warning**: Listen to `UIApplication.didReceiveMemoryWarningNotification` to clear the KV-cache and release state buffers instantly.

```swift
import UIKit
import CoreML

actor LocalModelManager {
    private var isLoaded = false
    private var modelRuntime: CoreMLModelRuntime?
    private let maxMemoryBudgetBytes: UInt64 = 500 * 1024 * 1024 // 500 MB limit
    
    init() {
        NotificationCenter.default.addObserver(
            forName: UIApplication.didReceiveMemoryWarningNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            Task {
                await self?.handleMemoryPressure()
            }
        }
    }
    
    func loadModelIfNecessary() async throws {
        guard !isLoaded else { return }
        
        let availableMemory = os_proc_available_memory()
        guard availableMemory > maxMemoryBudgetBytes else {
            throw ModelError.insufficientMemory(available: availableMemory)
        }
        
        // Memory-mapped loading via CoreML / ExecuTorch
        self.modelRuntime = try await CoreMLModelRuntime.loadModel(
            name: "Llama3-3B-Instruct-4bit",
            computeUnits: .all // Uses ANE (Neural Engine) + GPU
        )
        self.isLoaded = true
    }
    
    func handleMemoryPressure() {
        // Evict KV cache & unload weights under Jetsam warning
        modelRuntime?.clearKVCache()
        modelRuntime = nil
        isLoaded = false
        print("[AI Engine] Unloaded local model due to Memory Pressure warning")
    }
}

enum ModelError: Error {
    case insufficientMemory(available: UInt64)
}
```

---

### Subsystem 3: Real-Time Token Generation & Async Sequence Streaming

Token generation must be asynchronous and streamed back to the UI incrementally without blocking the `@MainActor`.

```swift
import Foundation

public struct GeneratedToken {
    public let text: String
    public let isFinal: Bool
    public let totalTokensSoFar: Int
}

public actor TokenStreamEngine {
    private let modelRuntime: CoreMLModelRuntime
    
    public init(modelRuntime: CoreMLModelRuntime) {
        self.modelRuntime = modelRuntime
    }
    
    /// Streams tokens asynchronously as they are generated by the Neural Engine
    public func generateStream(prompt: String) -> AsyncThrowingStream<GeneratedToken, Error> {
        return AsyncThrowingStream { continuation in
            Task {
                do {
                    var tokenCount = 0
                    try await modelRuntime.predict(prompt: prompt) { tokenText in
                        tokenCount += 1
                        continuation.yield(GeneratedToken(
                            text: tokenText,
                            isFinal: false,
                            totalTokensSoFar: tokenCount
                        ))
                    }
                    continuation.yield(GeneratedToken(text: "", isFinal: true, totalTokensSoFar: tokenCount))
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }
}
```

---

### Subsystem 4: Thermal, Battery & Hybrid Fallback Router

Running Neural Engine inference at max capacity causes rapid thermal buildup and battery drain. The system monitors iOS process state and dynamically shifts workload to Cloud LLM APIs.

```swift
import Foundation
import UIKit

public actor HybridAIRouter {
    private let localEngine: TokenStreamEngine
    private let cloudClient: CloudLLMAPIClient
    
    public init(localEngine: TokenStreamEngine, cloudClient: CloudLLMAPIClient) {
        self.localEngine = localEngine
        self.cloudClient = cloudClient
    }
    
    public func processPrompt(_ prompt: String, estimatedTokens: Int) -> AsyncThrowingStream<String, Error> {
        let thermalState = ProcessInfo.processInfo.thermalState
        let isLowPowerMode = ProcessInfo.processInfo.isLowPowerModeEnabled
        
        // Fallback to Cloud if thermal state is elevated, low battery mode is active, or context is too large
        let shouldExecuteOnCloud = thermalState == .serious || 
                                   thermalState == .critical || 
                                   isLowPowerMode || 
                                   estimatedTokens > 2048
        
        if shouldExecuteOnCloud {
            print("[Hybrid Router] Routing to Cloud API (Thermal: \(thermalState.rawValue), LowPower: \(isLowPowerMode))")
            return cloudClient.streamCloudInference(prompt: prompt)
        } else {
            print("[Hybrid Router] Executing on-device via Apple Neural Engine")
            return AsyncThrowingStream { continuation in
                Task {
                    do {
                        let stream = await localEngine.generateStream(prompt: prompt)
                        for try await token in stream {
                            continuation.yield(token.text)
                        }
                        continuation.finish()
                    } catch {
                        // Fallback to cloud on local inference error
                        for try await cloudToken in self.cloudClient.streamCloudInference(prompt: prompt) {
                            continuation.yield(cloudToken)
                        }
                        continuation.finish()
                    }
                }
            }
        }
    }
}
```

---

## Edge Cases & Failure Modes

1. **Jetsam Memory Termination (OOM)**:
   * *Mitigation*: Register for `UIApplication.didReceiveMemoryWarningNotification`. Purge KV cache immediately and release model pointers. Set hard limit of 500MB budget for active weights.
2. **Thermal Throttling Dropoff**:
   * *Mitigation*: Monitor `ProcessInfo.thermalStateDidChangeNotification`. Switch active generation to Cloud LLM mid-stream if thermal state transitions from `.nominal` $\rightarrow$ `.serious`.
3. **Infinite Generation Loop (Repetition Trap)**:
   * *Mitigation*: Implement frequency and presence penalty parameters in local logits processor. Set hard stop token limit at 1,024 tokens.
4. **Privileged PII Leakage in Cloud Fallback**:
   * *Mitigation*: Apply local regex & NER (Named Entity Recognition) scrubber (Apple `NaturalLanguage` framework) to strip email addresses, phone numbers, and SSNs before dispatching prompts to cloud APIs.

---

## FAANG-Style Mock Interview Q&A

### Q1: How do you fit a 3B parameter model onto an iPhone with 6GB RAM without crashing the app?
**Answer**: We use 4-bit INT4 quantization (reducing model footprint from 6GB in FP16 down to $\sim 1.5\text{GB}$). Furthermore, we memory-map weights using `mmap` so only the currently executed layers reside in active RAM. We enforce a 500MB max memory ceiling for model execution buffers, and under OS memory pressure (`didReceiveMemoryWarning`), we instantly flush the KV-cache and release model pointers.

### Q2: Why use local SQLite VSS / USearch instead of querying a Cloud Vector Database (Pinecone/Milvus)?
**Answer**: Local vector search guarantees 100% offline functionality, zero network latency ($< 15\text{ms}$ search time), and zero cloud data ingress costs. Crucially, personal user data (emails, notes, messages) never leaves the device, adhering to Apple Intelligence and GDPR privacy standards.

---

## Common Mistakes (❌ Wrong $\rightarrow$ ✅ Correct)

- ❌ **Wrong**: Loading full 16-bit unquantized model weights directly into `Data(contentsOf: url)` in RAM.  
  ✅ **Correct**: Use 4-bit quantized CoreML/ExecuTorch models backed by memory-mapped files (`mmap`).

- ❌ **Wrong**: Running model inference directly on the `@MainActor` thread.  
  ✅ **Correct**: Execute inference inside a background `actor` dispatching onto Apple Neural Engine / Metal Performance Shaders.

- ❌ **Wrong**: Ignoring device thermal state during long generation tasks.  
  ✅ **Correct**: Listen to `ProcessInfo.thermalState` and fallback to Cloud SSE APIs when thermal state reaches `.serious`.
