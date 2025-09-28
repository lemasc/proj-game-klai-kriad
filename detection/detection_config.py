# Detection Configuration Constants
# These values control the sensitivity and behavior of punch detection algorithms

# Accelerometer Detection Settings
ACCEL_PUNCH_THRESHOLD = 20.0  # m/s² - Minimum acceleration magnitude to trigger punch detection
ACCEL_SCORING_MAX = 40.0  # m/s² - Maximum acceleration for score normalization

# Pose Detection Settings
VISUAL_PUNCH_THRESHOLD = 0.3  # Minimum pose score to trigger punch detection
POSE_ARM_EXTENSION_WEIGHT = 0.7  # Weight for arm extension in pose analysis
POSE_FORWARD_MOVEMENT_WEIGHT = 0.3  # Weight for forward movement in pose analysis
POSE_SCORE_MULTIPLIER = 2.0  # Multiplier to boost pose scores

# Fusion Logic Settings
ACCEL_WEIGHT = 0.7  # Weight of accelerometer data in combined score
VISUAL_WEIGHT = 0.3  # Weight of pose data in combined score
MINIMUM_COMBINED_SCORE = 0.2  # Minimum combined score to register as punch
PUNCH_TRIGGER_ACCEL_THRESHOLD = 0.3  # Min accelerometer score to trigger punch

# Timing Settings
PUNCH_COOLDOWN = 0.5  # Seconds between punch detections to prevent false positives

# MediaPipe Configuration
MP_MIN_DETECTION_CONFIDENCE = 0.5
MP_MIN_TRACKING_CONFIDENCE = 0.5
MP_MODEL_COMPLEXITY = 1

# Data Buffer Settings
SENSOR_BUFFER_SIZE = 10  # Maximum number of sensor readings to keep
POSE_BUFFER_SIZE = 10  # Maximum number of pose readings to keep