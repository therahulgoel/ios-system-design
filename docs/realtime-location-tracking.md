# Real-Time Geospatial Tracking & Ride Tracking (Uber / Lyft / DoorDash)

## Overview
Designing a system for real-time location tracking involves capturing high-frequency GPS data on a provider app (driver), transmitting it efficiently, and smoothly rendering it on a consumer app (rider). It tests hardware API knowledge (CoreLocation), battery optimization, noisy data filtering, and real-time networking.

## Target Companies & Frequency
| Company | Why They Ask | Frequency |
|---------|--------------|-----------|
| Uber / Lyft | Core to their entire business model. | ★★★★★ |
| DoorDash / Instacart | Real-time delivery tracking. | ★★★★★ |
| Grab / GoJek | Super-apps with heavy ride/delivery focus. | ★★★★★ |

## Scope Definition

### In Scope
- Driver app: GPS capture, noise filtering, efficient transmission.
- Rider app: Real-time map rendering, car animation, route interpolation.
- Network transport (WebSockets / Server-Sent Events).
- Battery and thermal management.
- Offline/Network failure caching.

### Out of Scope
- Ride matching algorithms (dispatch).
- Payment processing.
- Routing engine (Google Maps API backend).

## Requirements

### Functional Requirements
1. Driver app transmits location every few seconds.
2. Rider app shows car moving smoothly on a map.
3. System calculates and updates ETA.
4. Must handle GPS dead zones (tunnels, rural areas).

### Non-Functional Requirements
| Requirement | Target | Source |
|-------------|--------|--------|
| Transmission Frequency | 2-4s (Active) / 15s (Background) | Uber Eng Blog |
| Location Accuracy | ±3m to ±5m | CLLocation Docs |
| Battery Consumption | < 5% per hour | iOS Guidelines |
| Render Framerate | 60fps (Smooth animation) | MapKit Guidelines |

## High-Level Architecture (HLD)

### Component Diagram
```text
[Driver App]                              [Rider App]
    │                                         │
    ├─► CoreLocation Manager                  ├─► MapKit / UI Layer
    ├─► Kalman Filter (Noise reduction)       ├─► Animation Engine (Interpolator)
    ├─► Location Batcher                      ├─► WebSocketManager
    ├─► WebSocketManager                      └─► Local Cache
    │                                         
    ▼                                         ▼
[ API Gateway / Load Balancer (Envoy) ] ◄─────┘
    │
    ├─► WebSocket Connection Handlers (Go)
    ├─► Pub/Sub Message Bus (Kafka)
    ├─► ETA / Routing Service
    └─► Geospatial DB (PostGIS / Redis Geo)
```

### Component Responsibilities
| Component | Responsibility | iOS Implementation |
|-----------|----------------|--------------------|
| LocationTracker | Interfaces with OS, requests permissions. | `CLLocationManager` |
| KalmanFilter | Smooths GPS jitter before network send. | Swift math logic |
| LocationBatcher | Groups coordinates to reduce HTTP/WS overhead. | Swift Queue |
| MapViewController | Renders map, polylines, and car annotations. | `MKMapView` / MapKit |
| TripViewModel | Manages state machine (waiting, active, complete). | `ObservableObject` |

### Data Flow
1. **Capture**: OS wakes driver app, provides raw `CLLocation`.
2. **Process**: Filter applies logic (drop inaccurate points, Kalman smooth).
3. **Transmit**: Location appended to batch. Sent via WS every 4s.
4. **Broadcast**: Backend receives, saves to Redis, pushes to Kafka topic.
5. **Consume**: Rider app WS receives location payload.
6. **Render**: Rider app interpolates car from old coordinate to new coordinate over 4 seconds.

## Data Models

### Core Entities
```swift
import Foundation
import CoreLocation

struct TripLocation: Codable, Equatable {
    let latitude: Double
    let longitude: Double
    let accuracy: Double
    let speed: Double
    let heading: Double
    let timestamp: TimeInterval
}

struct TripState: Codable {
    let tripId: String
    let status: String // "en_route", "arrived", "in_progress"
    let estimatedTimeOfArrival: TimeInterval
    let remainingDistanceMeters: Double
}
```

## API Design

### Endpoints

**1. WebSocket Connection (Driver & Rider)**
- **URL**: `wss://realtime.example.com/v2/trips/{tripId}`
- **Payload (Driver -> Server)**:
```json
{
  "type": "location_batch",
  "locations": [
    {
      "lat": 37.7749,
      "lng": -122.4194,
      "accuracy": 5.0,
      "heading": 90.0,
      "timestamp": 1690000000
    }
  ]
}
```
- **Payload (Server -> Rider)**:
```json
{
  "type": "driver_update",
  "location": { "lat": 37.7749, "lng": -122.4194, "heading": 90.0 },
  "eta_seconds": 320
}
```

## Client Architecture Deep-Dives

### 1. Driver Side: CoreLocation & Battery Management
CoreLocation is heavily optimized, but poor configuration kills batteries. We use `distanceFilter` and monitor `ProcessInfo` for low power mode.

