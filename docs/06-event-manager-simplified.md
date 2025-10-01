# EventManager - Simplified Guide

## What is EventManager?

EventManager is a **publish-subscribe (pub-sub) event system** that enables components in the game to communicate without knowing about each other. Think of it as a central message hub where components can:

- **Listen** for specific events they care about
- **Broadcast** events when something important happens

Instead of components directly calling methods on each other, they communicate through events. This keeps the code loosely coupled and modular.

---

## How Does It Work?

### Step 1: Register Hooks (Subscribe to Events)

Components register callback functions for specific events they want to listen to.

**Example from [AccelerometerStrategy](../detection/accelerometer/accelerometer_strategy.py):**

```python
class AccelerometerStrategy(BaseDetectionStrategy):
    def register_hooks(self):
        # Listen for the 'setup' event
        self.event_manager.register_hook('setup', self.setup_server, priority=10)

        # Listen for the 'process_sensor_queue' event
        self.event_manager.register_hook('process_sensor_queue',
                                         self.process_sensor_queue, priority=10)

        # Listen for the 'cleanup' event
        self.event_manager.register_hook('cleanup', self.cleanup_server, priority=10)
```

**Parameters:**

- `event_name`: The event to listen for (e.g., 'setup', 'frame_received')
- `callback`: The function to call when the event triggers
- `priority`: Higher numbers run first (default is 0)

### Step 2: Trigger Events (Publish Messages)

When something important happens, components trigger events to notify all listeners.

**Example from [main.py](../main.py):**

```python
class PunchDetectionGame:
    def run(self):
        # Initialize all strategies
        self.event_manager.trigger_event('setup')

        while True:
            frame = self.camera.read()

            # Send frame to all listeners
            self.event_manager.trigger_event('frame_received', frame)

            # Process sensor data
            self.event_manager.trigger_event('process_sensor_queue')

            # Draw UI with context chaining
            draw_context = {'next_y': 40, 'x': 220}
            self.event_manager.trigger_event_chain('draw_ui', draw_context, frame)
```

### Event Flow Example

When `trigger_event('setup')` is called:

```
EventManager broadcasts 'setup' event
  ├─ AccelerometerStrategy.setup_server() executes
  │   ├─ Starts Flask server for phone connection
  │   └─ Initializes MotionAnalyzer
  │
  └─ PoseStrategy.setup_mediapipe() executes
      ├─ Initializes MediaPipe pose detection
      └─ Creates PoseAnalyzer
```

Both strategies set themselves up **without knowing about each other** or the main game loop.

---

## Benefits

1. **Loose Coupling**

   - Strategies don't need references to the main game or each other
   - Components can be developed and tested independently
   - Easy to understand each component in isolation

2. **Easy Extensibility**

   - Want to add a new detection strategy? Just register hooks for the events you need
   - No need to modify existing strategies or main game loop
   - Example: Adding sound effects just requires listening to `punch_detected` event

3. **Error Isolation**

   - If one strategy crashes, others continue working
   - The game gracefully degrades instead of completely breaking
   - Errors are logged with the event name for easier debugging

4. **Priority Control**

   - Control the execution order of callbacks using priority values
   - Critical components can execute first
   - UI components can chain outputs (e.g., stacking UI elements vertically)

5. **Clean Code Organization**
   - Each component focuses only on its own responsibility
   - Main game loop remains simple and readable
   - Clear separation between detection logic, game state, and UI rendering
