import cv2
import mediapipe as mp
import numpy as np
import threading
import queue
import time
import json
import websockets
import asyncio
from collections import deque
import math

class PunchDetectionGame:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Game state
        self.score = 0
        self.punch_count = 0
        self.combo_count = 0
        self.last_punch_time = 0
        self.combo_timeout = 2.0  # seconds
        
        # Data storage
        self.sensor_queue = queue.Queue()
        self.sensor_data_buffer = deque(maxlen=10)  # Keep last 10 readings
        self.pose_data_buffer = deque(maxlen=10)
        
        # Thresholds (adjust based on testing)
        self.accel_punch_threshold = 20.0  # m/s²
        self.visual_punch_threshold = 0.3
        self.punch_cooldown = 0.5  # seconds between punches
        
        # Visual elements
        self.punch_effect_timer = 0
        self.punch_effect_duration = 0.3

        # WebSocket connection tracking
        self.connected_clients = set()
        self.connection_lock = threading.Lock()
        
        print("Starting WebSocket sensor server...")
        self.start_websocket_server()
        print("WebSocket sensor server will start on port 5000")
        print("Connect your smartphone app via WebSocket to ws://[IP]:5000")
    
    def start_websocket_server(self):
        """Start WebSocket server to receive sensor data from smartphone"""

        async def handle_websocket(websocket):
            """Handle WebSocket connections and messages"""
            try:
                print(f"New WebSocket connection from {websocket.remote_address}")

                # Add client to connected set
                with self.connection_lock:
                    self.connected_clients.add(websocket)

                async for message in websocket:
                    try:
                        data = json.loads(message)

                        # Handle different message types
                        if data.get('type') == 'sensor':
                            # Add timestamp if not present
                            if 'timestamp' not in data:
                                data['timestamp'] = time.time() * 1000

                            self.sensor_queue.put(data)

                            # Send acknowledgment with current status
                            response = {
                                'type': 'ack',
                                'status': 'ok',
                                'queue_size': self.sensor_queue.qsize()
                            }
                            await websocket.send(json.dumps(response))

                        elif data.get('type') == 'status_request':
                            # Send current game status
                            response = {
                                'type': 'status',
                                'connected': True,
                                'score': self.score,
                                'punches': self.punch_count,
                                'combo': self.combo_count
                            }
                            await websocket.send(json.dumps(response))

                    except json.JSONDecodeError:
                        print(f"Invalid JSON received: {message}")
                    except Exception as e:
                        print(f"Error processing message: {e}")

            except websockets.exceptions.ConnectionClosed:
                print(f"WebSocket connection closed: {websocket.remote_address}")
            except Exception as e:
                print(f"WebSocket error: {e}")
            finally:
                # Remove client from connected set
                with self.connection_lock:
                    self.connected_clients.discard(websocket)

        # Start WebSocket server in background thread
        def run_websocket_server():
            async def start_server_async():
                server = await websockets.serve(
                    handle_websocket,
                    "0.0.0.0",
                    5000,
                    ping_interval=30,
                    ping_timeout=10
                )
                print("WebSocket server started on port 5000")
                await server.wait_closed()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(start_server_async())

        server_thread = threading.Thread(target=run_websocket_server, daemon=True)
        server_thread.start()
    
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
    
    def analyze_accelerometer_punch(self, sensor_data):
        """Analyze accelerometer data for punch detection"""
        if not sensor_data:
            return 0, {}
        
        try:
            x, y, z = sensor_data.get('x', 0), sensor_data.get('y', 0), sensor_data.get('z', 0)
            
            # Calculate acceleration magnitude
            magnitude = math.sqrt(x**2 + y**2 + z**2)
            
            # Remove gravity (approximate)
            magnitude_no_gravity = abs(magnitude - 9.81)
            
            # Calculate punch score based on acceleration
            punch_score = 0
            if magnitude_no_gravity > self.accel_punch_threshold:
                # Normalize score (0-1)
                punch_score = min(magnitude_no_gravity / 40.0, 1.0)
            
            # Additional metrics
            metrics = {
                'magnitude': magnitude,
                'magnitude_no_gravity': magnitude_no_gravity,
                'x': x, 'y': y, 'z': z,
                'punch_score': punch_score
            }
            
            return punch_score, metrics
            
        except Exception as e:
            print(f"Error analyzing accelerometer data: {e}")
            return 0, {}
    
    def analyze_pose_punch(self, landmarks):
        """Analyze pose landmarks for punch-like movements"""
        if not landmarks:
            return 0, {}
        
        try:
            # Get key landmarks
            left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            left_elbow = landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value]
            right_elbow = landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value]
            
            # Calculate arm extension (simplified)
            left_arm_extension = abs(left_wrist.x - left_shoulder.x)
            right_arm_extension = abs(right_wrist.x - right_shoulder.x)
            max_extension = max(left_arm_extension, right_arm_extension)
            
            # Calculate forward movement (using Y coordinate change)
            left_forward = abs(left_wrist.y - left_shoulder.y)
            right_forward = abs(right_wrist.y - right_shoulder.y)
            max_forward = max(left_forward, right_forward)
            
            # Simple punch score based on extension and forward movement
            punch_score = (max_extension * 0.7 + max_forward * 0.3) * 2
            punch_score = min(punch_score, 1.0)
            
            metrics = {
                'left_extension': left_arm_extension,
                'right_extension': right_arm_extension,
                'max_extension': max_extension,
                'forward_movement': max_forward,
                'punch_score': punch_score
            }
            
            return punch_score, metrics
            
        except Exception as e:
            print(f"Error analyzing pose: {e}")
            return 0, {}
    
    def detect_punch(self, pose_landmarks, sensor_data):
        """Main punch detection combining both visual and accelerometer data"""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_punch_time < self.punch_cooldown:
            return False, 0, {}
        
        # Analyze both data sources
        accel_score, accel_metrics = self.analyze_accelerometer_punch(sensor_data)
        visual_score, visual_metrics = self.analyze_pose_punch(pose_landmarks)
        
        # Combine scores (weighted average)
        combined_score = (accel_score * 0.7 + visual_score * 0.3)
        
        # Determine if it's a punch
        is_punch = (accel_score > 0.3) or (visual_score > self.visual_punch_threshold)
        
        if is_punch and combined_score > 0.2:
            self.register_punch(combined_score, current_time)
            
            # Visual effect
            self.punch_effect_timer = current_time
            
            return True, combined_score, {
                'accel_metrics': accel_metrics,
                'visual_metrics': visual_metrics,
                'combined_score': combined_score
            }
        
        return False, combined_score, {
            'accel_metrics': accel_metrics,
            'visual_metrics': visual_metrics,
            'combined_score': combined_score
        }
    
    def register_punch(self, score, timestamp):
        """Register a successful punch and update game state"""
        self.punch_count += 1
        
        # Calculate score based on punch quality
        points = int(score * 100)
        
        # Combo system
        if timestamp - self.last_punch_time < self.combo_timeout:
            self.combo_count += 1
            # Bonus points for combos
            points += self.combo_count * 10
        else:
            self.combo_count = 1
        
        self.score += points
        self.last_punch_time = timestamp
        
        print(f"PUNCH! Score: +{points}, Total: {self.score}, Combo: {self.combo_count}")
    
    def draw_game_ui(self, image):
        """Draw game UI elements on the image"""
        height, width = image.shape[:2]
        
        # Background for UI elements
        cv2.rectangle(image, (10, 10), (400, 120), (0, 0, 0), -1)
        cv2.rectangle(image, (10, 10), (400, 120), (255, 255, 255), 2)
        
        # Score display
        cv2.putText(image, f"Score: {self.score}", (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Punch count
        cv2.putText(image, f"Punches: {self.punch_count}", (20, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Combo display
        combo_color = (0, 255, 255) if self.combo_count > 1 else (255, 255, 255)
        cv2.putText(image, f"Combo: {self.combo_count}x", (20, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, combo_color, 2)
        
        # Connection status
        with self.connection_lock:
            is_connected = len(self.connected_clients) > 0
            client_count = len(self.connected_clients)

        status_color = (0, 255, 0) if is_connected else (0, 0, 255)
        if is_connected:
            status_text = f"WebSocket: {client_count} client{'s' if client_count != 1 else ''}"
        else:
            status_text = "WebSocket: Disconnected"
        cv2.putText(image, status_text, (220, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2)
        
        # Punch effect
        current_time = time.time()
        if current_time - self.punch_effect_timer < self.punch_effect_duration:
            # Flash effect
            alpha = 1.0 - (current_time - self.punch_effect_timer) / self.punch_effect_duration
            overlay = image.copy()
            cv2.rectangle(overlay, (0, 0), (width, height), (0, 255, 0), -1)
            cv2.addWeighted(overlay, alpha * 0.3, image, 1.0, 0, image)
            
            # "PUNCH!" text
            text_size = cv2.getTextSize("PUNCH!", cv2.FONT_HERSHEY_SIMPLEX, 2, 3)[0]
            text_x = (width - text_size[0]) // 2
            text_y = (height + text_size[1]) // 2
            cv2.putText(image, "PUNCH!", (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
        
        # Instructions
        if self.punch_count == 0:
            instructions = [
                "1. Open smartphone web interface",
                "2. Start punching while holding phone",
                "3. Face the camera for best results"
            ]
            for i, instruction in enumerate(instructions):
                cv2.putText(image, instruction, (20, height - 80 + i * 25), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    def run(self):
        """Main game loop"""
        print("Starting Punch Detection Game...")
        print("Make sure to:")
        print("1. Connect your smartphone to the sensor interface")
        print("2. Stand in front of the camera")
        print("3. Start punching!")
        print("Press 'q' to quit, 'r' to reset score")
        
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Could not read frame")
                    break
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Convert to RGB for MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process pose
                pose_results = self.pose.process(rgb_frame)
                
                # Process sensor data
                current_sensor_data = self.process_sensor_data()
                
                # Detect punches
                if pose_results.pose_landmarks:
                    landmarks = pose_results.pose_landmarks.landmark
                    is_punch, punch_score, metrics = self.detect_punch(landmarks, current_sensor_data)
                    
                    # Draw pose landmarks
                    self.mp_drawing.draw_landmarks(
                        frame, pose_results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
                
                # Draw game UI
                self.draw_game_ui(frame)
                
                # Show debug info
                if current_sensor_data:
                    accel_mag = math.sqrt(
                        current_sensor_data.get('x', 0)**2 + 
                        current_sensor_data.get('y', 0)**2 + 
                        current_sensor_data.get('z', 0)**2
                    )
                    cv2.putText(frame, f"Accel: {accel_mag:.1f}", (220, 70), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Display frame
                cv2.imshow('Punch Detection Game', frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    # Reset score
                    self.score = 0
                    self.punch_count = 0
                    self.combo_count = 0
                    print("Score reset!")
                elif key == ord(' '):
                    # Manual punch trigger for testing
                    self.register_punch(1.0, time.time())
        
        except KeyboardInterrupt:
            print("\nGame interrupted by user")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print(f"\nFinal Score: {self.score}")
            print(f"Total Punches: {self.punch_count}")

if __name__ == "__main__":
    game = PunchDetectionGame()
    game.run()