"""Configuration for the recording system."""

import os
from pathlib import Path

# Recording directories
RECORDINGS_DIR = Path("recordings")
RECORDINGS_DIR.mkdir(exist_ok=True)

# Video settings
VIDEO_CODEC = "mp4v"  # or 'avc1' for H.264, 'XVID' for AVI
VIDEO_EXTENSION = ".mp4"
VIDEO_FPS = 30  # Target FPS for recording (will match game FPS)

# File names
VIDEO_FILENAME = "video.mp4"
METADATA_FILENAME = "metadata.json"
DETECTIONS_FILENAME = "detections.jsonl"
SENSOR_DATA_FILENAME = "sensor_data.jsonl"
LABELS_FILENAME = "labels.json"

# Recording settings
BUFFER_SIZE = 100  # Number of lines to buffer before writing to JSONL files
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# UI settings
RECORDING_INDICATOR_COLOR = (0, 0, 255)  # Red in BGR
RECORDING_INDICATOR_RADIUS = 10
RECORDING_INDICATOR_POSITION = (30, 30)  # Top-left corner
EVALUATION_MODE_TEXT_POSITION = (30, 60)
EVALUATION_MODE_COLOR = (0, 165, 255)  # Orange in BGR
