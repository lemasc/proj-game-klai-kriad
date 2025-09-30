import cv2
import queue
import time
from collections import deque
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

class PunchDetectionGame:
    def __init__(self):
        # Event system
        self.event_manager = EventManager()

        # Camera setup
        self.cap = None

        # Game state
        self.game_state = GameState()

        # Data storage
        self.sensor_queue = queue.Queue()
        self.sensor_data_buffer = deque(maxlen=SENSOR_BUFFER_SIZE)  # Keep last 10 readings
        self.pose_data_buffer = deque(maxlen=POSE_BUFFER_SIZE)

        # Thresholds (adjust based on testing)
        self.accel_punch_threshold = ACCEL_PUNCH_THRESHOLD  # m/s²
        self.visual_punch_threshold = VISUAL_PUNCH_THRESHOLD
        self.punch_cooldown = PUNCH_COOLDOWN  # seconds between punches

        # UI Manager
        self.ui_manager = UIManager()

        # FusionDetector now uses event system
        self.fusion_detector = FusionDetector(self.event_manager)

        # Initialize detection strategies
        self._init_strategies()

        print("Detection strategies initialized")
        print("Open the smartphone web interface to connect accelerometer")

    def _init_strategies(self):
        """Initialize detection strategies and add them to fusion detector."""
        # Create server config for accelerometer strategy
        class ServerConfig:
            FLASK_SECRET_KEY = FLASK_SECRET_KEY
            SERVER_HOST = SERVER_HOST
            SERVER_PORT = SERVER_PORT
            ENABLE_NGROK = ENABLE_NGROK
            NGROK_AUTH_TOKEN = NGROK_AUTH_TOKEN

        config = ServerConfig()

        # Initialize accelerometer strategy
        self.accelerometer_strategy = AccelerometerStrategy(
            event_manager=self.event_manager,
            sensor_data_callback=self._handle_sensor_data,
            game_state_provider=self._get_game_state,
            config=config
        )

        # Initialize pose strategy
        self.pose_strategy = PoseStrategy(self.event_manager)

        # Add strategies to fusion detector with weights
        self.fusion_detector.add_strategy(self.accelerometer_strategy, weight=ACCEL_WEIGHT)
        self.fusion_detector.add_strategy(self.pose_strategy, weight=VISUAL_WEIGHT)

    def _handle_sensor_data(self, data):
        """Handle incoming sensor data from the server"""
        self.sensor_queue.put(data)
        return self.sensor_queue.qsize()

    def _get_game_state(self):
        """Provide current game state for the sensor server"""
        return self.game_state.get_state_dict()
    
    def process_sensor_data(self):
        """Process queued sensor data"""
        current_sensor_data = None
        
        # Get latest sensor data
        while not self.sensor_queue.empty():
            try:
                current_sensor_data = self.sensor_queue.get_nowait()
                self.sensor_data_buffer.append(current_sensor_data)
            except queue.Empty:
                break
        
        return current_sensor_data
    
    
    def register_punch(self, score, timestamp):
        """Register a successful punch and update game state"""
        punch_result = self.game_state.register_punch(score, timestamp)

        # Trigger punch detected event
        self.event_manager.trigger_event('punch_detected', punch_result, score, timestamp)

        print(f"PUNCH! Score: +{punch_result['total_points']}, Total: {punch_result['new_score']}, Combo: {punch_result['combo_count']}")

        # Trigger game state change event (AccelerometerStrategy will handle broadcasting)
        game_state = self.game_state.get_state_dict()
        self.event_manager.trigger_event('game_state_changed', game_state)
    
    def get_sensor_status(self):
        """Get current sensor connection status."""
        # Check if accelerometer strategy has connected WebSocket clients
        connected = False
        if hasattr(self, 'accelerometer_strategy') and self.accelerometer_strategy:
            connected = self.accelerometer_strategy.has_connected_clients()

        return {
            'connected': connected
        }
    
    def run(self):
        """Main game loop with event-driven architecture"""
        print("Starting Punch Detection Game...")
        print("Make sure to:")
        print("1. Connect your smartphone to the sensor interface")
        print("2. Stand in front of the camera")
        print("3. Start punching!")
        print("Press 'q' to quit, 'r' to reset score")

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

                # Process sensor data
                current_sensor_data = self.process_sensor_data()

                # Trigger sensor data event if data is available
                if current_sensor_data:
                    self.event_manager.trigger_event('sensor_data_received', current_sensor_data)

                # Detect punches using fusion detector (strategies provide results)
                is_punch, punch_score, metrics = self.fusion_detector.detect_punch()

                if is_punch:
                    self.register_punch(punch_score, time.time())
                    # Trigger visual effect
                    self.ui_manager.trigger_punch_effect()

                # Trigger drawing phase events (strategies handle their own drawing)
                self.event_manager.trigger_event('draw_overlays', frame)

                # Draw game UI
                sensor_status = self.get_sensor_status()
                self.ui_manager.draw_game_ui(frame, self.game_state, sensor_status, current_sensor_data)

                # Trigger UI drawing event
                self.event_manager.trigger_event('draw_ui', frame, self.game_state, sensor_status)

                # Display frame
                cv2.imshow('Punch Detection Game', frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    # Reset score
                    self.game_state.reset_score()
                    print("Score reset!")
                elif key == ord(' '):
                    # Manual punch trigger for testing
                    self.register_punch(1.0, time.time())

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

if __name__ == "__main__":
    game = PunchDetectionGame()
    game.run()