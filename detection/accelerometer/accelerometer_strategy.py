"""
Accelerometer detection strategy that manages sensor server and motion analysis.
This strategy handles its own dependencies and lifecycle through event hooks.
"""

import cv2
import math
import queue
import time
from collections import deque
from typing import Optional, Dict, Any
from detection.base_strategy import BaseDetectionStrategy
from detection.accelerometer.sensor_server import SensorServer
from detection.accelerometer.motion_analyzer import MotionAnalyzer
from detection.detection_config import ACCEL_PUNCH_THRESHOLD
from detection.detection_config import SENSOR_BUFFER_SIZE
from game.event_manager import EventManager
from game.game_config import (
    SENSOR_CONNECTED_COLOR,
    SENSOR_DISCONNECTED_COLOR,
    NORMAL_TEXT_COLOR,
    FLASK_SECRET_KEY,
    SERVER_HOST,
    SERVER_PORT,
    ENABLE_NGROK,
    NGROK_AUTH_TOKEN
)


class AccelerometerStrategy(BaseDetectionStrategy):
    """
    Detection strategy for smartphone accelerometer data.

    Manages Flask server lifecycle, receives sensor data, and analyzes motion
    for punch detection. Results are stored internally and accessed by FusionDetector.
    """

    def __init__(self, event_manager: EventManager, game_state_provider=None, recording_manager=None):
        """
        Initialize accelerometer strategy.

        Args:
            event_manager: Event manager for registering hooks
            game_state_provider: Function that returns current game state
            recording_manager: Optional RecordingManager instance for ground truth logging
        """
        self.sensor_server: Optional[SensorServer] = None
        self.motion_analyzer: Optional[MotionAnalyzer] = None
        self.game_state_provider = game_state_provider
        self.recording_manager = recording_manager

        # Internal sensor data queue and buffer
        self.sensor_queue = queue.Queue()
        self.sensor_data_buffer = deque(maxlen=SENSOR_BUFFER_SIZE)

        # Latest sensor data and analysis results
        self.latest_sensor_data: Optional[Dict] = None
        self.latest_analysis: Optional[Dict] = None

        super().__init__(event_manager)

    def register_hooks(self) -> None:
        """Register event hooks for accelerometer strategy."""
        self.event_manager.register_hook('setup', self.setup_server, priority=10)
        self.event_manager.register_hook('process_sensor_queue', self.process_sensor_queue, priority=10)
        self.event_manager.register_hook('game_state_changed', self.handle_game_state_update, priority=10)
        self.event_manager.register_hook('draw_ui', self.draw_strategy_ui, priority=10)
        self.event_manager.register_hook('cleanup', self.cleanup_server, priority=10)

    def setup_server(self) -> None:
        """Initialize accelerometer server and motion analyzer."""
        try:
            # Initialize motion analyzer
            self.motion_analyzer = MotionAnalyzer(ACCEL_PUNCH_THRESHOLD)

            # Create sensor server
            print("AccelerometerStrategy: Starting sensor server...")
            class ServerConfig:
                FLASK_SECRET_KEY = FLASK_SECRET_KEY
                SERVER_HOST = SERVER_HOST
                SERVER_PORT = SERVER_PORT
                ENABLE_NGROK = ENABLE_NGROK
                NGROK_AUTH_TOKEN = NGROK_AUTH_TOKEN

            self.sensor_server = SensorServer(
                sensor_data_callback=self._handle_sensor_data,
                game_state_provider=self.game_state_provider or self._default_game_state_provider,
                config=ServerConfig(),
                recording_manager=self.recording_manager
            )
            self.sensor_server.start()
            print("AccelerometerStrategy: Sensor server started")

            self.activate()
            print("AccelerometerStrategy: Initialized successfully")

        except Exception as e:
            print(f"AccelerometerStrategy: Error during setup: {e}")
            self.deactivate()

    def cleanup_server(self) -> None:
        """Clean up sensor server and release resources."""
        try:
            if self.sensor_server and self.sensor_server.is_running():
                print("AccelerometerStrategy: Stopping sensor server...")
                # Note: SensorServer doesn't have a stop method, but it runs in daemon thread
                # so it will be cleaned up automatically when main thread exits

            self.deactivate()
            self.latest_sensor_data = None
            self.latest_analysis = None
            print("AccelerometerStrategy: Cleanup completed")

        except Exception as e:
            print(f"AccelerometerStrategy: Error during cleanup: {e}")

    def process_sensor_queue(self) -> Optional[Dict[str, Any]]:
        """
        Process queued sensor data from internal queue.

        Returns:
            Latest sensor data processed, or None if no data available
        """
        if not self.is_strategy_active() or not self.motion_analyzer:
            return None

        current_sensor_data = None

        # Get latest sensor data from queue
        while not self.sensor_queue.empty():
            try:
                current_sensor_data = self.sensor_queue.get_nowait()
                self.sensor_data_buffer.append(current_sensor_data)
            except queue.Empty:
                break

        # Process the latest sensor data if available
        if current_sensor_data:
            self._analyze_sensor_data(current_sensor_data)

        return current_sensor_data

    def _analyze_sensor_data(self, sensor_data: Dict[str, Any]) -> None:
        """
        Analyze sensor data for punch detection.

        Args:
            sensor_data: Dictionary containing accelerometer data (x, y, z, timestamp)
        """
        try:
            # Store latest sensor data
            self.latest_sensor_data = sensor_data

            # Analyze accelerometer data for punch detection
            punch_score, metrics = self.motion_analyzer.analyze_accelerometer_punch(sensor_data)

            # Update results with analysis
            analysis_result = {
                'score': punch_score,
                'is_confident': punch_score > ACCEL_PUNCH_THRESHOLD,
                'metrics': metrics,
                'sensor_data': sensor_data,
                'timestamp': time.time(),
                'strategy': 'accelerometer'
            }

            self.latest_analysis = analysis_result
            self.update_results(analysis_result)

        except Exception as e:
            print(f"AccelerometerStrategy: Error analyzing sensor data: {e}")

    def handle_game_state_update(self, game_state: Dict[str, Any]) -> None:
        """
        Handle game state changes by broadcasting to connected clients.

        Args:
            game_state: Updated game state dictionary
        """
        if self.is_strategy_active() and self.sensor_server:
            try:
                self.sensor_server.emit_game_update(game_state)
            except Exception as e:
                print(f"AccelerometerStrategy: Error broadcasting game state: {e}")

    def _handle_sensor_data(self, data: Dict[str, Any]) -> int:
        """
        Internal sensor data callback that queues incoming sensor data.

        Args:
            data: Sensor data from smartphone

        Returns:
            Queue size for monitoring
        """
        self.sensor_queue.put(data)
        return self.sensor_queue.qsize()

    def _default_game_state_provider(self) -> Dict[str, Any]:
        """
        Default game state provider if none is provided.

        Returns:
            Basic game state dictionary
        """
        return {
            'score': 0,
            'punch_count': 0,
            'combo_count': 0,
            'last_punch_score': 0
        }

    def get_latest_sensor_data(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent sensor data received.

        Returns:
            Latest sensor data or None if no data available
        """
        return self.latest_sensor_data

    def get_analysis_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed analysis metrics from the latest processing.

        Returns:
            Analysis metrics or None if no analysis available
        """
        return self.latest_analysis.get('metrics') if self.latest_analysis else None

    def is_server_running(self) -> bool:
        """
        Check if the sensor server is running.

        Returns:
            True if server is running, False otherwise
        """
        return self.sensor_server is not None and self.sensor_server.is_running()

    def has_connected_clients(self) -> bool:
        """
        Check if there are any connected WebSocket clients.

        Returns:
            True if clients are connected, False otherwise
        """
        return self.sensor_server is not None and self.sensor_server.has_connected_clients()

    def get_connected_client_count(self) -> int:
        """
        Get the number of connected WebSocket clients.

        Returns:
            Number of connected clients
        """
        return self.sensor_server.get_connected_client_count() if self.sensor_server else 0

    def draw_strategy_ui(self, draw_context: Dict[str, Any], image) -> Dict[str, Any]:
        """
        Draw accelerometer-specific UI elements on the frame.

        This method is called via the draw_ui event and uses the chained context
        to determine where to draw. It updates the context with the next available
        position for subsequent handlers.

        Args:
            draw_context: Dictionary containing drawing position and state
            image: OpenCV image to draw on

        Returns:
            Updated context dictionary with next available position
        """
        if not self.is_strategy_active():
            return draw_context

        # Extract position from context
        start_y = draw_context.get('next_y', 40)
        x = draw_context.get('x', 220)
        current_y = start_y

        # Draw sensor connection status
        is_connected = self.has_connected_clients()
        status_color = SENSOR_CONNECTED_COLOR if is_connected else SENSOR_DISCONNECTED_COLOR
        status_text = "Sensor: Connected" if is_connected else "Sensor: Disconnected"
        cv2.putText(image, status_text, (x, current_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2)
        current_y += 30

        # Draw debug info if sensor data is available
        if self.latest_sensor_data:
            try:
                accel_mag = math.sqrt(
                    self.latest_sensor_data.get('x', 0)**2 +
                    self.latest_sensor_data.get('y', 0)**2 +
                    self.latest_sensor_data.get('z', 0)**2
                )
                cv2.putText(image, f"Accel: {accel_mag:.1f}", (x, current_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, NORMAL_TEXT_COLOR, 1)
                current_y += 30
            except (TypeError, ValueError):
                # Handle invalid sensor data gracefully
                pass

        # Return updated context with next available position
        return {'next_y': current_y, 'x': x}

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about this strategy's status.

        Returns:
            Dictionary containing strategy status information
        """
        base_info = super().get_strategy_info()
        base_info.update({
            'server_running': self.is_server_running(),
            'has_connected_clients': self.has_connected_clients(),
            'connected_client_count': self.get_connected_client_count(),
            'has_sensor_data': self.latest_sensor_data is not None,
            'has_analysis': self.latest_analysis is not None,
            'motion_analyzer_ready': self.motion_analyzer is not None
        })
        return base_info