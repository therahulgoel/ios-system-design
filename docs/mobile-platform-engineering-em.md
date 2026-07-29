# Mobile Platform Engineering, Release & Engineering Management Guide

## Overview
In Staff, Principal, and Engineering Manager (EM) interview rounds, system design questions often transition beyond purely technical component diagrams into **Mobile Engineering Leadership & Platform Governance**. Candidates are asked how to manage monorepos for 100+ iOS engineers, orchestrate zero-downtime mobile release trains, handle Sev-1 mobile incidents (App Store emergency rollbacks), establish build time budgets (< 5 mins), and enforce architectural consistency across dozens of product teams.

## Target Companies & Frequency
| Company | Why They Ask | Frequency |
| :--- | :--- | :--- |
| Uber | 200+ iOS engineers working in a single monorepo (Needle DI, SPM/Buck build system) | ★★★★★ |
| Meta | Massive mobile codebase scale (Instagram/Facebook monorepo, custom build tooling) | ★★★★★ |
| Airbnb | Modularized architecture, strict release trains, dynamic server-driven releases | ★★★★★ |
| Google | Large-scale iOS apps (YouTube, Maps, Drive), core platform team governance | ★★★★☆ |
| Stripe / Block | High financial reliability requirements, strict release gatekeeping & canary rollouts | ★★★★☆ |

---

## 1. Mobile Team Topology & Monorepo Architecture

### Staff/EM Decision Framework: Monorepo vs. Multi-Repo

```ascii
+-----------------------------------------------------------------------------------+
|                            MOBILE CODEBASE TOPOLOGY                               |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                             iOS MONOREPO                                    |  |
|  |                                                                             |  |
|  |  +-------------------+   +--------------------+   +----------------------+  |  |
|  |  | App Shell (Main)  |   | Core Infrastructure|   | Feature Modules      |  |  |
|  |  | (App Delegate,    |   | (Networking, Sync, |   | (Checkout, Search,   |  |  |
|  |  |  DI Registry)     |   |  Analytics, UI Kit)|   |  Ride Tracking)      |  |  |
|  |  +---------+---------+   +---------+----------+   +----------+-----------+  |  |
|  +------------|-----------------------|-------------------------|--------------+  |
|               |                       |                         |                 |
|               v                       v                         v                 |
|  +-----------------------------------------------------------------------------+  |
|  |                        BUILD & ARCHITECTURE GOVERNANCE                      |  |
|  |  - Swift Package Manager (SPM) / Bazel Tuist Graph Enforcer                  |  |
|  |  - Circular Dependency Prevention (Feature Modules cannot import each other)    |  |
|  |  - Interface vs Implementation Module Separation                              |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### Module Separation Principles (Uber / Google Model)
To prevent build times from exploding as engineering headcount scales from 10 to 150+ engineers, every domain must be split into **two distinct targets**:

1. **`FeatureInterface`**: Protocols, data models, public API contracts. *Zero implementation dependencies.*
2. **`FeatureImplementation`**: Internal SwiftUI views, ViewModels, business logic. *Imports only `FeatureInterface` targets.*

#### Swift Package Dependency Rule (Enforced via CI)
```
CheckoutInterface <----+
                       |
                       +--- RideTrackingImplementation (Compiles in parallel!)
                       |
