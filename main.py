"""
Gesture Data Collector - Simplified Edition v2.0
User-based folder structure: data/User/Session/Gesture
"""

import asyncio
import sys
import os
import time
from datetime import datetime
from colorama import init, Fore, Style
from bleak import BleakScanner
from ble_manager import BLEManager
from data_processor import DataProcessor
from plot_from_json import plot_all_fingers_from_json
import config

# Initialize colorama
init(autoreset=True)


class GestureCollectorApp:
    def __init__(self):
        self.ble_manager = BLEManager()
        self.data_processor: DataProcessor = None
        self.recording_active = False
        self.session_name = ""
        self.user_name = ""
        self.connected = False
        self.last_button_time = 0
        self.gesture_counter = 0
    
    def print_header(self):
        """Print application header"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Fore.CYAN + Style.BRIGHT + "╔" + "═"*68 + "╗")
        print(Fore.CYAN + Style.BRIGHT + "║" + " "*68 + "║")
        print(Fore.CYAN + Style.BRIGHT + "║" + "      GESTURE DATA COLLECTOR v2.0".center(68) + "║")
        print(Fore.CYAN + Style.BRIGHT + "║" + "      Easy Recording & Visualization Tool".center(68) + "║")
        print(Fore.CYAN + Style.BRIGHT + "║" + " "*68 + "║")
        print(Fore.CYAN + Style.BRIGHT + "╚" + "═"*68 + "╝")
    
    async def main_menu(self):
        """Main menu loop - simplified"""
        while True:
            self.print_header()
            
            if not self.connected:
                # NOT CONNECTED MENU
                print(Fore.YELLOW + "\n📍 STATUS: " + Fore.RED + "Not Connected")
                print(Fore.CYAN + "\n┌" + "─"*68 + "┐")
                print(Fore.CYAN + "│" + "  MAIN MENU".ljust(68) + "│")
                print(Fore.CYAN + "├" + "─"*68 + "┤")
                print(Fore.WHITE + "│  " + Fore.GREEN + "1" + Fore.WHITE + " │ Connect to Gloves & Start Session".ljust(68) + "│")
                print(Fore.WHITE + "│  " + Fore.BLUE + "2" + Fore.WHITE + " │ View Saved Data (Browse & Plot)".ljust(68) + "│")
                print(Fore.WHITE + "│  " + Fore.RED + "3" + Fore.WHITE + " │ Exit Application".ljust(68) + "│")
                print(Fore.CYAN + "└" + "─"*68 + "┘")
                
                choice = input(Fore.WHITE + "\n👉 Enter your choice (1-3): ").strip()
                
                if choice == "1":
                    await self.setup_and_connect()
                elif choice == "2":
                    self.view_saved_data_menu()
                elif choice == "3":
                    self.exit_application()
                else:
                    print(Fore.RED + "\n❌ Invalid choice! Press Enter to try again...")
                    input()
            
            else:
                # CONNECTED MENU
                print(Fore.YELLOW + "\n📍 STATUS: " + Fore.GREEN + "✓ Connected")
                print(Fore.WHITE + f"   User: {Fore.CYAN}{self.user_name}")
                print(Fore.WHITE + f"   Session: {Fore.CYAN}{self.session_name}")
                print(Fore.WHITE + f"   Gestures Recorded: {Fore.CYAN}{self.gesture_counter}")
                
                print(Fore.CYAN + "\n┌" + "─"*68 + "┐")
                print(Fore.CYAN + "│" + "  RECORDING MENU".ljust(68) + "│")
                print(Fore.CYAN + "├" + "─"*68 + "┤")
                print(Fore.WHITE + "│  " + Fore.GREEN + "4" + Fore.WHITE + " │ Start Recording Gestures (Button Mode)".ljust(68) + "│")
                print(Fore.WHITE + "│  " + Fore.BLUE + "5" + Fore.WHITE + " │ View Saved Data (Browse & Plot)".ljust(68) + "│")
                print(Fore.WHITE + "│  " + Fore.YELLOW + "6" + Fore.WHITE + " │ Session Statistics".ljust(68) + "│")
                print(Fore.WHITE + "│  " + Fore.MAGENTA + "7" + Fore.WHITE + " │ Disconnect & Start New Session".ljust(68) + "│")
                print(Fore.WHITE + "│  " + Fore.RED + "8" + Fore.WHITE + " │ Disconnect & Exit".ljust(68) + "│")
                print(Fore.CYAN + "└" + "─"*68 + "┘")
                
                choice = input(Fore.WHITE + "\n👉 Enter your choice (4-8): ").strip()
                
                if choice == "4":
                    await self.recording_mode()
                elif choice == "5":
                    self.view_saved_data_menu()
                elif choice == "6":
                    self.show_statistics()
                elif choice == "7":
                    await self.disconnect_gloves()
                    await self.setup_and_connect()
                elif choice == "8":
                    await self.disconnect_gloves()
                    self.exit_application()
                else:
                    print(Fore.RED + "\n❌ Invalid choice! Press Enter to try again...")
                    input()
    
    def view_saved_data_menu(self):
        """Submenu for viewing saved data - User-based browsing"""
        self.print_header()
        print(Fore.CYAN + "\n┌" + "─"*68 + "┐")
        print(Fore.CYAN + "│" + "  VIEW SAVED DATA".ljust(68) + "│")
        print(Fore.CYAN + "├" + "─"*68 + "┤")
        print(Fore.WHITE + "│  1 │ Browse by User → Session → Gesture".ljust(68) + "│")
        print(Fore.WHITE + "│  2 │ Plot specific JSON file (direct path)".ljust(68) + "│")
        print(Fore.WHITE + "│  3 │ List all users".ljust(68) + "│")
        print(Fore.WHITE + "│  4 │ Back to main menu".ljust(68) + "│")
        print(Fore.CYAN + "└" + "─"*68 + "┘")
        
        choice = input(Fore.WHITE + "\n👉 Enter choice (1-4): ").strip()
        
        if choice == "1":
            self._browse_user_sessions()
        elif choice == "2":
            self._plot_single_file()
        elif choice == "3":
            self._list_all_users()
        elif choice == "4":
            return
        else:
            print(Fore.RED + "❌ Invalid choice!")
            input("\nPress Enter to continue...")
    
    def _browse_user_sessions(self):
        """Browse user → session → gesture hierarchy"""
        # List users
        users = DataProcessor.list_users()
        
        if not users:
            print(Fore.RED + "\n❌ No users found!")
            input("\nPress Enter to continue...")
            return
        
        print(Fore.CYAN + f"\n{'='*70}")
        print(Fore.CYAN + "AVAILABLE USERS")
        print(Fore.CYAN + f"{'='*70}")
        
        for i, user in enumerate(users, 1):
            sessions = DataProcessor.list_user_sessions(user)
            print(f"  {i}. {Fore.YELLOW}{user}{Fore.WHITE} - {len(sessions)} session(s)")
        
        print(Fore.CYAN + f"{'='*70}")
        
        try:
            user_choice = int(input(Fore.WHITE + "\nSelect user number (or 0 to cancel): ").strip())
            
            if user_choice == 0:
                return
            
            selected_user = users[user_choice - 1]
            
            # List sessions for selected user
            sessions = DataProcessor.list_user_sessions(selected_user)
            
            if not sessions:
                print(Fore.RED + f"\n❌ No sessions found for {selected_user}!")
                input("\nPress Enter to continue...")
                return
            
            print(Fore.CYAN + f"\n{'='*70}")
            print(Fore.CYAN + f"SESSIONS FOR {selected_user}")
            print(Fore.CYAN + f"{'='*70}")
            
            for i, session in enumerate(sessions, 1):
                gestures = DataProcessor.list_session_gestures(selected_user, session)
                print(f"  {i}. {Fore.YELLOW}{session}{Fore.WHITE} - {len(gestures)} gesture(s)")
            
            print(Fore.CYAN + f"{'='*70}")
            
            session_choice = int(input(Fore.WHITE + "\nSelect session number (or 0 to cancel): ").strip())
            
            if session_choice == 0:
                return
            
            selected_session = sessions[session_choice - 1]
            
            # List gestures in selected session
            gestures = DataProcessor.list_session_gestures(selected_user, selected_session)
            
            if not gestures:
                print(Fore.RED + f"\n❌ No gestures found!")
                input("\nPress Enter to continue...")
                return
            
            print(Fore.CYAN + f"\n{'='*70}")
            print(Fore.CYAN + f"GESTURES IN SESSION")
            print(Fore.CYAN + f"{'='*70}")
            
            for i, gesture in enumerate(gestures, 1):
                print(f"  {i}. {Fore.WHITE}{gesture}")
            
            print(Fore.CYAN + f"{'='*70}")
            print(Fore.YELLOW + "\nOptions:")
            print(Fore.WHITE + "  [number] - Plot specific gesture")
            print(Fore.WHITE + "  [0] - Cancel")
            print(Fore.WHITE + "  [all] - Plot all gestures one by one")
            
            gesture_choice = input(Fore.WHITE + "\nEnter choice: ").strip()
            
            if gesture_choice == "0":
                return
            elif gesture_choice.lower() == "all":
                # Plot all gestures
                base_folder = "data"
                session_path = os.path.join(base_folder, selected_user, selected_session)
                
                print(Fore.CYAN + f"\n📊 Plotting {len(gestures)} gesture(s)...")
                print(Fore.YELLOW + "(Close each window to see next gesture)\n")
                
                for i, gesture_file in enumerate(gestures, 1):
                    file_path = os.path.join(session_path, gesture_file)
                    print(Fore.CYAN + f"[{i}/{len(gestures)}] {Fore.WHITE}{gesture_file}")
                    
                    try:
                        plot_all_fingers_from_json(file_path, show_plots=True, save_plots=True)
                    except Exception as e:
                        print(Fore.RED + f"  ❌ Error: {e}")
                
                print(Fore.GREEN + "\n✓ All gestures plotted!")
            else:
                # Plot specific gesture
                gesture_idx = int(gesture_choice)
                selected_gesture = gestures[gesture_idx - 1]
                
                base_folder = "data"
                file_path = os.path.join(base_folder, selected_user, selected_session, selected_gesture)
                
                print(Fore.CYAN + f"\n📊 Plotting: {selected_gesture}")
                
                try:
                    plot_all_fingers_from_json(file_path, show_plots=True, save_plots=True)
                    print(Fore.GREEN + "\n✓ Plot displayed!")
                except Exception as e:
                    print(Fore.RED + f"\n❌ Error: {e}")
        
        except (ValueError, IndexError):
            print(Fore.RED + "\n❌ Invalid selection!")
        except Exception as e:
            print(Fore.RED + f"\n❌ Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _plot_single_file(self):
        """Plot a single JSON file by direct path"""
        print("\n" + Fore.CYAN + "─"*70)
        json_file = input(Fore.WHITE + "Enter JSON file path: ").strip()
        
        if not os.path.exists(json_file):
            print(Fore.RED + f"\n❌ File not found: {json_file}")
            input("\nPress Enter to continue...")
            return
        
        try:
            print(Fore.CYAN + "\n📊 Generating plots...")
            plot_all_fingers_from_json(json_file, show_plots=True, save_plots=True)
            print(Fore.GREEN + "\n✓ Plots displayed and saved!")
        except Exception as e:
            print(Fore.RED + f"\n❌ Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _list_all_users(self):
        """List all users with their session counts"""
        users = DataProcessor.list_users()
        
        if not users:
            print(Fore.RED + f"\n❌ No users found!")
            input("\nPress Enter to continue...")
            return
        
        print(Fore.CYAN + f"\n{'='*70}")
        print(Fore.CYAN + "ALL USERS")
        print(Fore.CYAN + f"{'='*70}")
        
        for i, user in enumerate(users, 1):
            sessions = DataProcessor.list_user_sessions(user)
            total_gestures = 0
            
            for session in sessions:
                gestures = DataProcessor.list_session_gestures(user, session)
                total_gestures += len(gestures)
            
            print(f"  {i}. {Fore.YELLOW}{user}")
            print(f"      └─ {len(sessions)} session(s), {total_gestures} gesture(s) total")
        
        print(Fore.CYAN + f"{'='*70}")
        input("\nPress Enter to continue...")
    
    async def setup_and_connect(self):
        """Setup session and connect to gloves"""
        self.print_header()
        print(Fore.CYAN + "\n┌" + "─"*68 + "┐")
        print(Fore.CYAN + "│" + "  SESSION SETUP".ljust(68) + "│")
        print(Fore.CYAN + "└" + "─"*68 + "┘")
        
        print(Fore.YELLOW + "\n📝 Step 1: User & Session Information")
        self.user_name = input(Fore.WHITE + "Enter your name: ").strip()
        self.session_name = input(Fore.WHITE + "Enter session name (e.g., Morning_Training): ").strip()
        
        if not self.session_name or not self.user_name:
            print(Fore.RED + "\n❌ User name and session name are required!")
            input("\nPress Enter to try again...")
            return
        
        self.data_processor = DataProcessor(self.session_name, self.user_name)
        self.gesture_counter = 0
        
        print(Fore.GREEN + f"\n✓ Session initialized")
        print(Fore.CYAN + f"   User: {self.user_name}")
        print(Fore.CYAN + f"   Session: {self.session_name}")
        print(Fore.CYAN + f"   Folder: {self.data_processor.session_folder}")
        
        # Scan for gloves
        print(Fore.YELLOW + "\n📡 Step 2: Scanning for gloves...")
        print(Fore.WHITE + "   (Make sure both gloves are powered on)")
        
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            print(Fore.CYAN + f"\n🔍 Scan attempt {attempt}/{max_attempts}...")
            
            try:
                gloves = await self.ble_manager.scan_devices(retry_count=2)
                
                if len(gloves) >= 2:
                    for glove in gloves:
                        if glove.hand == "Left":
                            self.ble_manager.left_glove = glove
                        elif glove.hand == "Right":
                            self.ble_manager.right_glove = glove
                    
                    if self.ble_manager.left_glove and self.ble_manager.right_glove:
                        print(Fore.GREEN + "\n✓ Both gloves found!")
                        print(f"   Left:  {self.ble_manager.left_glove.name}")
                        print(f"   Right: {self.ble_manager.right_glove.name}")
                        break
                
                if attempt < max_attempts:
                    print(Fore.YELLOW + "⚠️  Not all gloves found, retrying...")
                    await asyncio.sleep(2)
            except Exception as e:
                print(Fore.RED + f"❌ Scan error: {e}")
                if attempt < max_attempts:
                    await asyncio.sleep(2)
        
        if not (self.ble_manager.left_glove and self.ble_manager.right_glove):
            print(Fore.RED + "\n❌ Could not find both gloves!")
            input("\nPress Enter to return to menu...")
            return
        
        # Connect to gloves
        print(Fore.YELLOW + "\n🔗 Step 3: Connecting to gloves...")
        
        try:
            left_ok = await self.ble_manager.connect_glove(self.ble_manager.left_glove, retry_count=2)
            right_ok = await self.ble_manager.connect_glove(self.ble_manager.right_glove, retry_count=2)
            
            if left_ok and right_ok:
                await self.ble_manager.setup_notifications(self.ble_manager.left_glove)
                await self.ble_manager.setup_notifications(self.ble_manager.right_glove)
                
                self.ble_manager.button_callback = self.handle_button_press
                
                self.connected = True
                
                print(Fore.GREEN + "\n" + "═"*70)
                print(Fore.GREEN + "✅ CONNECTION SUCCESSFUL!")
                print(Fore.GREEN + "═"*70)
                print(Fore.WHITE + "\n📖 Instructions:")
                print("   1. Press button on RIGHT glove to START recording")
                print("   2. Perform your gesture")
                print("   3. Press button again to STOP recording")
                print("   4. Enter gesture name (or use timestamp default)")
                print("   5. View plots automatically (saved to gesture folder)")
                
                input(Fore.CYAN + "\n✓ Ready to record! Press Enter to continue...")
                return
            else:
                print(Fore.RED + "\n❌ Connection failed!")
                input("\nPress Enter to return to menu...")
                return
                
        except Exception as e:
            print(Fore.RED + f"\n❌ Connection error: {e}")
            input("\nPress Enter to return to menu...")
            return
    
    async def handle_button_press(self, hand: str):
        """Handle button press"""
        current_time = time.time()
        
        # Debounce
        if current_time - self.last_button_time < 1.0:
            return
        
        self.last_button_time = current_time
        
        if not self.recording_active:
            # START RECORDING
            print(Fore.CYAN + "\n⏺️  " + "="*66)
            print(Fore.CYAN + "   RECORDING STARTED")
            print(Fore.CYAN + "   " + "="*66)
            print(Fore.YELLOW + "   Perform your gesture now...")
            print(Fore.YELLOW + "   Press button again to STOP")
            
            self.ble_manager.left_glove.data_buffer.clear()
            self.ble_manager.right_glove.data_buffer.clear()
            self.ble_manager.left_glove.frame_count = 0
            self.ble_manager.right_glove.frame_count = 0
            
            await self.ble_manager.start_recording(self.ble_manager.left_glove)
            await self.ble_manager.start_recording(self.ble_manager.right_glove)
            
            self.recording_active = True
        
        else:
            # STOP RECORDING
            print(Fore.YELLOW + "\n⏹️  " + "="*66)
            print(Fore.YELLOW + "   RECORDING STOPPED")
            print(Fore.YELLOW + "   " + "="*66)
            
            await self.ble_manager.stop_recording(self.ble_manager.left_glove)
            await self.ble_manager.stop_recording(self.ble_manager.right_glove)
            
            self.recording_active = False
            
            await asyncio.sleep(0.5)
            
            left_data = self.ble_manager.left_glove.data_buffer.copy()
            right_data = self.ble_manager.right_glove.data_buffer.copy()
            
            print(Fore.CYAN + f"\n   📊 Captured: Left={len(left_data)} frames, Right={len(right_data)} frames")
            
            if len(left_data) == 0 and len(right_data) == 0:
                print(Fore.RED + "\n   ❌ NO DATA - Recording failed!")
                return
            
            # Generate default timestamp-based name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"gesture_{timestamp}"
            
            print(Fore.CYAN + "\n💾 " + "="*66)
            print(Fore.CYAN + "   SAVE GESTURE")
            print(Fore.CYAN + "   " + "="*66)
            print(Fore.WHITE + f"   Default: {Fore.YELLOW}{default_name}.json")
            
            gesture_name = input(Fore.WHITE + "   Enter custom name (or Enter for default): ").strip()
            
            try:
                filepath = self.data_processor.save_gesture(
                    left_data,
                    right_data,
                    self.ble_manager.left_glove.address,
                    self.ble_manager.right_glove.address,
                    gesture_name if gesture_name else None
                )
                
                self.gesture_counter += 1
                
                print(Fore.GREEN + f"\n   ✅ SAVED: {os.path.basename(filepath)}")
                
                # Auto-plot and save to folder
                print(Fore.CYAN + "\n📊 Generating plots...")
                print(Fore.YELLOW + "   - Displaying on screen")
                print(Fore.YELLOW + "   - Saving to gesture folder")
                
                try:
                    plot_all_fingers_from_json(filepath, show_plots=True, save_plots=True)
                    print(Fore.GREEN + "\n   ✓ Plots displayed and saved!")
                except Exception as e:
                    print(Fore.RED + f"\n   ⚠️  Plot error: {e}")
                    import traceback
                    traceback.print_exc()
                
            except Exception as e:
                print(Fore.RED + f"\n   ❌ Save error: {e}")
                import traceback
                traceback.print_exc()
            
            # Clear buffers
            self.ble_manager.left_glove.data_buffer.clear()
            self.ble_manager.right_glove.data_buffer.clear()
            
            print(Fore.GREEN + "\n" + "="*70)
            print(Fore.GREEN + "✓ Ready for next gesture!")
            print(Fore.GREEN + "="*70 + "\n")
    
    async def recording_mode(self):
        """Enter recording mode"""
        self.print_header()
        print(Fore.CYAN + "\n┌" + "─"*68 + "┐")
        print(Fore.CYAN + "│" + "  GESTURE RECORDING MODE".ljust(68) + "│")
        print(Fore.CYAN + "└" + "─"*68 + "┘")
        
        print(Fore.YELLOW + "\n📖 Instructions:")
        print(Fore.WHITE + "   • Press button on RIGHT glove to START/STOP recording")
        print(Fore.WHITE + "   • Perform gesture between button presses")
        print(Fore.WHITE + "   • Name gesture when prompted (or use timestamp default)")
        print(Fore.WHITE + "   • Plots saved automatically to gesture folder")
        print(Fore.WHITE + "   • Press Ctrl+C to return to menu")
        
        session_info = self.data_processor.get_session_info()
        print(Fore.CYAN + f"\n📁 Data folder: {Fore.WHITE}{session_info['session_folder']}")
        
        print(Fore.GREEN + "\n✓ " + "="*66)
        print(Fore.GREEN + "  READY - Waiting for button press...")
        print(Fore.GREEN + "  " + "="*66 + "\n")
        
        try:
            while True:
                if self.recording_active:
                    left_f = self.ble_manager.left_glove.frame_count
                    right_f = self.ble_manager.right_glove.frame_count
                    print(f"\r   ⏺️  REC... L:{left_f} R:{right_f}", end='', flush=True)
                
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            if self.recording_active:
                print(Fore.RED + "\n\n⚠️  Recording in progress! Stop recording first.")
                await asyncio.sleep(2)
                await self.recording_mode()
            else:
                print(Fore.YELLOW + "\n\n↩️  Returning to menu...")
                await asyncio.sleep(1)
    
    def show_statistics(self):
        """Show session statistics"""
        self.print_header()
        print(Fore.CYAN + "\n┌" + "─"*68 + "┐")
        print(Fore.CYAN + "│" + "  SESSION STATISTICS".ljust(68) + "│")
        print(Fore.CYAN + "└" + "─"*68 + "┘")
        
        session_info = self.data_processor.get_session_info()
        
        print(Fore.YELLOW + f"\n👤 User: {Fore.WHITE}{self.user_name}")
        print(Fore.YELLOW + f"📊 Session: {Fore.WHITE}{self.session_name}")
        print(Fore.YELLOW + f"🎯 Gestures Recorded: {Fore.WHITE}{self.gesture_counter}")
        print(Fore.YELLOW + f"📁 Data Folder: {Fore.WHITE}{session_info['session_folder']}")
        
        print(Fore.YELLOW + f"\n🔌 Left Glove:")
        print(Fore.WHITE + f"   Name: {self.ble_manager.left_glove.name}")
        print(Fore.WHITE + f"   Address: {self.ble_manager.left_glove.address}")
        
        print(Fore.YELLOW + f"\n🔌 Right Glove:")
        print(Fore.WHITE + f"   Name: {self.ble_manager.right_glove.name}")
        print(Fore.WHITE + f"   Address: {self.ble_manager.right_glove.address}")
        
        input(Fore.CYAN + "\nPress Enter to continue...")
    
    async def disconnect_gloves(self):
        """Disconnect from gloves"""
        print(Fore.YELLOW + "\n🔌 Disconnecting from gloves...")
        
        await self.ble_manager.disconnect_all()
        
        self.connected = False
        self.recording_active = False
        
        print(Fore.GREEN + "✓ Disconnected")
        input("\nPress Enter to continue...")
    
    def exit_application(self):
        """Exit the application"""
        print(Fore.CYAN + "\n" + "="*70)
        print(Fore.CYAN + "Thank you for using Gesture Data Collector!")
        print(Fore.CYAN + "="*70 + "\n")
        sys.exit(0)


async def main():
    app = GestureCollectorApp()
    try:
        await app.main_menu()
    except KeyboardInterrupt:
        print(Fore.RED + "\n\n⚠️ Application interrupted")
        if app.connected:
            await app.ble_manager.disconnect_all()
        sys.exit(0)
    except Exception as e:
        print(Fore.RED + f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
