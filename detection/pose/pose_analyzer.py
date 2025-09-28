import mediapipe as mp
import time
import math
from detection.detection_config import (
    POSE_ARM_EXTENSION_WEIGHT,
    POSE_FORWARD_MOVEMENT_WEIGHT,
    POSE_SCORE_MULTIPLIER,
    PUNCH_VELOCITY_THRESHOLD,
    FRONT_FACING_SHOULDER_THRESHOLD,
    FRONT_VELOCITY_MULTIPLIER,
    SIDE_FORWARD_MULTIPLIER
)


class PoseAnalyzer:
    """Analyzes pose landmarks for punch-like movements"""

    def __init__(self):
        """Initialize the pose analyzer"""
        self.mp_pose = mp.solutions.pose
        self.prev_landmarks = None
        self.prev_timestamp = None

    def analyze_pose_punch(self, landmarks):
        """
        Analyze pose landmarks for punch-like movements

        Args:
            landmarks: MediaPipe pose landmarks

        Returns:
            tuple: (punch_score, metrics) where punch_score is 0-1 and metrics contains analysis details
        """
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

            # Detect user orientation
            orientation = self.detect_orientation(landmarks)

            # Calculate velocity if we have previous data
            current_timestamp = time.time()
            velocity_score = 0
            if self.prev_landmarks is not None:
                velocity_score = self.calculate_movement_velocity(landmarks, current_timestamp)

            # Analyze based on orientation
            if orientation == "front":
                movement_score = self.analyze_front_facing(landmarks, velocity_score)
            else:  # side-facing
                movement_score = self.analyze_side_facing(landmarks, velocity_score)

            # Combine extension and movement scores
            punch_score = (max_extension * POSE_ARM_EXTENSION_WEIGHT + movement_score * POSE_FORWARD_MOVEMENT_WEIGHT) * POSE_SCORE_MULTIPLIER
            punch_score = min(punch_score, 1.0)

            # Store current data for next velocity calculation
            self.prev_landmarks = landmarks
            self.prev_timestamp = current_timestamp

            metrics = {
                'left_extension': left_arm_extension,
                'right_extension': right_arm_extension,
                'max_extension': max_extension,
                'movement_score': movement_score,
                'velocity_score': velocity_score,
                'orientation': orientation,
                'punch_score': punch_score
            }

            return punch_score, metrics

        except Exception as e:
            print(f"Error analyzing pose: {e}")
            return 0, {}

    def detect_orientation(self, landmarks):
        """Detect if user is facing front or side based on shoulder width"""
        try:
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

            shoulder_width = abs(left_shoulder.x - right_shoulder.x)

            # Wide shoulders = front-facing, narrow = side-facing
            if shoulder_width > FRONT_FACING_SHOULDER_THRESHOLD:
                return "front"
            else:
                return "side"
        except:
            return "front"  # Default to front-facing

    def calculate_movement_velocity(self, current_landmarks, current_timestamp):
        """Calculate wrist movement velocity"""
        try:
            # Get current wrist positions
            left_wrist = current_landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
            right_wrist = current_landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]

            # Get previous wrist positions
            prev_left_wrist = self.prev_landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
            prev_right_wrist = self.prev_landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]

            # Calculate distances moved
            left_distance = math.sqrt(
                (left_wrist.x - prev_left_wrist.x)**2 +
                (left_wrist.y - prev_left_wrist.y)**2
            )
            right_distance = math.sqrt(
                (right_wrist.x - prev_right_wrist.x)**2 +
                (right_wrist.y - prev_right_wrist.y)**2
            )

            # Calculate time difference
            time_diff = current_timestamp - self.prev_timestamp
            if time_diff <= 0:
                return 0

            # Calculate velocities and return maximum
            left_velocity = left_distance / time_diff
            right_velocity = right_distance / time_diff

            return max(left_velocity, right_velocity)
        except:
            return 0

    def analyze_front_facing(self, landmarks, velocity):
        """Analyze movement for front-facing user using velocity + X/Y analysis"""
        try:
            left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

            # Calculate lateral (X-axis) and vertical (Y-axis) movements
            left_lateral = abs(left_wrist.x - left_shoulder.x)
            right_lateral = abs(right_wrist.x - right_shoulder.x)
            left_vertical = abs(left_wrist.y - left_shoulder.y)
            right_vertical = abs(right_wrist.y - right_shoulder.y)

            # Get maximum movements
            max_lateral = max(left_lateral, right_lateral)
            max_vertical = max(left_vertical, right_vertical)

            # Combine position-based and velocity-based scores
            position_score = max(max_lateral, max_vertical)
            velocity_component = min(velocity / PUNCH_VELOCITY_THRESHOLD, 1.0) if velocity > 0 else 0

            # Weight velocity more heavily for front-facing detection
            movement_score = (position_score * 0.4 + velocity_component * 0.6) * FRONT_VELOCITY_MULTIPLIER
            return min(movement_score, 1.0)
        except:
            return 0

    def analyze_side_facing(self, landmarks, velocity):
        """Analyze movement for side-facing user using reliable X-axis forward detection"""
        try:
            left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

            # X-axis forward movement (most reliable for side-facing)
            left_forward = abs(left_wrist.x - left_shoulder.x)
            right_forward = abs(right_wrist.x - right_shoulder.x)

            # Y-axis vertical movement (uppercuts)
            left_vertical = abs(left_wrist.y - left_shoulder.y)
            right_vertical = abs(right_wrist.y - right_shoulder.y)

            # Get maximum movements
            max_forward = max(left_forward, right_forward)
            max_vertical = max(left_vertical, right_vertical)

            # Emphasize forward movement for side-facing users
            position_score = max(max_forward * SIDE_FORWARD_MULTIPLIER, max_vertical)
            velocity_component = min(velocity / PUNCH_VELOCITY_THRESHOLD, 1.0) if velocity > 0 else 0

            # Combine position and velocity
            movement_score = max(position_score * 0.5 + velocity_component * 0.5, velocity_component)
            return min(movement_score, 1.0)
        except:
            return 0