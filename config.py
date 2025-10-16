"""
Configuration for BLE Gesture Data Collector
"""

# BLE Service and Characteristic UUIDs
SERVICE_UUID = "000000ee-0000-1000-8000-00805f9b34fb"
CHAR_CONTROL_UUID = "0000ee01-0000-1000-8000-00805f9b34fb"
CHAR_DATA_UUID = "0000ff01-0000-1000-8000-00805f9b34fb"

# BLE Settings
MTU_SIZE = 512
SCAN_DURATION = 10
CONNECTION_TIMEOUT = 20.0
MAX_CONNECTION_RETRIES = 3
MAX_SCAN_RETRIES = 2

# Device Identification
# Auto-detect devices with "Glovatrix" in name
LEFT_DEVICE_NAME_PATTERN = "Glovatrix"  # Will match any Glovatrix device
RIGHT_DEVICE_NAME_PATTERN = "Glovatrix"

# Data Settings
EXPECTED_FRAME_LENGTH = 36  # 6 fingers × 6 values
DATA_INTERVAL_MS = 15

# File Settings
SESSION_FOLDER = "sessions"
LOG_FOLDER = "logs"

# Button trigger byte
BUTTON_TRIGGER = 64

# Control commands
CMD_START_BROADCAST = [0x01, 0x01]
CMD_STOP_BROADCAST = [0x01, 0x02]
