"""
Plot from JSON - Saves plots to folder with JSON filename
"""

import os
import json
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict


FINGER_NAMES = ["IndexFinger", "MiddleFinger", "RingFinger", "LittleFinger", "Thumb", "Palm"]
COMPONENT_NAMES = ["AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"]


def transform_value(val, is_accelerometer):
    """Transform raw sensor value to physical units"""
    try:
        val = float(val)
        if is_accelerometer:
            if val >= 32768:
                return (val - 65536) / 4096.0
            else:
                return val / 4096.0
        else:
            if val >= 32768:
                return (val - 65536) / 32.8
            else:
                return val / 32.8
    except:
        return None


def flatten_hand_data(nested_list):
    """Flatten nested list structure"""
    result = []
    if isinstance(nested_list, list):
        for item in nested_list:
            if isinstance(item, list):
                if len(item) == 36 and all(isinstance(x, (int, float)) for x in item):
                    result.append(item)
                else:
                    result.extend(flatten_hand_data(item))
    return result


def parse_hand_data(hand_data_list):
    """Parse hand data into structured format"""
    parsed = []
    for arr in hand_data_list:
        frame_data = {}
        for i, finger in enumerate(FINGER_NAMES):
            start_idx = i * 6
            for j, comp in enumerate(COMPONENT_NAMES):
                key = f"{finger}_{comp}"
                frame_data[key] = arr[start_idx + j]
        parsed.append(frame_data)
    return parsed


def load_gesture_data(json_file):
    """Load gesture data from JSON file"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    metadata = {
        'session_name': data.get('session_name', 'Unknown'),
        'user_name': data.get('user_name', 'Unknown'),
        'gesture_name': data.get('custom_name', os.path.splitext(os.path.basename(json_file))[0]),
        'timestamp': data.get('timestamp', 'Unknown'),
        'device_name': data.get('device_name', {})
    }
    
    gesture_recording = data.get('gesture_recording', {})
    left_hand_data = gesture_recording.get('leftHandDataList', [[]])[0]
    right_hand_data = gesture_recording.get('rightHandDataList', [[]])[0]
    
    print(f"\n{'='*70}")
    print(f"Loaded: {os.path.basename(json_file)}")
    print(f"{'='*70}")
    print(f"User: {metadata['user_name']}")
    print(f"Session: {metadata['session_name']}")
    print(f"Gesture: {metadata['gesture_name']}")
    print(f"Left frames: {len(left_hand_data)}")
    print(f"Right frames: {len(right_hand_data)}")
    print(f"{'='*70}")
    
    return metadata, left_hand_data, right_hand_data


def convert_frame_data(raw_frames):
    """Convert raw frames to physical units"""
    converted_data = {finger: {'acc': [], 'gyro': []} for finger in FINGER_NAMES}
    
    for frame in raw_frames:
        if len(frame) != 36:
            continue
        
        for finger_idx, finger in enumerate(FINGER_NAMES):
            start_idx = finger_idx * 6
            
            acc = [
                transform_value(frame[start_idx], True),
                transform_value(frame[start_idx + 1], True),
                transform_value(frame[start_idx + 2], True)
            ]
            
            gyro = [
                transform_value(frame[start_idx + 3], False),
                transform_value(frame[start_idx + 4], False),
                transform_value(frame[start_idx + 5], False)
            ]
            
            converted_data[finger]['acc'].append(acc)
            converted_data[finger]['gyro'].append(gyro)
    
    return converted_data


def plot_single_finger_window(finger_name, left_data, right_data, metadata):
    """Create window for single finger (2x2 grid)"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.canvas.manager.set_window_title(f'{finger_name} - {metadata["gesture_name"]}')
    
    fig.suptitle(f"{finger_name} - {metadata['gesture_name']} (User: {metadata['user_name']})", 
                 fontsize=14, fontweight='bold')
    
    left_acc = np.array(left_data[finger_name]['acc'])
    left_gyro = np.array(left_data[finger_name]['gyro'])
    right_acc = np.array(right_data[finger_name]['acc'])
    right_gyro = np.array(right_data[finger_name]['gyro'])
    
    # Top-left: Left Hand Accelerometer
    ax = axes[0, 0]
    if len(left_acc) > 0:
        frames = range(len(left_acc))
        ax.plot(frames, left_acc[:, 0], 'r-', label='AccX', linewidth=1.5)
        ax.plot(frames, left_acc[:, 1], 'g-', label='AccY', linewidth=1.5)
        ax.plot(frames, left_acc[:, 2], 'b-', label='AccZ', linewidth=1.5)
    ax.set_title('Left Hand - Accelerometer (g)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Frame', fontsize=9)
    ax.set_ylabel('Acceleration (g)', fontsize=9)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)
    
    # Top-right: Left Hand Gyroscope
    ax = axes[0, 1]
    if len(left_gyro) > 0:
        frames = range(len(left_gyro))
        ax.plot(frames, left_gyro[:, 0], 'orange', label='GyroX', linewidth=1.5)
        ax.plot(frames, left_gyro[:, 1], 'purple', label='GyroY', linewidth=1.5)
        ax.plot(frames, left_gyro[:, 2], 'brown', label='GyroZ', linewidth=1.5)
    ax.set_title('Left Hand - Gyroscope (°/s)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Frame', fontsize=9)
    ax.set_ylabel('Angular Velocity (°/s)', fontsize=9)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)
    
    # Bottom-left: Right Hand Accelerometer
    ax = axes[1, 0]
    if len(right_acc) > 0:
        frames = range(len(right_acc))
        ax.plot(frames, right_acc[:, 0], 'r-', label='AccX', linewidth=1.5)
        ax.plot(frames, right_acc[:, 1], 'g-', label='AccY', linewidth=1.5)
        ax.plot(frames, right_acc[:, 2], 'b-', label='AccZ', linewidth=1.5)
    ax.set_title('Right Hand - Accelerometer (g)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Frame', fontsize=9)
    ax.set_ylabel('Acceleration (g)', fontsize=9)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)
    
    # Bottom-right: Right Hand Gyroscope
    ax = axes[1, 1]
    if len(right_gyro) > 0:
        frames = range(len(right_gyro))
        ax.plot(frames, right_gyro[:, 0], 'orange', label='GyroX', linewidth=1.5)
        ax.plot(frames, right_gyro[:, 1], 'purple', label='GyroY', linewidth=1.5)
        ax.plot(frames, right_gyro[:, 2], 'brown', label='GyroZ', linewidth=1.5)
    ax.set_title('Right Hand - Gyroscope (°/s)', fontsize=11, fontweight='bold')
    ax.set_xlabel('Frame', fontsize=9)
    ax.set_ylabel('Angular Velocity (°/s)', fontsize=9)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    return fig


