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
        """Detect if user is facing front or side based on multiple factors"""
        try:
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            nose = landmarks[self.mp_pose.PoseLandmark.NOSE.value]

            # Calculate shoulder width (primary factor)
            shoulder_width = abs(left_shoulder.x - right_shoulder.x)

            # Calculate nose position relative to shoulders (secondary factor)
            shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
            nose_offset = abs(nose.x - shoulder_center_x)

            # Calculate shoulder visibility (tertiary factor)
            # Both shoulders should be visible and roughly at same depth for front-facing
            shoulder_z_diff = abs(left_shoulder.z - right_shoulder.z) if hasattr(left_shoulder, 'z') and hasattr(right_shoulder, 'z') else 0

            # Multi-factor scoring system
            front_score = 0

            # Factor 1: Shoulder width (lowered threshold, more generous)
            if shoulder_width > FRONT_FACING_SHOULDER_THRESHOLD:
                front_score += 2
            elif shoulder_width > FRONT_FACING_SHOULDER_THRESHOLD * 0.7:  # More lenient
                front_score += 1

            # Factor 2: Nose alignment (should be centered between shoulders)
            if nose_offset < shoulder_width * 0.3:  # Nose close to shoulder center
                front_score += 1

            # Factor 3: Shoulder depth similarity (both shoulders at similar Z depth)
            if shoulder_z_diff < 0.1:  # Similar depth = front-facing
                front_score += 1

            # Factor 4: Minimum shoulder visibility
            if shoulder_width > 0.08:  # Very basic visibility check
                front_score += 1

            # Decision: Need at least 3 out of 5 points to be considered front-facing
            orientation = "front" if front_score >= 3 else "side"

            return orientation

        except Exception as e:
            print(f"Error in orientation detection: {e}")
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

    def _calculate_z_velocity(self, current_landmarks):
        """Calculate Z-axis velocity based on wrist extension relative to shoulders (punch biomechanics)"""
        try:
            # Get current positions
            left_wrist = current_landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
            right_wrist = current_landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
            left_shoulder = current_landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = current_landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

            # Get previous positions
            prev_left_wrist = self.prev_landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
            prev_right_wrist = self.prev_landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
            prev_left_shoulder = self.prev_landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            prev_right_shoulder = self.prev_landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

            # Calculate relative Z-distances (wrist forward of shoulder = punch extension)
            current_left_extension = left_wrist.z - left_shoulder.z
            current_right_extension = right_wrist.z - right_shoulder.z
            prev_left_extension = prev_left_wrist.z - prev_left_shoulder.z
            prev_right_extension = prev_right_wrist.z - prev_right_shoulder.z

            # Calculate changes in punch extension
            left_extension_change = abs(current_left_extension - prev_left_extension)
            right_extension_change = abs(current_right_extension - prev_right_extension)

            # Calculate time difference
            current_time = time.time()
            time_diff = current_time - self.prev_timestamp
            if time_diff <= 0:
                return 0

            # Calculate extension velocities (how fast the punch is extending)
            left_extension_velocity = left_extension_change / time_diff
            right_extension_velocity = right_extension_change / time_diff

            # Use maximum extension velocity (most active hand)
            max_extension_velocity = max(left_extension_velocity, right_extension_velocity)

            # Apply smoothing to reduce noise
            if hasattr(self, 'extension_velocity_history'):
                self.extension_velocity_history.append(max_extension_velocity)
                if len(self.extension_velocity_history) > 3:  # Keep last 3 measurements (faster response)
                    self.extension_velocity_history.pop(0)
                # Return smoothed velocity
                smoothed_velocity = sum(self.extension_velocity_history) / len(self.extension_velocity_history)
                return smoothed_velocity
            else:
                # Initialize smoothing history
                self.extension_velocity_history = [max_extension_velocity]
                return max_extension_velocity

        except Exception as e:
            print(f"Error calculating punch extension velocity: {e}")
            return 0

    def analyze_front_facing(self, landmarks, velocity):
        """Analyze front-facing punches using biomechanics (extension) + X/Y filtering"""
        try:
            left_wrist = landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value]
            right_wrist = landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value]
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

            # Calculate lateral (X-axis) and vertical (Y-axis) movements for filtering
            left_lateral = abs(left_wrist.x - left_shoulder.x)
            right_lateral = abs(right_wrist.x - right_shoulder.x)
            left_vertical = abs(left_wrist.y - left_shoulder.y)
            right_vertical = abs(right_wrist.y - right_shoulder.y)

            max_lateral = max(left_lateral, right_lateral)
            max_vertical = max(left_vertical, right_vertical)

            # Calculate punch extension velocity (primary signal)
            extension_velocity = 0
            if self.prev_landmarks:
                extension_velocity = self._calculate_z_velocity(landmarks)

            # X/Y Movement Filter: Reject if too much lateral/vertical movement
            # Clean front punches should have minimal X/Y movement
            lateral_filter = 1.0 if max_lateral < 0.15 else max(0.3, 1.0 - (max_lateral - 0.15) * 3)
            vertical_filter = 1.0 if max_vertical < 0.15 else max(0.3, 1.0 - (max_vertical - 0.15) * 3)
            movement_filter = min(lateral_filter, vertical_filter)

            # Primary score based on punch extension velocity
            extension_score = min(extension_velocity / PUNCH_VELOCITY_THRESHOLD, 1.0) if extension_velocity > 0 else 0

            # Apply movement filter to reduce false positives
            filtered_score = extension_score * movement_filter * FRONT_VELOCITY_MULTIPLIER

            return min(filtered_score, 1.0)
        except Exception as e:
            print(f"Error in front-facing analysis: {e}")
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