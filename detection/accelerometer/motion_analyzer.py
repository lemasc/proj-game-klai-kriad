import math
from detection.detection_config import ACCEL_SCORING_MAX


class MotionAnalyzer:
    """Analyzes accelerometer data for punch detection"""

    def __init__(self, accel_punch_threshold):
        """
        Initialize the motion analyzer

        Args:
            accel_punch_threshold (float): Threshold for detecting punches in m/s²
        """
        self.accel_punch_threshold = accel_punch_threshold

    def analyze_accelerometer_punch(self, sensor_data):
        """
        Analyze accelerometer data for punch detection

        Args:
            sensor_data (dict): Sensor data containing x, y, z acceleration values

        Returns:
            tuple: (punch_score, metrics) where punch_score is 0-1 and metrics contains analysis details
        """
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
                punch_score = min(magnitude_no_gravity / ACCEL_SCORING_MAX, 1.0)

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