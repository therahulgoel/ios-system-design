# iOS System Design Interview Experiences

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A personal collection of real interview experiences and system design questions from product companies, curated by Rahul Goel. This repository focuses on common problems faced in mobile engineering interviews and highlights proven solutions for scaling mobile apps. Keywords: iOS system design interviews, mobile engineering, interview preparation, system design questions.

> See the repository architecture guideline: [REPO_SPEC.md](REPO_SPEC.md)

## 👨‍💻 About the Author

I'm Rahul Goel, an Engineering Manager - iOS with 12 years of experience and roles at SonyLiv, ShareChat, Paytm, and Myntra. I've scaled iOS apps to 100M+ users across domains like Shorts, Streaming, Payments, and E-commerce. This repository represents my journey through technical interviews at product companies, documenting the challenges, solutions, and growth opportunities I've encountered.

## 📋 Table of Contents

- [About](#about)
- [Essential Problems & Solutions](#essential-problems--solutions)
- [Industry-Specific Challenges](#industry-specific-challenges)
- [Interview Framework](#interview-framework)
- [Key Learnings](#key-learnings)
- [Repository Spec](#repository-spec)
- [Resources](#resources)
- [License](#license)

## 🎯 About

This repository is my personal archive of authentic interview experiences from mobile engineering roles at leading Indian tech companies. It highlights proven solutions for day-to-day problems in building mobile apps that scale to millions of users, based on real-world implementation and interview insights.

As someone passionate about mobile development, I created this to document my journey and provide valuable insights for others pursuing similar paths in the Indian tech ecosystem.

## 🌟 Why This Repository?

- **Real-World Insights**: Authentic experiences from interviews at India's top tech companies
- **Expert Perspective**: Curated by someone who's scaled apps to 100M+ users
- **Focused on iOS**: Deep dives into mobile-specific system design challenges
- **Practical Framework**: Step-by-step interview approach based on proven experience
- **Best Solutions**: Highlighted approaches that work for apps serving millions of users

## 🔍 Essential Problems & Solutions for Scalable Mobile Apps

This repository focuses on critical problems faced in day-to-day development of mobile apps serving millions of users. Below is a curated table of key challenges and their proven best solutions, drawn from real-world experience scaling iOS apps.

| Problem | Best Solution | Key Benefits for Millions of Users |
|---------|---------------|------------------------------------|
| **App Architecture Design** | MVVM with modular components and dependency injection | Enables parallel development, easier testing, and seamless feature scaling without breaking existing code |
| **Scalability Considerations** | Horizontal scaling with load balancers, CDN for static assets, and efficient caching strategies | Handles sudden user spikes, reduces server load, and ensures consistent performance during peak times |
| **Database Design for Mobile Apps** | Core Data with offline-first sync using background tasks and conflict resolution | Provides reliable offline access, minimizes data loss, and syncs efficiently across devices |
| **API Design and Integration** | RESTful APIs with GraphQL for complex queries, proper authentication (OAuth/JWT), and rate limiting | Reduces over-fetching, secures data transmission, and prevents API abuse while maintaining flexibility |
| **Performance Optimization** | Lazy loading, image optimization (WebP/AVIF), memory management with ARC, and background processing | Minimizes battery drain, improves app responsiveness, and handles large datasets without crashes |
| **Networking and Data Synchronization** | URLSession with background sessions, exponential backoff for retries, and real-time sync via WebSockets | Ensures reliable connectivity, handles network fluctuations, and provides instant updates for collaborative features |

Each solution is battle-tested in production environments and optimized for iOS ecosystem constraints.
## 🧩 Generic Mobile Problems

This section covers essential, platform-agnostic mobile design problems with a focus on what iOS engineers need to know.

| Problem | Best Solution | iOS-Specific Notes |
|---------|---------------|-------------------|
| **[Designing Search in Mobile Apps](docs/generic-mobile-problems.md)** | Use a responsive search UI with debounce, incremental results loading, local caching, and lightweight token-based query filtering | Implement debounce using standard SwiftUI patterns or throttled DispatchWorkItem, build a custom search page, support search suggestions, and optimize results rendering using diffable data sources |
## � Industry-Specific Challenges

Drawing from my experience scaling apps across different domains, here are industry-specific challenges and their proven solutions.

### Payments (e.g., Fintech Apps)
| Challenge | Best Solution | Key Benefits |
|-----------|---------------|--------------|
| **Server-driven UI for Home Screen SDK** | Remote configuration with server-driven cards and modular screens | Enables real-time UI updates, personalization, and faster release cycles without app updates |

### E-commerce (e.g., Shopping Apps)
| Challenge | Best Solution | Key Benefits |
|-----------|---------------|--------------|
| **Product Catalog Performance** | Efficient caching with optimized image delivery | Improves browsing speed and keeps users engaged during discovery |

### Social/Shorts (e.g., Content Platforms)
| Challenge | Best Solution | Key Benefits |
|-----------|---------------|--------------|
| **Optimizing for Low Network** | Adaptive image quality, progressive image loading, and local caching | Faster image load times and smoother feed experience on weak connections |

### Travel (e.g., Booking Apps)
| Challenge | Best Solution | Key Benefits |
|-----------|---------------|--------------|
| **Shareable Wishlist Feature** | Cloud-synced wishlists with share links and real-time collaboration | Makes planning social trips easier, keeps wishlist state consistent, and boosts engagement |

## 🏗️ Interview Framework

Based on my experiences, here's a structured approach to mobile system design interviews (45-60 minutes):

### 1. Introductions (2-5 min)
Briefly share relevant experience and background to build rapport.

### 2. Task Definition (5 min)
Clarify the scope: client-side only, client + API, or full-stack design.

### 3. Requirements Gathering (10 min)
Categorize into functional, non-functional, and out-of-scope features.

### 4. High-Level Discussion (20-30 min)
Present system architecture, component interactions, and trade-offs.

### 5. Detailed Discussion (10-15 min)
Deep dive into specific components like data storage, API design, or performance.

### 6. Questions for Interviewer (5 min)
Ask about team size, tech stack, or company-specific challenges.

## ❓ Standard Interview Question

- **How would you design a mobile feed that serves personalized content to millions of users while maintaining offline access and optimal performance?**

This question tests your ability to balance user experience, data synchronization, caching, and scalability in a mobile-first system design.

## 🧠 Key Learnings

Through these interviews, I've gained deep insights into:

- Designing scalable mobile architectures
- Balancing user experience with technical constraints
- Communicating complex technical concepts effectively
- Adapting to different company cultures and expectations
- Continuous learning in the fast-evolving mobile landscape

## � Repository Spec

This repository follows an architectural convention detailed in [REPO_SPEC.md](REPO_SPEC.md), including MVVM, SwiftUI with `ObservableObject`, `URLSession` networking, and custom search flow patterns.

## �📚 Resources

- [iOS Developer Documentation](https://developer.apple.com/documentation/)
- [System Design Primer](https://github.com/donnemartin/system-design-primer)
- [Repository Implementation Rules](REPO_SPEC.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Happy interviewing! 🚀*

If you find this repository helpful, please ⭐ **star it** to help others discover these valuable insights!