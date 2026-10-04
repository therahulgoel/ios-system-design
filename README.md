# Distributed Systems, Client Architecture & Engineering Leadership

![Repository banner](assets/banner.jpg)

Interview preparation for backend EM / SDM, staff engineers and engineering leaders, with a mobile architecture reference library.

## Start here

1. [Rahul's resume-based preparation plan](docs/rahul-backend-interview-plan.md): experience, evidence gaps, company guidance and readiness criteria.
2. [Backend EM, staff and leadership guide](docs/backend-engineering-manager-guide.md): correctness, data architecture, reliability, security and organizational judgment.
3. [Backend casebook](docs/backend-system-design-casebook.md): twelve design exercises, failure drills and role-specific follow-ups.
4. [Behavioral and leadership guide](docs/behavioral-engineering-manager-staff-guide.md): actual career evidence and probing practice.
5. [Evidence standard](docs/evidence-and-sources.md) and [repository review](docs/repository-review.md): supported claims, repairs and validation limits.

## How to use the material

Choose the actual role and its required scope. Reconstruct your own project evidence, study backend fundamentals, practice correctness and recovery, then rehearse coding, leadership and writing as required by the recruiter.

The client specifications cover API consumers, local state and device constraints. They complement backend preparation but do not establish experience operating server-side infrastructure. Embedded code is study material with incomplete dependencies, not a compiled application. Performance tuning choices require measurements for the actual environment.

Official process references: [Amazon SDM preparation](https://amazon.jobs/content/en/how-we-hire/sdm-interview-prep), [Google hiring](https://www.google.com/about/careers/applications/how-we-hire/), [Google DeepMind careers](https://deepmind.google/careers/), [SpaceX careers](https://www.spacex.com/careers/). Use the selected posting and recruiter instructions rather than assuming a universal loop or level mapping.

## Complete document catalog

All documents below exist in this checkout. Names of products describe design domains, not verified internal architectures or interview frequency.

| Document | Resource |
| :--- | :--- |
| Design a Mobile A/B Testing & Experimentation SDK | [ab-testing-experimentation-sdk.md](docs/ab-testing-experimentation-sdk.md) |
| Design Airbnb Search & Property Booking Engine | [airbnb-search-booking.md](docs/airbnb-search-booking.md) |
| Mobile Analytics & Telemetry SDK | [analytics-sdk.md](docs/analytics-sdk.md) |
| App Modularization & Dependency Injection System | [app-modularization.md](docs/app-modularization.md) |
| Design Mobile App Performance Monitoring System (APM) | [app-performance-monitoring.md](docs/app-performance-monitoring.md) |
| Design Mobile Authentication System (OAuth2 / SSO / Biometric) | [authentication-oauth-biometric.md](docs/authentication-oauth-biometric.md) |
| Master Guide: Backend Engineering Management, Staff Engineering & Leadership | [backend-engineering-manager-guide.md](docs/backend-engineering-manager-guide.md) |
| Backend System Design Casebook | [backend-system-design-casebook.md](docs/backend-system-design-casebook.md) |
| Engineering Leadership and Behavioral Interview Guide | [behavioral-engineering-manager-staff-guide.md](docs/behavioral-engineering-manager-staff-guide.md) |
| Mobile System Design - Master Cheatsheet | [cheatsheet.md](docs/cheatsheet.md) |
| Collaborative Document Editor (Google Docs / Notion / Quip) | [collaborative-editor.md](docs/collaborative-editor.md) |
| Design a Mobile Crash Reporting & Observability SDK | [crash-reporting-sdk.md](docs/crash-reporting-sdk.md) |
| Deep Linking Universal Links | [deep-linking-universal-links.md](docs/deep-linking-universal-links.md) |
| Design DoorDash / UberEats Live Delivery Order Tracking | [doordash-delivery-tracker.md](docs/doordash-delivery-tracker.md) |
| E-Commerce Product Catalog & Discovery Feed | [e-commerce-catalog.md](docs/e-commerce-catalog.md) |
| Evidence Standard and Verified Sources | [evidence-and-sources.md](docs/evidence-and-sources.md) |
| Feature Flag & Experimentation System | [feature-flag-system.md](docs/feature-flag-system.md) |
| Generic Mobile Problems | [generic-mobile-problems.md](docs/generic-mobile-problems.md) |
| Design Google Calendar Mobile Client | [google-calendar.md](docs/google-calendar.md) |
| Design Google Meet / Zoom Mobile App (Video Calling) | [google-meet-webrtc.md](docs/google-meet-webrtc.md) |
| Primary Reading Map: Learning Systems, Language Models and Agent Loops | [history-of-agentic-loops.md](docs/history-of-agentic-loops.md) |
| How AI Summarization Systems Work | [how-ai-summarization-agents-work.md](docs/how-ai-summarization-agents-work.md) |
| Image Loading Library | [image-loading-library.md](docs/image-loading-library.md) |
| Instant Messaging & Chat App (WhatsApp / Slack / iMessage) | [messaging-chat.md](docs/messaging-chat.md) |
| Example: .github/workflows/ios-ci.yml (Simplified) | [mobile-ci-cd-pipeline.md](docs/mobile-ci-cd-pipeline.md) |
| Mobile Platform Engineering, Release & Engineering Management Guide | [mobile-platform-engineering-em.md](docs/mobile-platform-engineering-em.md) |
| Mobile Security, Cryptography & Zero-Trust Engine | [mobile-security-privacy-engine.md](docs/mobile-security-privacy-engine.md) |
| Networking Layer / HTTP Client SDK Architecture | [networking-layer.md](docs/networking-layer.md) |
| Offline-First Data Sync Engine (Notes / Tasks / Drive) | [offline-sync-engine.md](docs/offline-sync-engine.md) |
| On-Device LLM and Mobile AI Architecture | [on-device-llm-ai-engine.md](docs/on-device-llm-ai-engine.md) |
| Mobile Payment Checkout Flow | [payment-checkout.md](docs/payment-checkout.md) |
| Design a Mobile Push Notification System | [push-notification-system.md](docs/push-notification-system.md) |
| Rahul Goel: Backend EM, Staff & Leadership Preparation Plan | [rahul-backend-interview-plan.md](docs/rahul-backend-interview-plan.md) |
| Real-Time Geospatial Tracking & Ride Tracking (Uber / Lyft / DoorDash) | [realtime-location-tracking.md](docs/realtime-location-tracking.md) |
| Repository Review and Repair Record | [repository-review.md](docs/repository-review.md) |
| Sdui Engine | [sdui-engine.md](docs/sdui-engine.md) |
| Design Mobile Search with Autocomplete & Offline Index | [search-autocomplete.md](docs/search-autocomplete.md) |
| Design Slack Mobile App - Multi-Workspace Channel Sync | [slack-channel-sync.md](docs/slack-channel-sync.md) |
| Infinite Social Feed | [social-feed.md](docs/social-feed.md) |
| Design Spotify / Apple Music Audio Player with Offline Mode | [spotify-audio-player.md](docs/spotify-audio-player.md) |
| Design User Analytics Event Pipeline | [user-analytics-event-pipeline.md](docs/user-analytics-event-pipeline.md) |
| Video Feed Streaming | [video-feed-streaming.md](docs/video-feed-streaming.md) |
| Video Streaming Player | [video-streaming-player.md](docs/video-streaming-player.md) |

## Verification and contribution

Run `python3 scripts/check_docs.py` for local documentation checks. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [REPO_SPEC.md](REPO_SPEC.md) before contributing. Technical facts need exact primary sources; production and career claims need evidence. Do not add invented records, benchmark outcomes or first-person stories.

## Author and license

Rahul Goel. Career context: [public resume](https://therahulgoel.github.io/Rahul_Goel_Resume.pdf). Candidate-reported metrics are distinguished from independently verified technical behavior throughout the preparation plan.

Licensed under [MIT](LICENSE).
