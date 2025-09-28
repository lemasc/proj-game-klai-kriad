import mediapipe as mp
from detection.detection_config import (
    POSE_ARM_EXTENSION_WEIGHT,
    POSE_FORWARD_MOVEMENT_WEIGHT,
    POSE_SCORE_MULTIPLIER
)


class PoseAnalyzer:
    """Analyzes pose landmarks for punch-like movements"""

    def __init__(self):
        """Initialize the pose analyzer"""
        self.mp_pose = mp.solutions.pose

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

            # Calculate forward movement (using Y coordinate change)
            left_forward = abs(left_wrist.y - left_shoulder.y)
            right_forward = abs(right_wrist.y - right_shoulder.y)
            max_forward = max(left_forward, right_forward)

            # Simple punch score based on extension and forward movement
            punch_score = (max_extension * POSE_ARM_EXTENSION_WEIGHT + max_forward * POSE_FORWARD_MOVEMENT_WEIGHT) * POSE_SCORE_MULTIPLIER
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