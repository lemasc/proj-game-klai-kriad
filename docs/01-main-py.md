## Slide 3: Game Loop Flow

### **Main Loop** (main.py:73-160)

1. Setup Phase (line 78)

   - Trigger 'setup' event → All components initialize

2. Frame Capture Loop (lines 89-147)
   - Capture webcam frame
   - Flip for mirror effect
   - (ต่อในสไลด์ถัดไป)

```python
class PunchDetectionGame:
    def run(self):
        # Trigger setup event for all components
        self.event_manager.trigger_event('setup')

        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

        if not self.cap.isOpened():
            print("Error: Could not open camera")
            return

        try:
            while True:
                # Capture frame (strategies handle their own processing)
                ret, frame = self.cap.read()
                if not ret:
                    print("Error: Could not read frame")
                    break

                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                # ...
```

---

2. Frame Capture Loop (lines 89-147) (Continue)

   - Trigger 'frame_received' event → PoseStrategy processes
   - Trigger 'process_sensor_queue' → AccelerometerStrategy processes
   - Update game timer

3. Punch Detection (lines 109-115)
   - FusionDetector.detect_punch() combines strategy results
   - If punch detected → Register punch → Update score/combo
   - Trigger UI effects

```python
# Flip frame horizontally for mirror effect
frame = cv2.flip(frame, 1)

# Trigger frame_received event (PoseStrategy will handle MediaPipe processing)
self.event_manager.trigger_event('frame_received', frame)

# Trigger sensor queue processing (AccelerometerStrategy handles internally)
self.event_manager.trigger_event('process_sensor_queue')

# Update game timer if playing
self.game_state.update_timer()

# Detect punches using fusion detector (only during PLAYING state)
if self.game_state.is_playing():
    is_punch, punch_score, metrics = self.fusion_detector.detect_punch()

    if is_punch:
        self.register_punch(punch_score, time.time())
        # Trigger visual effect
        self.ui_manager.trigger_punch_effect()
```

---

4. Rendering Phase (lines 117-125)
   - Trigger 'draw_overlays' → Strategies draw debug info
   - UIManager.draw_game_ui() → Core UI (score, combo)
   - Trigger 'draw_ui' chain → Strategy-specific UI

```python
# Trigger drawing phase events (strategies handle their own drawing)
self.event_manager.trigger_event('draw_overlays', frame)

# Draw core game UI (score, combo, instructions, effects)
self.ui_manager.draw_game_ui(frame, self.game_state)

# Trigger strategy UI drawing with position context for chaining
draw_context = {'next_y': STRATEGY_UI_START_Y, 'x': STRATEGY_UI_START_X}
self.event_manager.trigger_event_chain('draw_ui', draw_context, frame)

# Display frame
cv2.imshow('Punch Detection Game', frame)
```

---

5. User Input (lines 131-146)
   - 'q' = Quit, 's' = Start, 'r' = Reset, 'space' = Test punch

```python
# Handle keyboard input
key = cv2.waitKey(1) & 0xFF
if key == ord('q'):
    break
elif key == ord('s'):
    # Start game from menu
    if self.game_state.is_menu():
        self.game_state.start_game()
        print("Game starting...")
elif key == ord('r'):
    # Return to menu / restart
    self.game_state.return_to_menu()
    print("Returned to menu")
elif key == ord(' '):
    # Manual punch trigger for testing (only during PLAYING)
    if self.game_state.is_playing():
        self.register_punch(1.0, time.time())
```

---

6. Cleanup Phase (lines 152-159)
   - Trigger 'cleanup' event → All components cleanup
   - Release camera, close windows

```python
class PunchDetectionGame:
    def run(self):
        try:
            while True:
                # ...

        except KeyboardInterrupt:
            print("\nGame interrupted by user")

        finally:
            # Trigger cleanup event for all components
            self.event_manager.trigger_event('cleanup')
            if self.cap:
                self.cap.release()
                self.cap = None
            cv2.destroyAllWindows()
            print(f"\nFinal Score: {self.game_state.get_score()}")
            print(f"Total Punches: {self.game_state.get_punch_count()}")
```