def plot_all_fingers_from_json(json_file, show_plots=True, save_plots=True):
    """
    Plot all 6 fingers from JSON file
    
    Args:
        json_file: Path to JSON file
        show_plots: If True, display plots on screen
        save_plots: If True, save plots to folder (named after JSON file)
    """
    
    # Load data
    metadata, left_raw, right_raw = load_gesture_data(json_file)
    
    # Convert to physical units
    print(f"\nConverting sensor data to physical units...")
    left_data = convert_frame_data(left_raw)
    right_data = convert_frame_data(right_raw)
    
    # Get plot folder (same name as JSON file)
    if save_plots:
        from data_processor import DataProcessor
        plot_folder = DataProcessor(metadata['session_name'], metadata['user_name']).get_plot_folder(json_file)
        print(f"\nPlots will be saved to: {plot_folder}")
    else:
        plot_folder = None
    
    # Plot each finger
    print(f"\nGenerating plots for 6 fingers...")
    
    for finger in FINGER_NAMES:
        print(f"  Processing {finger}...")
        fig = plot_single_finger_window(finger, left_data, right_data, metadata)
        
        # Save plot
        if save_plots and plot_folder:
            filename = f"{finger}.png"
            filepath = os.path.join(plot_folder, filename)
            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"    ✓ Saved: {filename}")
        
        # Show plot
        if show_plots:
            plt.show(block=False)
        else:
            plt.close(fig)
    
    if show_plots:
        print(f"\n✓ All 6 plots displayed!")
        print(f"  Close any window to continue...")
        plt.show()  # Block until windows closed
    
    if save_plots:
        print(f"\n✓ All plots saved to: {plot_folder}")
