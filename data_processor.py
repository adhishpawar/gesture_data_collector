"""
Data Processor - User-based folder structure
Organizes data by: data/User/Session/Gesture
"""

import os
import json
from datetime import datetime
from typing import List


class DataProcessor:
    """Handles data storage and organization"""
    
    def __init__(self, session_name: str, user_name: str):
        self.session_name = session_name
        self.user_name = user_name
        self.gesture_count = 0
        
        # Create folder structure: data/UserName/SessionName/
        self.base_folder = "data"
        self.user_folder = os.path.join(self.base_folder, self._sanitize_name(user_name))
        self.session_folder = os.path.join(self.user_folder, self._sanitize_name(session_name))
        
        # Create folders
        os.makedirs(self.session_folder, exist_ok=True)
        
        print(f"📁 Data will be saved to: {self.session_folder}")
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize folder/file names"""
        # Replace spaces with underscores, remove special chars
        sanitized = name.replace(" ", "_")
        sanitized = "".join(c for c in sanitized if c.isalnum() or c in ['_', '-'])
        return sanitized
    
    def save_gesture(
        self,
        left_data: List,
        right_data: List,
        left_device_id: str,
        right_device_id: str,
        custom_name: str = None
    ) -> str:
        """
        Save gesture data with timestamp-based naming
        
        Args:
            left_data: Left hand data frames
            right_data: Right hand data frames
            left_device_id: Left glove device ID
            right_device_id: Right glove device ID
            custom_name: Optional custom name (otherwise uses timestamp)
        
        Returns:
            Path to saved JSON file
        """
        
        self.gesture_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate filename
        if custom_name:
            # Use custom name + timestamp
            filename = f"{self._sanitize_name(custom_name)}_{timestamp}.json"
        else:
            # Use default timestamp-based name
            filename = f"gesture_{timestamp}.json"
        
        filepath = os.path.join(self.session_folder, filename)
        
        # Create data structure
        gesture_data = {
            "session_name": self.session_name,
            "user_name": self.user_name,
            "user_id": self._sanitize_name(self.user_name),
            "timestamp": datetime.now().isoformat(),
            "gesture_number": self.gesture_count,
            "custom_name": custom_name if custom_name else None,
            "device_name": {
                "leftHandDevice": left_device_id,
                "rightHandDevice": right_device_id
            },
            "gesture_recording": {
                "leftHandDataList": [left_data],
                "rightHandDataList": [right_data]
            }
        }
        
        # Save JSON file
        with open(filepath, 'w') as f:
            json.dump(gesture_data, f, indent=2)
        
        print(f"✓ JSON saved: {filename}")
        
        return filepath
    
    def get_plot_folder(self, json_filepath: str) -> str:
        """
        Get folder path for plots based on JSON filename
        Creates folder if it doesn't exist
        
        Args:
            json_filepath: Path to JSON file
        
        Returns:
            Path to plot folder
        """
        # Get JSON filename without extension
        json_filename = os.path.basename(json_filepath)
        folder_name = os.path.splitext(json_filename)[0]
        
        # Create plot folder in same directory as JSON
        json_dir = os.path.dirname(json_filepath)
        plot_folder = os.path.join(json_dir, folder_name)
        
        os.makedirs(plot_folder, exist_ok=True)
        
        return plot_folder
    
    def get_session_info(self) -> dict:
        """Get session information"""
        return {
            "session_name": self.session_name,
            "user_name": self.user_name,
            "gesture_count": self.gesture_count,
            "session_folder": self.session_folder,
            "user_folder": self.user_folder
        }
    
    @staticmethod
    def list_users(base_folder: str = "data") -> List[str]:
        """List all users"""
        if not os.path.exists(base_folder):
            return []
        
        users = [d for d in os.listdir(base_folder) 
                if os.path.isdir(os.path.join(base_folder, d))]
        return sorted(users)
    
    @staticmethod
    def list_user_sessions(user_name: str, base_folder: str = "data") -> List[str]:
        """List all sessions for a user"""
        user_folder = os.path.join(base_folder, user_name)
        
        if not os.path.exists(user_folder):
            return []
        
        sessions = [d for d in os.listdir(user_folder) 
                   if os.path.isdir(os.path.join(user_folder, d))]
        return sorted(sessions, reverse=True)
    
    @staticmethod
    def list_session_gestures(user_name: str, session_name: str, base_folder: str = "data") -> List[str]:
        """List all gesture JSON files in a session"""
        session_folder = os.path.join(base_folder, user_name, session_name)
        
        if not os.path.exists(session_folder):
            return []
        
        gestures = [f for f in os.listdir(session_folder) 
                   if f.endswith('.json')]
        return sorted(gestures)
