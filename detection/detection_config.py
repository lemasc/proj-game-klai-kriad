# Detection Configuration Constants
# These values control the sensitivity and behavior of punch detection algorithms

# Accelerometer Detection Settings
ACCEL_PUNCH_THRESHOLD = 20.0  # m/s² - Minimum acceleration magnitude to trigger punch detection
ACCEL_SCORING_MAX = 40.0  # m/s² - Maximum acceleration for score normalization

# Pose Detection Settings
VISUAL_PUNCH_THRESHOLD = 0.3  # Minimum pose score to trigger punch detection
POSE_ARM_EXTENSION_WEIGHT = 0.8  # Weight for arm extension in pose analysis
POSE_FORWARD_MOVEMENT_WEIGHT = 0.2  # Weight for forward movement in pose analysis
POSE_SCORE_MULTIPLIER = 2.0  # Multiplier to boost pose scores

# Velocity-based Detection Settings
PUNCH_VELOCITY_THRESHOLD = 2.0  # m/s minimum punch speed
VELOCITY_WEIGHT = 0.6  # Weight for velocity in scoring
POSITION_WEIGHT = 0.4  # Weight for position in scoring

# Orientation Detection Settings
FRONT_FACING_SHOULDER_THRESHOLD = 0.3  # Min shoulder width for front detection
SIDE_FACING_CONFIDENCE_THRESHOLD = 0.7  # Min confidence for side detection

# Movement Analysis Settings (no Z-axis)
FRONT_VELOCITY_MULTIPLIER = 1.0    # Movement speed multiplier (front-facing)
SIDE_FORWARD_MULTIPLIER = 1.2      # Forward movement boost (side-facing)
LATERAL_MOVEMENT_WEIGHT = 0.8      # Weight for lateral movement detection

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