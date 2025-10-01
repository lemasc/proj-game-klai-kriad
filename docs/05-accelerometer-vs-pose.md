## Slide 28: PoseStrategy vs AccelerometerStrategy

### **Comparison**

| Aspect                  | AccelerometerStrategy            | PoseStrategy                     |
| ----------------------- | -------------------------------- | -------------------------------- |
| **Data Source**         | Smartphone accelerometer         | Webcam + MediaPipe               |
| **Primary Signal**      | Acceleration magnitude           | Wrist position + velocity        |
| **Latency**             | ~10-50ms (WebSocket)             | ~33ms (30 FPS)                   |
| **Reliability**         | High (measures force directly)   | Medium (visual occlusion issues) |
| **Setup Complexity**    | High (requires phone connection) | Low (webcam only)                |
| **Weight in Fusion**    | 70%                              | 30%                              |
| **Confident Threshold** | 15.0 m/s²                        | 0.6 score                        |
| **False Positives**     | Low (deliberate motion only)     | Higher (hand waves, reaching)    |
| **Advantages**          | Precise force measurement        | No external device needed        |
| **Disadvantages**       | Requires smartphone + network    | Sensitive to lighting/occlusion  |

### **Why 70/30 Weighting?**

- **Accelerometer** measures actual punch force → primary signal
- **Pose** provides visual confirmation → prevents gaming the system
- Combined: Requires both movement AND visible arm extension

---