```swift
import CoreLocation
import Foundation

class LocationTracker: NSObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    private var isLowPowerMode: Bool { ProcessInfo.processInfo.isLowPowerModeEnabled }
    
    override init() {
        super.init()
        manager.delegate = self
        manager.allowsBackgroundLocationUpdates = true
        manager.pausesLocationUpdatesAutomatically = false
        
        configureAccuracy()
        
        NotificationCenter.default.addObserver(self, selector: #selector(powerModeChanged), name: .NSProcessInfoPowerStateDidChange, object: nil)
    }
    
    @objc private func powerModeChanged() {
        configureAccuracy()
    }
    
    private func configureAccuracy() {
        if isLowPowerMode {
            // Battery saving
            manager.desiredAccuracy = kCLLocationAccuracyHundredMeters
            manager.distanceFilter = 50 // meters
        } else {
            // High fidelity for driving
            manager.desiredAccuracy = kCLLocationAccuracyBestForNavigation
            manager.distanceFilter = 10 // meters
        }
    }
    
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let latest = locations.last, latest.horizontalAccuracy < 20 else { return }
        // Filter out bad accuracy points (e.g., cell tower triangulation)
        
        // 1. Pass to Kalman Filter
        // 2. Batch and transmit
    }
}
```

### 2. Driver Side: GPS Smoothing (Kalman Filter Concept)
Raw GPS jumps around. A Kalman filter uses the driver's speed and heading to predict where they should be, and merges it with the raw GPS coordinate to produce a smoothed result. (Reduces ±15m jumps to ±3m). *Note: Full matrix math is usually abstracted in interviews, but knowing the concept is a strong signal.*

### 3. Rider Side: Smooth Map Animation & Interpolation
If we receive an update every 4 seconds, simply setting the car annotation's coordinate makes it "teleport". We must interpolate the movement.

```swift
import MapKit

class DriverAnnotation: MKPointAnnotation {}

class MapViewController: UIViewController {
    var mapView = MKMapView()
    var driverMarker = DriverAnnotation()
    
    func updateDriverLocation(to newLocation: CLLocationCoordinate2D, heading: CLLocationDirection) {
        // CoreAnimation to smoothly slide the marker over 4 seconds
        UIView.animate(withDuration: 4.0, delay: 0, options: [.curveLinear, .allowUserInteraction]) {
            self.driverMarker.coordinate = newLocation
        }
        
        // Rotate the marker view to match heading
        if let view = mapView.view(for: driverMarker) {
            UIView.animate(withDuration: 1.0) {
                view.transform = CGAffineTransform(rotationAngle: CGFloat(heading * .pi / 180))
            }
        }
    }
    
    // Polyline updates: Only redraw the delta!
    // Re-rendering a 1000-point polyline takes 16ms+. 
    // Re-rendering just the sliced path in front of the driver is <1ms.
}
```

### 4. WebSocket Reconnection & Jitter
Like the chat app, the WebSocket must use exponential backoff (1s → 2s → 4s → 8s → max 60s) with ±30% jitter to prevent DDOSing the server on reconnects.

## Performance & Optimizations
| Optimization | Technique | Benchmark/Impact |
|--------------|-----------|------------------|
| Location Batching | Send array of 3-4 points every 4s instead of 1 per sec | Reduces radio wakeups, saves ~15% battery |
| Map Polyline Delta | Slice polyline array, only render remaining route | 16ms -> <1ms UI frame time |
| Backgrounding | Keep WS alive via background task / silent push | Maintains state when user switches apps |

## Failure Modes & Fallbacks
| Failure Scenario | Detection | Fallback Strategy |
|------------------|-----------|-------------------|
| Dead Zone (Driver) | Network offline | Queue GPS points in SQLite. Burst send when reconnected. |
| WS Disconnect (Rider)| Heartbeat fail | Fallback to HTTP Polling (every 5s) for ETAs until WS recovers. |
| GPS Spoofing | Unrealistic speed/jumps | Server-side validation drops points > 200mph or impossible jumps. |

## Trade-off Analysis
| Decision | Option A | Option B | Chosen | Why |
|----------|----------|----------|--------|-----|
| Transport | SSE (Server-Sent Events) | WebSockets | WebSockets | WS is bidirectional, which is perfect for the Driver sending up. SSE is fine for Rider, but WS standardizes stack. |
| Location API | `.nearestTenMeters` | `.bestForNavigation` | `.best` (contextual) | `.bestForNavigation` uses more battery but provides sensor fusion (gyro+accelerometer) for smoother headings. |
| Rider Sync | Pull | Push (WS) | Push | Polling wastes bandwidth and battery on the rider device. |

## Observability & Metrics
- **Location Fix Rate**: Percentage of GPS points with accuracy < 10m.
- **Data Freshness**: Latency between driver timestamp and rider receive timestamp (p99 < 1s).
- **Battery Drain**: Monitored via OS metrics; critical SLA for driver app.

## Production Benchmarks Reference
| Metric | Value | Source |
|--------|-------|--------|
| Transmission Rate | 4 seconds | Uber Engineering |
| Kalman Filter | Reduces noise ~60% | Geospatial studies |
| WS Heartbeat | 30s | RFC 6455 |

## Interview Tips
- **Drive the dual-app narrative**: Explicitly separate your design into "Provider (Driver)" and "Consumer (Rider)". The constraints are completely different.
- **Battery is everything**: The interviewer wants to hear about `distanceFilter`, `desiredAccuracy`, and batching. If you don't mention battery on the driver side, you fail.
- **Interpolation**: Mention that cars shouldn't "teleport" on the map. This shows product-minded UI engineering.
