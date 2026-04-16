# Repository Implementation Rules

This repository follows a consistent architectural convention for iOS mobile system design and sample implementations.

## Core Rule

- Use MVVM for all app/UI-related examples and implementations.
- Build SwiftUI views backed by `ObservableObject` ViewModels.
- Keep view logic in SwiftUI views, state and business logic in ViewModels, and networking/caching in separate services or data layers.

## Networking

- Use `URLSession` for API calls.
- Prefer lightweight request models, proper error handling, and response decoding with `JSONDecoder`.
- Avoid `UISearchController` for custom SwiftUI search flows; use a custom search page instead.

## Recommended Patterns

- Debounce search input in the ViewModel.
- Cache recent search queries and results to improve performance.
- Keep service dependencies injectable for testability.
- Maintain clear separation:
  - `View` — presentation and bindings
  - `ViewModel` — input handling, state updates, orchestration
  - `Service / Data Layer` — network, cache, persistence

## Why This Rule

- MVVM improves testability and separation of concerns.
- It keeps SwiftUI views declarative and lightweight.
- It makes design examples easier to map to production iOS apps.

This file is the authoritative repo-level guideline for architecture and implementation conventions.
