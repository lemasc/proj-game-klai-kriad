import cv2
import time
from dotenv import load_dotenv

# Load environment variables at the start
load_dotenv()

# Import configuration modules
from detection.detection_config import *
from game.game_config import *
from detection.fusion_detector import FusionDetector
from detection.accelerometer.accelerometer_strategy import AccelerometerStrategy
from detection.pose.pose_strategy import PoseStrategy
from game.game_state import GameState
from game.ui_manager import UIManager
from game.event_manager import EventManager
from evaluation.recording_manager import RecordingManager

class PunchDetectionGame:
    def __init__(self):
        # Event system
        self.event_manager = EventManager()

        # Camera setup
        self.cap = None

        # Game state
        self.game_state = GameState(self.event_manager)

        # UI Manager
        self.ui_manager = UIManager()

        # FusionDetector now uses event system
        self.fusion_detector = FusionDetector(self.event_manager)

        # Recording manager for evaluation
        self.recording_manager = RecordingManager(self.event_manager)
        self.evaluation_mode = False

        # Initialize detection strategies
        self._init_strategies()

        # Setup event listeners for evaluation mode
        self._setup_evaluation_listeners()

        print("Detection strategies initialized")
        print("Open the smartphone web interface to connect accelerometer")

    def _init_strategies(self):
        """Initialize detection strategies and add them to fusion detector."""
        # Initialize accelerometer strategy (handles sensor data internally)
        self.accelerometer_strategy = AccelerometerStrategy(
            event_manager=self.event_manager,
            game_state_provider=self._get_game_state
        )

        # Initialize pose strategy
        self.pose_strategy = PoseStrategy(self.event_manager)

        # Add strategies to fusion detector with weights
        self.fusion_detector.add_strategy(self.accelerometer_strategy, weight=ACCEL_WEIGHT)
        self.fusion_detector.add_strategy(self.pose_strategy, weight=VISUAL_WEIGHT)

    def _get_game_state(self):
        """Provide current game state for the sensor server"""
        return self.game_state.get_state_dict()

    def _setup_evaluation_listeners(self):
        """Setup event listeners for automatic recording in evaluation mode."""
        # Listen for game state changes to auto-start/stop recording
        self.event_manager.register_hook('game_mode_changed', self._on_game_mode_changed)

    def _on_game_mode_changed(self, new_mode):
        """Handle game mode changes for automatic recording.

        Args:
            new_mode: The new game mode (GameMode enum)
        """
        from game.game_state import GameMode

        if not self.evaluation_mode:
            return

        # Start recording when entering PLAYING mode
        if new_mode == GameMode.PLAYING:
            if not self.recording_manager.is_recording():
                resolution = (CAMERA_WIDTH, CAMERA_HEIGHT)
                fps = 30  # TODO: Get actual FPS from camera
                detection_config = {
                    'accel_threshold': ACCEL_PUNCH_THRESHOLD,
                    'visual_threshold': VISUAL_PUNCH_THRESHOLD,
                    'accel_weight': ACCEL_WEIGHT,
                    'visual_weight': VISUAL_WEIGHT
                }
                self.recording_manager.start_recording(resolution, fps, detection_config)
                print("📹 Recording started (evaluation mode)")

        # Stop recording when leaving PLAYING mode (game over or return to menu)
        elif new_mode in (GameMode.GAME_OVER, GameMode.MENU):
            if self.recording_manager.is_recording():
                session_dir = self.recording_manager.stop_recording()
                if session_dir:
                    print(f"💾 Recording saved: {session_dir}")

    def toggle_evaluation_mode(self):
        """Toggle evaluation mode on/off."""
        self.evaluation_mode = not self.evaluation_mode
        status = "ENABLED" if self.evaluation_mode else "DISABLED"
        print(f"🔬 Evaluation Mode {status}")

        # Stop any active recording if disabling evaluation mode
        if not self.evaluation_mode and self.recording_manager.is_recording():
            self.recording_manager.stop_recording()
            print("Recording stopped (evaluation mode disabled)")
    
    def register_punch(self, score, timestamp):
        """Register a successful punch and update game state"""
        punch_result = self.game_state.register_punch(score, timestamp)

        # Trigger punch detected event
        self.event_manager.trigger_event('punch_detected', punch_result, score, timestamp)

        print(f"PUNCH! Score: +{punch_result['total_points']}, Total: {punch_result['new_score']}, Combo: {punch_result['combo_count']}")

        # Trigger game state change event (AccelerometerStrategy will handle broadcasting)
        game_state = self.game_state.get_state_dict()
        self.event_manager.trigger_event('game_state_changed', game_state)
    
    def run(self):
        """Main game loop with event-driven architecture"""
        print("Starting Punch Detection Game...")

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

                # Trigger drawing phase events (strategies handle their own drawing)
                self.event_manager.trigger_event('draw_overlays', frame)

                # Draw core game UI (score, combo, instructions, effects)
                self.ui_manager.draw_game_ui(
                    frame,
                    self.game_state,
                    evaluation_mode=self.evaluation_mode,
                    is_recording=self.recording_manager.is_recording(),
                    recording_time=self.recording_manager.get_recording_time()
                )

                # Trigger strategy UI drawing with position context for chaining
                draw_context = {'next_y': STRATEGY_UI_START_Y, 'x': STRATEGY_UI_START_X}
                self.event_manager.trigger_event_chain('draw_ui', draw_context, frame)

                # Display frame
                cv2.imshow('Punch Detection Game', frame)

                # Pass frame to recording manager
                if self.recording_manager.is_recording():
                    self.recording_manager.record_frame(frame)

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
                elif key == ord('e'):
                    # Toggle evaluation mode
                    self.toggle_evaluation_mode()
                elif key == ord(' '):
                    # Manual punch trigger for testing (only during PLAYING)
                    if self.game_state.is_playing():
                        self.register_punch(1.0, time.time())

        except KeyboardInterrupt:
            print("\nGame interrupted by user")

        finally:
            # Cleanup recording if active
            self.recording_manager.cleanup()

            # Trigger cleanup event for all components
            self.event_manager.trigger_event('cleanup')
            if self.cap:
                self.cap.release()
                self.cap = None
            cv2.destroyAllWindows()
            print(f"\nFinal Score: {self.game_state.get_score()}")
            print(f"Total Punches: {self.game_state.get_punch_count()}")

if __name__ == "__main__":
    game = PunchDetectionGame()
    game.run()