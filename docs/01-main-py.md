## Slide 3: Game Loop Flow

### **Main Loop** (main.py:73-160)
```
1. Setup Phase (line 78)
   → Trigger 'setup' event → All components initialize

2. Frame Capture Loop (lines 89-147)
   → Capture webcam frame
   → Flip for mirror effect
   → Trigger 'frame_received' event → PoseStrategy processes
   → Trigger 'process_sensor_queue' → AccelerometerStrategy processes
   → Update game timer

3. Punch Detection (lines 109-115)
   → FusionDetector.detect_punch() combines strategy results
   → If punch detected → Register punch → Update score/combo
   → Trigger UI effects

4. Rendering Phase (lines 117-125)
   → Trigger 'draw_overlays' → Strategies draw debug info
   → UIManager.draw_game_ui() → Core UI (score, combo)
   → Trigger 'draw_ui' chain → Strategy-specific UI

5. User Input (lines 131-146)
   → 'q' = Quit, 's' = Start, 'r' = Reset, 'space' = Test punch

6. Cleanup Phase (lines 152-159)
   → Trigger 'cleanup' event → All components cleanup
   → Release camera, close windows
```

---

## Slide 4: Event-Driven Communication

### **Event Types Used**
| Event | Trigger | Handlers |
|-------|---------|----------|
| `setup` | Game start | All strategies initialize |
| `frame_received` | Every frame | PoseStrategy processes MediaPipe |
| `process_sensor_queue` | Every frame | AccelerometerStrategy processes data |
| `punch_detected` | Punch registered | UI effects, state update |
| `game_state_changed` | Score updated | AccelerometerStrategy broadcasts to web |
| `draw_overlays` | Render phase | Strategies draw debug visualizations |
| `draw_ui` | Render phase | Strategies draw metric panels |
| `cleanup` | Game exit | All strategies cleanup resources |

### **Benefits**
- **Loose Coupling**: Components don't reference each other directly
- **Extensibility**: New strategies can subscribe to events without modifying existing code
- **Testability**: Components can be tested independently
