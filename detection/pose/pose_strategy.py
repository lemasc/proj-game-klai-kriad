"""
Pose detection strategy that manages MediaPipe pose processing and analysis.
This strategy handles its own MediaPipe lifecycle through event hooks.
"""

import time
import cv2
import mediapipe as mp
from typing import Optional, Dict, Any, List
from detection.base_strategy import BaseDetectionStrategy
from detection.pose.pose_analyzer import PoseAnalyzer
from detection.detection_config import (
    MP_MIN_DETECTION_CONFIDENCE,
    MP_MIN_TRACKING_CONFIDENCE,
    MP_MODEL_COMPLEXITY
)
from game.event_manager import EventManager


class PoseStrategy(BaseDetectionStrategy):
    """
    Detection strategy for MediaPipe pose detection and analysis.

    Manages MediaPipe pose detection lifecycle, processes camera frames,
    and analyzes pose landmarks for punch detection. Results are stored
    internally and accessed by FusionDetector.
    """

    def __init__(self, event_manager: EventManager):
        """
        Initialize pose strategy.

        Args:
            event_manager: Event manager for registering hooks
        """
        # MediaPipe components
        self.mp_pose: Optional[mp.solutions.pose] = None
        self.mp_drawing: Optional[mp.solutions.drawing_utils] = None
        self.pose: Optional[mp.solutions.pose.Pose] = None

        # Pose analyzer
        self.pose_analyzer: Optional[PoseAnalyzer] = None

        # Latest processing results
        self.latest_pose_results = None
        self.latest_landmarks: Optional[List] = None
        self.latest_analysis: Optional[Dict] = None

        super().__init__(event_manager)

    def register_hooks(self) -> None:
        """Register event hooks for pose strategy."""
        self.event_manager.register_hook('setup', self.setup_mediapipe, priority=10)
        self.event_manager.register_hook('frame_received', self.process_frame, priority=10)
        self.event_manager.register_hook('draw_overlays', self.draw_landmarks, priority=10)
        self.event_manager.register_hook('cleanup', self.cleanup_mediapipe, priority=10)

    def setup_mediapipe(self) -> None:
        """Initialize MediaPipe pose detection components."""
        try:
            print("PoseStrategy: Initializing MediaPipe...")

            # Initialize MediaPipe
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=MP_MODEL_COMPLEXITY,
                enable_segmentation=False,
                min_detection_confidence=MP_MIN_DETECTION_CONFIDENCE,
                min_tracking_confidence=MP_MIN_TRACKING_CONFIDENCE
            )

            # Initialize pose analyzer
            self.pose_analyzer = PoseAnalyzer()

            self.activate()
            print("PoseStrategy: MediaPipe initialized successfully")

        except Exception as e:
            print(f"PoseStrategy: Error during setup: {e}")
            self.deactivate()

    def cleanup_mediapipe(self) -> None:
        """Clean up MediaPipe resources."""
        try:
            if self.pose:
                self.pose.close()
                self.pose = None

            self.mp_pose = None
            self.mp_drawing = None
            self.pose_analyzer = None

            self.deactivate()
            self.latest_pose_results = None
            self.latest_landmarks = None
            self.latest_analysis = None

            print("PoseStrategy: MediaPipe cleanup completed")

        except Exception as e:
            print(f"PoseStrategy: Error during cleanup: {e}")

    def process_frame(self, frame) -> None:
        """
        Process camera frame and extract pose landmarks.

        Args:
            frame: OpenCV camera frame (BGR format)
        """
        if not self.is_strategy_active() or not self.pose or not self.pose_analyzer:
            return

        try:
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Process pose detection
            pose_results = self.pose.process(rgb_frame)

            # Store pose results for drawing
            self.latest_pose_results = pose_results

            # Extract and analyze landmarks if available
            if pose_results.pose_landmarks:
                landmarks = pose_results.pose_landmarks.landmark
                self.latest_landmarks = landmarks

                # Analyze pose for punch detection
                punch_score, metrics = self.pose_analyzer.analyze_pose_punch(landmarks)

                # Update results with analysis
                analysis_result = {
                    'score': punch_score,
                    'metrics': metrics,
                    'landmarks': landmarks,
                    'pose_results': pose_results,
                    'timestamp': time.time(),
                    'strategy': 'pose'
                }

                self.latest_analysis = analysis_result
                self.update_results(analysis_result)

            else:
                # No landmarks detected
                self.latest_landmarks = None
                no_pose_result = {
                    'score': 0,
                    'metrics': {'no_pose_detected': True},
                    'landmarks': None,
                    'pose_results': pose_results,
                    'timestamp': time.time(),
                    'strategy': 'pose'
                }
                self.latest_analysis = no_pose_result
                self.update_results(no_pose_result)

        except Exception as e:
            print(f"PoseStrategy: Error processing frame: {e}")

    def draw_landmarks(self, frame) -> None:
        """
        Draw pose landmarks on the frame.

        Args:
            frame: OpenCV frame to draw on
        """
        if not self.is_strategy_active() or not self.mp_drawing or not self.latest_pose_results:
            return

        try:
            if self.latest_pose_results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    self.latest_pose_results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS
                )
        except Exception as e:
            print(f"PoseStrategy: Error drawing landmarks: {e}")

    def get_latest_landmarks(self) -> Optional[List]:
        """
        Get the most recent pose landmarks.

        Returns:
            Latest pose landmarks or None if no landmarks available
        """
        return self.latest_landmarks

    def get_latest_pose_results(self):
        """
        Get the most recent MediaPipe pose results.

        Returns:
            Latest pose results or None if no results available
        """
        return self.latest_pose_results

    def get_analysis_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed analysis metrics from the latest processing.

        Returns:
            Analysis metrics or None if no analysis available
        """
        return self.latest_analysis.get('metrics') if self.latest_analysis else None

    def has_pose_detected(self) -> bool:
        """
        Check if a pose is currently detected.

        Returns:
            True if pose landmarks are available, False otherwise
        """
        return (self.latest_pose_results is not None and
                self.latest_pose_results.pose_landmarks is not None)

    def get_landmark_by_name(self, landmark_name: str) -> Optional[Any]:
        """
        Get a specific landmark by its MediaPipe name.

        Args:
            landmark_name: Name of the landmark (e.g., 'LEFT_WRIST')

        Returns:
            Landmark object or None if not available
        """
        if not self.latest_landmarks or not self.mp_pose:
            return None

        try:
            landmark_enum = getattr(self.mp_pose.PoseLandmark, landmark_name)
            return self.latest_landmarks[landmark_enum.value]
        except (AttributeError, IndexError):
            return None

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about this strategy's status.

        Returns:
            Dictionary containing strategy status information
        """
        base_info = super().get_strategy_info()
        base_info.update({
            'mediapipe_ready': self.pose is not None,
            'has_pose_detected': self.has_pose_detected(),
            'has_landmarks': self.latest_landmarks is not None,
            'has_analysis': self.latest_analysis is not None,
            'pose_analyzer_ready': self.pose_analyzer is not None
        })
        return base_info