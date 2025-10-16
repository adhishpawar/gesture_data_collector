"""
Live Plotter - 6 Separate Windows (One per finger)
Each window: 2x2 grid (Left Acc, Left Gyro, Right Acc, Right Gyro)
Simple version - works reliably
"""

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict
from collections import deque


FINGER_NAMES = ["IndexFinger", "MiddleFinger", "RingFinger", "LittleFinger", "Thumb", "Palm"]
COMPONENT_NAMES = ["AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"]


class FingerWindow:
    """Single window for one finger (2x2 grid)"""
    
    def __init__(self, finger_name: str):
        self.finger_name = finger_name
        self.fig = None
        self.axes = None
        self.lines = {}
        self.max_frames = 200  # X-axis display limit
        
        # Track TOTAL frames (doesn't reset)
        self.total_frames = {
            'left_acc': 0,
            'left_gyro': 0,
            'right_acc': 0,
            'right_gyro': 0
        }
        
        # Data storage (keeps last 500 for memory efficiency)
        self.data = {
            'left_acc': deque(maxlen=500),
            'left_gyro': deque(maxlen=500),
            'right_acc': deque(maxlen=500),
            'right_gyro': deque(maxlen=500)
        }
        
        self._init_window()
    
    def _init_window(self):
        """Initialize 2x2 subplot window"""
        self.fig, self.axes = plt.subplots(2, 2, figsize=(14, 10))
        self.fig.canvas.manager.set_window_title(f'{self.finger_name} - Live Data')
        self.fig.suptitle(f'{self.finger_name} - Real-time Sensor Data', 
                         fontsize=14, fontweight='bold')
        
        # Top-left: Left Hand Accelerometer
        ax_left_acc = self.axes[0, 0]
        ax_left_acc.set_title('Left Hand - Accelerometer (g)', fontsize=11, fontweight='bold')
        ax_left_acc.set_xlabel('Frame', fontsize=9)
        ax_left_acc.set_ylabel('Acceleration (g)', fontsize=9)
        ax_left_acc.grid(True, alpha=0.3)
        ax_left_acc.set_xlim(0, self.max_frames)
        ax_left_acc.set_ylim(-4, 4)
        
        # Top-right: Left Hand Gyroscope
        ax_left_gyro = self.axes[0, 1]
        ax_left_gyro.set_title('Left Hand - Gyroscope (°/s)', fontsize=11, fontweight='bold')
        ax_left_gyro.set_xlabel('Frame', fontsize=9)
        ax_left_gyro.set_ylabel('Angular Velocity (°/s)', fontsize=9)
        ax_left_gyro.grid(True, alpha=0.3)
        ax_left_gyro.set_xlim(0, self.max_frames)
        ax_left_gyro.set_ylim(-200, 200)
        
        # Bottom-left: Right Hand Accelerometer
        ax_right_acc = self.axes[1, 0]
        ax_right_acc.set_title('Right Hand - Accelerometer (g)', fontsize=11, fontweight='bold')
        ax_right_acc.set_xlabel('Frame', fontsize=9)
        ax_right_acc.set_ylabel('Acceleration (g)', fontsize=9)
        ax_right_acc.grid(True, alpha=0.3)
        ax_right_acc.set_xlim(0, self.max_frames)
        ax_right_acc.set_ylim(-4, 4)
        
        # Bottom-right: Right Hand Gyroscope
        ax_right_gyro = self.axes[1, 1]
        ax_right_gyro.set_title('Right Hand - Gyroscope (°/s)', fontsize=11, fontweight='bold')
        ax_right_gyro.set_xlabel('Frame', fontsize=9)
        ax_right_gyro.set_ylabel('Angular Velocity (°/s)', fontsize=9)
        ax_right_gyro.grid(True, alpha=0.3)
        ax_right_gyro.set_xlim(0, self.max_frames)
        ax_right_gyro.set_ylim(-200, 200)
        
        # Create lines
        self.lines = {
            'left_acc': [
                ax_left_acc.plot([], [], label='AccX', color='red', linewidth=1.5)[0],
                ax_left_acc.plot([], [], label='AccY', color='green', linewidth=1.5)[0],
                ax_left_acc.plot([], [], label='AccZ', color='blue', linewidth=1.5)[0]
            ],
            'left_gyro': [
                ax_left_gyro.plot([], [], label='GyroX', color='orange', linewidth=1.5)[0],
                ax_left_gyro.plot([], [], label='GyroY', color='purple', linewidth=1.5)[0],
                ax_left_gyro.plot([], [], label='GyroZ', color='brown', linewidth=1.5)[0]
            ],
            'right_acc': [
                ax_right_acc.plot([], [], label='AccX', color='red', linewidth=1.5)[0],
                ax_right_acc.plot([], [], label='AccY', color='green', linewidth=1.5)[0],
                ax_right_acc.plot([], [], label='AccZ', color='blue', linewidth=1.5)[0]
            ],
            'right_gyro': [
                ax_right_gyro.plot([], [], label='GyroX', color='orange', linewidth=1.5)[0],
                ax_right_gyro.plot([], [], label='GyroY', color='purple', linewidth=1.5)[0],
                ax_right_gyro.plot([], [], label='GyroZ', color='brown', linewidth=1.5)[0]
            ]
        }
        
        # Add legends
        ax_left_acc.legend(loc='upper right', fontsize=8)
        ax_left_gyro.legend(loc='upper right', fontsize=8)
        ax_right_acc.legend(loc='upper right', fontsize=8)
        ax_right_gyro.legend(loc='upper right', fontsize=8)
        
        plt.tight_layout()
    
    def add_data(self, hand: str, acc_data: List[float], gyro_data: List[float]):
        """Add converted data for this finger"""
        storage_key = 'left' if hand == "Left" else 'right'
        
        if all(v is not None for v in acc_data):
            self.data[f'{storage_key}_acc'].append(acc_data)
            self.total_frames[f'{storage_key}_acc'] += 1
        
        if all(v is not None for v in gyro_data):
            self.data[f'{storage_key}_gyro'].append(gyro_data)
            self.total_frames[f'{storage_key}_gyro'] += 1
    
    def update(self):
        """Update all 4 plots in this window"""
        try:
            # Update Left Accelerometer
            if len(self.data['left_acc']) > 0:
                acc_array = np.array(list(self.data['left_acc']))
                total = self.total_frames['left_acc']
                
                if total > self.max_frames:
                    start_frame = total - self.max_frames
                    end_frame = total
                    display_data = acc_array[-self.max_frames:]
                else:
                    start_frame = 0
                    end_frame = total
                    display_data = acc_array
                
                frames = list(range(start_frame, end_frame))
                
                for i in range(3):
                    self.lines['left_acc'][i].set_data(frames, display_data[:, i])
                
                self.axes[0, 0].set_xlim(start_frame, start_frame + self.max_frames)
                
                if display_data.size > 0:
                    ymin, ymax = display_data.min(), display_data.max()
                    margin = max(0.5, (ymax - ymin) * 0.15)
                    ymin_clamped = max(-16, ymin - margin)
                    ymax_clamped = min(16, ymax + margin)
                    self.axes[0, 0].set_ylim(ymin_clamped, ymax_clamped)
            
            # Update Left Gyroscope
            if len(self.data['left_gyro']) > 0:
                gyro_array = np.array(list(self.data['left_gyro']))
                total = self.total_frames['left_gyro']
                
                if total > self.max_frames:
                    start_frame = total - self.max_frames
                    end_frame = total
                    display_data = gyro_array[-self.max_frames:]
                else:
                    start_frame = 0
                    end_frame = total
                    display_data = gyro_array
                
                frames = list(range(start_frame, end_frame))
                
                for i in range(3):
                    self.lines['left_gyro'][i].set_data(frames, display_data[:, i])
                
                self.axes[0, 1].set_xlim(start_frame, start_frame + self.max_frames)
                
                if display_data.size > 0:
                    ymin, ymax = display_data.min(), display_data.max()
                    margin = max(20, (ymax - ymin) * 0.15)
                    ymin_clamped = max(-2000, ymin - margin)
                    ymax_clamped = min(2000, ymax + margin)
                    self.axes[0, 1].set_ylim(ymin_clamped, ymax_clamped)
            
            # Update Right Accelerometer
            if len(self.data['right_acc']) > 0:
                acc_array = np.array(list(self.data['right_acc']))
                total = self.total_frames['right_acc']
                
                if total > self.max_frames:
                    start_frame = total - self.max_frames
                    end_frame = total
                    display_data = acc_array[-self.max_frames:]
                else:
                    start_frame = 0
                    end_frame = total
                    display_data = acc_array
                
                frames = list(range(start_frame, end_frame))
                
                for i in range(3):
                    self.lines['right_acc'][i].set_data(frames, display_data[:, i])
                
                self.axes[1, 0].set_xlim(start_frame, start_frame + self.max_frames)
                
                if display_data.size > 0:
                    ymin, ymax = display_data.min(), display_data.max()
                    margin = max(0.5, (ymax - ymin) * 0.15)
                    ymin_clamped = max(-16, ymin - margin)
                    ymax_clamped = min(16, ymax + margin)
                    self.axes[1, 0].set_ylim(ymin_clamped, ymax_clamped)
            
            # Update Right Gyroscope
            if len(self.data['right_gyro']) > 0:
                gyro_array = np.array(list(self.data['right_gyro']))
                total = self.total_frames['right_gyro']
                
                if total > self.max_frames:
                    start_frame = total - self.max_frames
                    end_frame = total
                    display_data = gyro_array[-self.max_frames:]
                else:
                    start_frame = 0
                    end_frame = total
                    display_data = gyro_array
                
                frames = list(range(start_frame, end_frame))
                
                for i in range(3):
                    self.lines['right_gyro'][i].set_data(frames, display_data[:, i])
                
                self.axes[1, 1].set_xlim(start_frame, start_frame + self.max_frames)
                
                if display_data.size > 0:
                    ymin, ymax = display_data.min(), display_data.max()
                    margin = max(20, (ymax - ymin) * 0.15)
                    ymin_clamped = max(-2000, ymin - margin)
                    ymax_clamped = min(2000, ymax + margin)
                    self.axes[1, 1].set_ylim(ymin_clamped, ymax_clamped)
            
            # Redraw
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            
        except Exception as e:
            pass
    
    def clear(self):
        """Clear all data"""
        for key in self.data:
            self.data[key].clear()
        
        for key in self.total_frames:
            self.total_frames[key] = 0
        
        for key in self.lines:
            for line in self.lines[key]:
                line.set_data([], [])
    
    def show(self):
        """Show window"""
        plt.show(block=False)
    
    def close(self):
        """Close window"""
        if self.fig:
            plt.close(self.fig)


