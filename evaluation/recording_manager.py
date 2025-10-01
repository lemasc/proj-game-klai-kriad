"""Manages recording of game sessions for evaluation."""

import json
import cv2
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from evaluation import recording_config as config


class RecordingManager:
    """Handles recording of video, sensor data, and detection events."""

    def __init__(self, event_manager):
        """Initialize the recording manager.

        Args:
            event_manager: Game event manager for subscribing to events
        """
        self.event_manager = event_manager
        self.is_recording_flag = False
        self.session_dir: Optional[Path] = None
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.start_time: Optional[float] = None
        self.frame_count = 0

        # Buffers for JSONL files
        self.detection_buffer: List[Dict] = []
        self.sensor_buffer: List[Dict] = []

        # Metadata tracking
        self.session_metadata: Dict[str, Any] = {}

        # Subscribe to game events
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """Subscribe to relevant game events."""
        # Listen for punch detections
        self.event_manager.register_hook(
            'punch_detected',
            self._on_punch_detected
        )

        # Listen for sensor data (if available)
        self.event_manager.register_hook(
            'sensor_data_received',
            self._on_sensor_data
        )

    def start_recording(self, resolution: tuple, fps: int,
                       detection_config: Optional[Dict] = None) -> bool:
        """Start a new recording session.

        Args:
            resolution: (width, height) of video frames
            fps: Frames per second
            detection_config: Current detection configuration snapshot

        Returns:
            True if recording started successfully, False otherwise
        """
        if self.is_recording_flag:
            print("Already recording!")
            return False

        # Create session directory
        timestamp = datetime.now().strftime(config.TIMESTAMP_FORMAT)
        session_id = f"session_{timestamp}"
        self.session_dir = config.RECORDINGS_DIR / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Initialize video writer
        video_path = self.session_dir / config.VIDEO_FILENAME
        fourcc = cv2.VideoWriter_fourcc(*config.VIDEO_CODEC)
        self.video_writer = cv2.VideoWriter(
            str(video_path),
            fourcc,
            fps,
            resolution
        )

        if not self.video_writer.isOpened():
            print(f"Failed to open video writer at {video_path}")
            return False

        # Initialize session metadata
        self.start_time = time.time()
        self.frame_count = 0
        self.session_metadata = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "fps": fps,
            "resolution": list(resolution),
            "detection_config": detection_config or {},
            "strategies": []  # Will be populated from detection events
        }

        # Clear buffers
        self.detection_buffer.clear()
        self.sensor_buffer.clear()

        self.is_recording_flag = True
        print(f"Recording started: {session_id}")
        return True

    def stop_recording(self) -> Optional[Path]:
        """Stop the current recording session.

        Returns:
            Path to the session directory, or None if not recording
        """
        if not self.is_recording_flag:
            return None

        # Flush buffers
        self._flush_detections()
        self._flush_sensor_data()

        # Release video writer
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None

        # Finalize metadata
        if self.start_time:
            duration = time.time() - self.start_time
            self.session_metadata["duration_seconds"] = round(duration, 2)
            self.session_metadata["total_frames"] = self.frame_count

        # Write metadata file
        metadata_path = self.session_dir / config.METADATA_FILENAME
        with open(metadata_path, 'w') as f:
            json.dump(self.session_metadata, f, indent=2)

        session_dir = self.session_dir
        print(f"Recording stopped: {session_dir.name}")
        print(f"Duration: {self.session_metadata.get('duration_seconds', 0):.1f}s")
        print(f"Frames: {self.frame_count}")

        # Reset state
        self.is_recording_flag = False
        self.session_dir = None
        self.start_time = None
        self.frame_count = 0

        return session_dir

    def record_frame(self, frame) -> bool:
        """Record a video frame.

        Args:
            frame: OpenCV frame (numpy array)

        Returns:
            True if frame was recorded, False otherwise
        """
        if not self.is_recording_flag or not self.video_writer:
            return False

        self.video_writer.write(frame)
        self.frame_count += 1
        return True

    def _on_punch_detected(self, punch_result: Dict[str, Any], score: float, event_timestamp: float):
        """Handle punch detection event.

        Args:
            punch_result: Dictionary with punch registration details
            score: Punch strength/quality score
            event_timestamp: Timestamp of the punch
        """
        if not self.is_recording_flag:
            return

        timestamp = time.time() - self.start_time if self.start_time else 0

        # Extract relevant data
        detection_record = {
            "timestamp": round(timestamp, 3),
            "frame": self.frame_count,
            "type": "punch",
            "hand": punch_result.get("hand", "unknown"),
            "confidence": score,
            "punch_result": {
                "base_points": punch_result.get("base_points", 0),
                "combo_bonus": punch_result.get("combo_bonus", 0),
                "total_points": punch_result.get("total_points", 0),
                "combo_count": punch_result.get("combo_count", 0),
            }
        }

        # Include strategy scores if available
        if "strategy_scores" in punch_result:
            detection_record["strategy_scores"] = punch_result["strategy_scores"]

        # Include accelerometer data if available
        if "accel_data" in punch_result:
            detection_record["accel_data"] = punch_result["accel_data"]

        # Track strategies used
        for strategy in punch_result.get("strategy_scores", {}).keys():
            if strategy not in self.session_metadata.get("strategies", []):
                self.session_metadata.setdefault("strategies", []).append(strategy)

        self.detection_buffer.append(detection_record)

        # Flush buffer if full
        if len(self.detection_buffer) >= config.BUFFER_SIZE:
            self._flush_detections()

    def _on_sensor_data(self, event_data: Dict[str, Any]):
        """Handle sensor data event.

        Args:
            event_data: Event data containing sensor readings
        """
        if not self.is_recording_flag:
            return

        timestamp = time.time() - self.start_time if self.start_time else 0

        sensor_record = {
            "timestamp": round(timestamp, 3),
            "accel": event_data.get("accel", {}),
            "gyro": event_data.get("gyro", {})
        }

        self.sensor_buffer.append(sensor_record)

        # Flush buffer if full
        if len(self.sensor_buffer) >= config.BUFFER_SIZE:
            self._flush_sensor_data()

    def _flush_detections(self):
        """Write detection buffer to file."""
        if not self.detection_buffer or not self.session_dir:
            return

        detections_path = self.session_dir / config.DETECTIONS_FILENAME
        with open(detections_path, 'a') as f:
            for detection in self.detection_buffer:
                f.write(json.dumps(detection) + '\n')

        self.detection_buffer.clear()

    def _flush_sensor_data(self):
        """Write sensor data buffer to file."""
        if not self.sensor_buffer or not self.session_dir:
            return

        sensor_path = self.session_dir / config.SENSOR_DATA_FILENAME
        with open(sensor_path, 'a') as f:
            for sensor in self.sensor_buffer:
                f.write(json.dumps(sensor) + '\n')

        self.sensor_buffer.clear()

    def is_recording(self) -> bool:
        """Check if currently recording.

        Returns:
            True if recording is active, False otherwise
        """
        return self.is_recording_flag

    def get_recording_time(self) -> float:
        """Get current recording duration in seconds.

        Returns:
            Duration in seconds, or 0 if not recording
        """
        if not self.is_recording_flag or not self.start_time:
            return 0.0
        return time.time() - self.start_time

    def cleanup(self):
        """Clean up resources."""
        if self.is_recording_flag:
            self.stop_recording()
