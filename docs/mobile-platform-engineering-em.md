# Mobile Platform Engineering, Release & Engineering Management Guide

> Reference status: client architecture study material. Embedded code and payloads are incomplete design sketches, not verified production implementations or records from the named products. Do not quote remaining numeric tuning choices as employer benchmarks. For backend preparation, start with the [backend guide](backend-engineering-manager-guide.md) and [evidence standard](evidence-and-sources.md).


## Overview
Study module ownership, release coordination, incident response and developer productivity. Backend rollback and mobile recovery have different constraints. Halting an App Store rollout does not replace installed app binaries. A remote flag helps only if the shipped application contains a safe alternative and receives the configuration.

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

### Phased release and recovery
Apple's automatic phased-update schedule is 1%, 2%, 5%, 10%, 20%, 50%, then 100% over seven days. Manual downloads remain possible throughout. See [Apple phased release](https://developer.apple.com/help/app-store-connect/update-your-app/release-a-version-update-in-phases).

Choose release cadence, gates and observation windows from customer risk and measured traffic. Define who can pause distribution, disable a supported feature, and submit a fixed binary. Do not claim guaranteed kill-switch delivery or App Review completion time.

## 3. Incident management

Assign incident command and technical coordination. Identify affected versions and cohorts, use a safe available mitigation, pause further distribution if appropriate, and verify user outcomes. A pre-main crash may prevent feature configuration from loading; a fixed binary may be required. Track residual users on the affected version.

Measure build latency, flakiness, crash-free sessions, startup, adoption and mitigation propagation with explicit denominators and cohorts. Do not quote fixed budgets as company standards.

## 4. FAANG-Style Mock Interview Q&A for EM & Staff Candidates

### Q1: How do you handle a team of 80 iOS engineers where build times have reached 25 minutes per PR?
**Answer**:
1. **Module Graph Decoupling**: Split monolithic targets into strict `Interface` vs `Implementation` modules using SPM/Tuist. This allows Xcode/Bazel to build independent features in parallel.
2. **Build Caching**: Implement remote build caching (Bazel Remote Cache or Tuist Cloud Cache) so CI nodes download pre-compiled `.swiftmodule` frameworks instead of re-compiling unchanged targets.
3. **Module Dependency Boundary Rule**: Enforce a CI rule preventing cross-feature implementation imports. Features must communicate strictly via DI interfaces (e.g., Needle or Swift-Dependencies).

### Q2: What is your policy for shipping a critical emergency hotfix to 10M users?
**Answer**:
1. **First Line of Defense**: Use remote feature flag kill switches to disable a supported broken path for clients that receive the configuration. Measure propagation and retain a recovery path for offline clients.
2. **Second Line of Defense**: If the crash is un-flagged (e.g., memory corruption in pre-main setup), immediately **Halt Rollout** in App Store Connect to prevent further user updates.
3. **Hotfix Branching**: Branch directly from the current live release tag (`release/12.4.0`), apply the minimal cherry-picked commit, run targeted regression suites, and submit to Apple using **Expedited App Review request** without assuming a guaranteed review completion time.
