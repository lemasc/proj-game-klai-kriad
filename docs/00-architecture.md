## Slide 1: System Overview - Main Architecture

### **PunchDetectionGame Class**

The central orchestrator that coordinates all game components through an event-driven architecture.

### **Core Components** (main.py:19-36)

```
EventManager → Central event bus for component communication
GameState → Manages scoring, combos, timing, and game lifecycle
UIManager → Handles visual rendering and effects
FusionDetector → Combines multiple detection strategies
Detection Strategies → AccelerometerStrategy + PoseStrategy
```

### **Key Design Patterns**

- **Event-Driven Architecture**: All components communicate via EventManager
- **Strategy Pattern**: Pluggable detection strategies with weighted fusion (70% accel, 30% pose)
- **Separation of Concerns**: Detection ↔ Game Logic ↔ UI are independent

---

## Slide 2: Architecture Diagram

```mermaid
graph TD
    Main[PunchDetectionGame<br/>main.py:18-160]
    EM[EventManager<br/>Central Event Bus]
    GS[GameState<br/>Score & Timer]
    UI[UIManager<br/>Visual Rendering]
    FD[FusionDetector<br/>Strategy Combiner]
    AS[AccelerometerStrategy<br/>Weight: 0.7]
    PS[PoseStrategy<br/>Weight: 0.3]
    CAM[OpenCV Camera<br/>Webcam Feed]
    SENSOR[Flask Server<br/>Smartphone Data]

    Main --> EM
    Main --> GS
    Main --> UI
    Main --> FD
    Main --> CAM

    FD --> AS
    FD --> PS

    AS --> SENSOR
    PS --> CAM

    EM -.event: punch_detected.-> GS
    EM -.event: frame_received.-> PS
    EM -.event: process_sensor_queue.-> AS
    EM -.event: draw_ui.-> UI
    EM -.event: draw_overlays.-> AS
    EM -.event: draw_overlays.-> PS

    style Main fill:#4CAF50
    style EM fill:#2196F3
    style FD fill:#FF9800
    style AS fill:#9C27B0
    style PS fill:#9C27B0
```
