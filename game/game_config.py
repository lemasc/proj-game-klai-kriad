# Game Configuration Constants
# These values control game mechanics, scoring, and user interface behavior

# Combo System Settings
COMBO_TIMEOUT = 2.0  # Seconds - Time window for consecutive punches to count as combo
COMBO_BONUS_POINTS = 10  # Points added per combo level

# Scoring Settings
BASE_SCORE_MULTIPLIER = 100  # Converts punch score (0-1) to points (0-100)

# Visual Effects Settings
PUNCH_EFFECT_DURATION = 0.3  # Seconds - How long the punch effect displays
PUNCH_EFFECT_ALPHA = 0.3  # Transparency level for screen flash effect

# UI Display Settings
UI_BACKGROUND_COLOR = (0, 0, 0)  # Black background for UI panel
UI_BORDER_COLOR = (255, 255, 255)  # White border for UI panel
UI_PANEL_POSITION = (10, 10)  # Top-left position of UI panel
UI_PANEL_SIZE = (400, 120)  # Width and height of UI panel

# Text Colors
SCORE_COLOR = (0, 255, 0)  # Green for score display
NORMAL_TEXT_COLOR = (255, 255, 255)  # White for normal text
COMBO_COLOR = (0, 255, 255)  # Cyan for combo display
PUNCH_TEXT_COLOR = (0, 0, 255)  # Red for "PUNCH!" text
INSTRUCTION_COLOR = (255, 255, 0)  # Yellow for instructions
SENSOR_CONNECTED_COLOR = (0, 255, 0)  # Green for connected sensor
SENSOR_DISCONNECTED_COLOR = (0, 0, 255)  # Red for disconnected sensor

# Camera Settings
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_INDEX = 0  # Default camera device index

# Flask Server Settings
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5000
FLASK_SECRET_KEY = 'punch-detection-secret'