RideTrackingInterface -+
```

---

## 2. Core Release Train & Canary Rollout Strategy

Unlike backend microservices which can deploy in seconds, iOS app binary releases are gated by Apple App Store review and user manual/auto-updates.

### 7-Day Phased Rollout Schedule (App Store Connect Standard)

```
Day 1: 1%   --> Monitor Crash-Free Session Rate (> 99.9%)
Day 2: 2%   --> Monitor ANR/Hang Rate (< 0.1%)
Day 3: 5%   --> Monitor Server API 5xx Spikes
Day 4: 10%  --> Feature Flag Kill Switch Check
Day 5: 20%
Day 6: 50%
Day 7: 100% --> Full Release
```

### Release Train Governance Rules (EM Standard)
1. **Weekly Fixed Release Train**: Cutting a release branch every Tuesday at 10:00 AM PST regardless of feature readiness. If a feature misses the train, it waits for next week's train.
2. **Feature Flag Mandatory Masking**: Every new line of code shipping to production **must be hidden behind a feature flag**. Unfinished features are safely merged into `main` without delaying the release train.
3. **Automated Release Gating**:
   * If crash-free sessions drop below **99.85%**, the automated canary system pauses the rollout automatically.
   * If HTTP 5xx error rates spike by $\ge 3\times$ baseline, the automated canary system pauses the rollout.

---

## 3. Incident Management & Sev-1 Mobile Triage Framework

### Sev-1 Scenario: A critical crash is affecting 5% of users after Day 3 rollout.

```ascii
+-----------------------------------------------------------------------------------+
|                         INCIDENT RESPONSE WORKFLOW (SEV-1)                        |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
                    +-------------------------------------------+
                    | 1. ISOLATE: Feature Flag Remote Kill      |
                    |    (Time to resolution < 5 minutes)       |
                    +---------------------+---------------------+
                                          |
                        +-----------------+-----------------+
                        | Feature flag    | Feature flag    |
                        | exists? (YES)   | missing? (NO)   |
                        v                 v                 v
          +-----------------------+     +-----------------------+
          | Disable flag instantly|     | Halt Rollout in       |
          | via Remote Config API |     | App Store Connect     |
          +-----------------------+     +-----------+-----------+
                                                    |
                                                    v
                                        +-----------------------+
                                        | Create Hotfix Branch  |
                                        | Cherry-pick fix       |
                                        | Expedited App Review  |
                                        +-----------------------+
```

### Key Metrics for Mobile Engineering Leaders (EM / Staff Benchmarks)

| Metric | Target / SLA | Source / Benchmark |
| :--- | :--- | :--- |
| Clean Build Time (CI) | $< 6\text{ minutes}$ | Tuist / Bazel Remote Cache Benchmark |
| Incremental Build Time (Dev) | $< 10\text{ seconds}$ | Xcode Build System Best Practices |
| Crash-Free Sessions | $> 99.9\%$ | Firebase Crashlytics Industry Baseline |
| Feature Flag Kill SLA | $< 5\text{ minutes}$ | Uber / Airbnb Feature Flag Production Rule |
| Mobile CI Flakiness Rate | $< 1.5\%$ of PR runs | Meta Mobile DevOps Metric |
| Pre-Main Cold Start Time | $< 500\text{ms}$ (p50) | Apple WWDC Session on Dynamic Linker |

---

## 4. FAANG-Style Mock Interview Q&A for EM & Staff Candidates

### Q1: How do you handle a team of 80 iOS engineers where build times have reached 25 minutes per PR?
**Answer**:
1. **Module Graph Decoupling**: Split monolithic targets into strict `Interface` vs `Implementation` modules using SPM/Tuist. This allows Xcode/Bazel to build independent features in parallel.
2. **Build Caching**: Implement remote build caching (Bazel Remote Cache or Tuist Cloud Cache) so CI nodes download pre-compiled `.swiftmodule` frameworks instead of re-compiling unchanged targets.
3. **Module Dependency Boundary Rule**: Enforce a CI rule preventing cross-feature implementation imports. Features must communicate strictly via DI interfaces (e.g., Needle or Swift-Dependencies).

### Q2: What is your policy for shipping a critical emergency hotfix to 10M users?
**Answer**:
1. **First Line of Defense**: Use remote feature flag kill switches to disable the broken code path instantly without updating the binary ($< 5\text{ min}$ SLA).
2. **Second Line of Defense**: If the crash is un-flagged (e.g., memory corruption in pre-main setup), immediately **Halt Rollout** in App Store Connect to prevent further user updates.
3. **Hotfix Branching**: Branch directly from the current live release tag (`release/12.4.0`), apply the minimal cherry-picked commit, run targeted regression suites, and submit to Apple using **Expedited App Review request** (typically approved within 2–4 hours).