class LivePlotter:
    """Manages 6 separate finger windows"""
    
    def __init__(self):
        self.is_running = False
        self.finger_windows: Dict[str, FingerWindow] = {}
        self._first_frame_logged = {}
        
        # Initialize all finger windows
        for finger in FINGER_NAMES:
            self.finger_windows[finger] = FingerWindow(finger)
        
        plt.ion()  # Interactive mode
    
    def transform_value(self, val, is_accelerometer):
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
                
        except (ValueError, TypeError):
            return None
    
    def parse_frame_data(self, data: List[int]):
        """Parse 36-value frame into finger data"""
        if len(data) != 36:
            return None
        
        parsed = {}
        for i, finger in enumerate(FINGER_NAMES):
            start_idx = i * 6
            finger_data = {
                'acc_raw': [data[start_idx], data[start_idx+1], data[start_idx+2]],
                'gyro_raw': [data[start_idx+3], data[start_idx+4], data[start_idx+5]]
            }
            parsed[finger] = finger_data
        
        return parsed
    
    def add_data(self, hand: str, data: List[int]):
        """Add new data frame - distribute to all finger windows"""
        
        # Validate data
        if not data or len(data) == 0:
            return
        
        if all(v == 0 for v in data):
            return
        
        if len(data) != 36:
            return
        
        # Debug first frame
        if hand not in self._first_frame_logged:
            self._first_frame_logged[hand] = True
            print(f"\n{'='*70}")
            print(f"LIVE PLOT - First Frame ({hand})")
            print(f"{'='*70}")
            print(f"Raw (first 6): {data[:6]}")
            
            idx_acc_x = self.transform_value(data[0], True)
            idx_acc_y = self.transform_value(data[1], True)
            
            print(f"IndexFinger:")
            print(f"  AccX: {data[0]} → {idx_acc_x:.6f}g")
            print(f"  AccY: {data[1]} → {idx_acc_y:.6f}g")
            print(f"{'='*70}\n")
        
        # Parse frame data
        frame_data = self.parse_frame_data(data)
        
        if not frame_data:
            return
        
        # Process all fingers
        for finger in FINGER_NAMES:
            if finger not in frame_data:
                continue
            
            finger_raw = frame_data[finger]
            
            # Convert values
            acc_converted = [
                self.transform_value(finger_raw['acc_raw'][0], True),
                self.transform_value(finger_raw['acc_raw'][1], True),
                self.transform_value(finger_raw['acc_raw'][2], True)
            ]
            
            gyro_converted = [
                self.transform_value(finger_raw['gyro_raw'][0], False),
                self.transform_value(finger_raw['gyro_raw'][1], False),
                self.transform_value(finger_raw['gyro_raw'][2], False)
            ]
            
            # Add to corresponding finger window
            if all(v is not None for v in acc_converted) and all(v is not None for v in gyro_converted):
                self.finger_windows[finger].add_data(hand, acc_converted, gyro_converted)
        
        # Update displays (every 10 frames)
        if self.is_running:
            total_frames = (len(self.finger_windows['IndexFinger'].data['left_acc']) + 
                          len(self.finger_windows['IndexFinger'].data['right_acc']))
            
            if total_frames % 10 == 0:
                self._update_all_displays()
    
    def _update_all_displays(self):
        """Update all 6 finger windows"""
        for finger_window in self.finger_windows.values():
            finger_window.update()
    
    def start(self):
        """Start live plotting - show all 6 windows"""
        self.is_running = True
        
        # Clear all data and reset logging
        self._first_frame_logged = {}
        for finger_window in self.finger_windows.values():
            finger_window.clear()
        
        # Show all windows
        print("\n📊 Opening 6 finger windows...")
        for finger, window in self.finger_windows.items():
            window.show()
            print(f"   ✓ {finger} window opened")
        
        print("\n✅ All 6 windows active (X-axis: 200 frames max)")
        print("⚠️  Update rate: Every 10 frames\n")
    
    def stop(self):
        """Stop plotting"""
        self.is_running = False
        print("📊 Live plotting stopped")
    
    def clear(self):
        """Clear all data"""
        self._first_frame_logged = {}
        for finger_window in self.finger_windows.values():
            finger_window.clear()
    
    def close(self):
        """Close all windows"""
        self.is_running = False
        for finger_window in self.finger_windows.values():
            finger_window.close()
        print("📊 All windows closed")
