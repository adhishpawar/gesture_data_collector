"""
BLE Manager - Handles device scanning, connection, and data streaming
"""

import asyncio
import struct
from bleak import BleakClient, BleakScanner
from typing import Optional, Callable, List
from datetime import datetime
from colorama import Fore  # ← ADD THIS LINE
import config


class GloveDevice:
    def __init__(self, address: str, name: str, hand: str):
        self.address = address
        self.name = name
        self.hand = hand  # "Left" or "Right"
        self.client: Optional[BleakClient] = None
        self.data_buffer: List[List[int]] = []
        self.is_recording = False
        self.frame_count = 0
        
    def __repr__(self):
        return f"GloveDevice({self.hand}, {self.name}, {self.address})"


class BLEManager:
    def __init__(self):
        self.left_glove: Optional[GloveDevice] = None
        self.right_glove: Optional[GloveDevice] = None
        self.button_callback: Optional[Callable] = None
        self.data_callback: Optional[Callable] = None
        self.live_plotter = None  # For live plotting
        
    async def scan_devices(self, retry_count=3) -> List[GloveDevice]:
        """Scan for BLE devices and identify gloves with manual selection"""
        
        for attempt in range(1, retry_count + 1):
            try:
                print(f"\n🔍 Scanning for BLE devices (Attempt {attempt}/{retry_count})...")
                
                devices = await BleakScanner.discover(timeout=config.SCAN_DURATION)
                
                glovatrix_devices = []
                all_devices = []
                
                print(f"\n📱 Found {len(devices)} BLE device(s):")
                
                for idx, device in enumerate(devices, 1):
                    name = device.name or "Unknown"
                    all_devices.append(device)
                    
                    # Collect all Glovatrix devices
                    if "glovatrix" in name.lower():
                        glovatrix_devices.append(device)
                        print(f"  {idx}. {name} ({device.address}) ✓ Glovatrix")
                    else:
                        print(f"  {idx}. {name} ({device.address})")
                
                # Manual selection for Glovatrix devices
                if len(glovatrix_devices) >= 2:
                    print(f"\n{'='*60}")
                    print(f"Found {len(glovatrix_devices)} Glovatrix device(s) - Manual Selection Required")
                    print(f"{'='*60}")
                    
                    print("\nGlovatrix Devices:")
                    for i, dev in enumerate(glovatrix_devices, 1):
                        print(f"  {i}. {dev.name} ({dev.address})")
                    
                    # Select LEFT glove
                    print(f"\n{'-'*60}")
                    while True:
                        try:
                            left_idx = int(input(f"Select LEFT glove [1-{len(glovatrix_devices)}]: ").strip()) - 1
                            if 0 <= left_idx < len(glovatrix_devices):
                                break
                            print(f"Please enter a number between 1 and {len(glovatrix_devices)}")
                        except ValueError:
                            print("Please enter a valid number")
                    
                    # Select RIGHT glove
                    while True:
                        try:
                            right_idx = int(input(f"Select RIGHT glove [1-{len(glovatrix_devices)}]: ").strip()) - 1
                            if 0 <= right_idx < len(glovatrix_devices):
                                if right_idx == left_idx:
                                    print("⚠️  Cannot select the same device for both hands!")
                                    continue
                                break
                            print(f"Please enter a number between 1 and {len(glovatrix_devices)}")
                        except ValueError:
                            print("Please enter a valid number")
                    
                    # Create glove devices
                    left_glove = GloveDevice(
                        glovatrix_devices[left_idx].address, 
                        glovatrix_devices[left_idx].name, 
                        "Left"
                    )
                    right_glove = GloveDevice(
                        glovatrix_devices[right_idx].address, 
                        glovatrix_devices[right_idx].name, 
                        "Right"
                    )
                    
                    print(f"\n{'='*60}")
                    print("✓ Manual Selection Complete:")
                    print(f"  LEFT:  {left_glove.name} ({left_glove.address})")
                    print(f"  RIGHT: {right_glove.name} ({right_glove.address})")
                    print(f"{'='*60}")
                    
                    return [left_glove, right_glove]
                
                elif len(glovatrix_devices) == 1:
                    print(f"\n⚠️  Only 1 Glovatrix device found - need 2 devices")
                    print("Please ensure both gloves are powered on")
                    
                    if attempt < retry_count:
                        print(f"\nRetrying scan in 3 seconds...")
                        await asyncio.sleep(3)
                        continue
                
                else:
                    print(f"\n⚠️  No Glovatrix devices found - using manual device selection")
                    # Will fall through to manual selection in main.py
                    return []
                
            except OSError as e:
                if "2147020577" in str(e):
                    print(f"\n❌ Attempt {attempt} failed: Bluetooth adapter not ready")
                    
                    if attempt < retry_count:
                        print("   Retrying in 3 seconds...")
                        await asyncio.sleep(3)
                    else:
                        raise RuntimeError("Bluetooth adapter not ready after retries")
                else:
                    raise
            
            except Exception as e:
                print(f"❌ Unexpected error during scan: {e}")
                if attempt >= retry_count:
                    raise
                await asyncio.sleep(3)
        
        return []


    async def select_devices_manual(self, devices: List) -> tuple:
        """Manual device selection from scan results"""
        print("\n" + "="*60)
        print("Manual Device Selection")
        print("="*60)
        
        for idx, device in enumerate(devices, 1):
            name = device.name or "Unknown"
            print(f" {idx}. {name} ({device.address})")
        
        left_idx = int(input("\nSelect LEFT glove [number]: ")) - 1
        right_idx = int(input("Select RIGHT glove [number]: ")) - 1
        
        self.left_glove = GloveDevice(devices[left_idx].address, 
                                      devices[left_idx].name, "Left")
        self.right_glove = GloveDevice(devices[right_idx].address, 
                                       devices[right_idx].name, "Right")
        
        return self.left_glove, self.right_glove
    
    async def connect_glove(self, glove: GloveDevice, retry_count=3) -> bool:
        """Connect to a single glove device with retry logic"""
        
        for attempt in range(1, retry_count + 1):
            try:
                print(f"🔗 Connecting to {glove.hand} glove ({glove.name})... [Attempt {attempt}/{retry_count}]")
                
                # Create new client instance for each attempt
                glove.client = BleakClient(glove.address, timeout=20.0)
                await glove.client.connect()
                
                if not glove.client.is_connected:
                    print(f"⚠️  Connection attempt {attempt} failed for {glove.hand} glove")
                    
                    if attempt < retry_count:
                        print(f"   Retrying in 2 seconds...")
                        await asyncio.sleep(2)
                        continue
                    else:
                        print(f"❌ Failed to connect to {glove.hand} glove after {retry_count} attempts")
                        return False
                
                print(f"✓ Connected to {glove.hand} glove")
                
                # Request MTU (optional)
                try:
                    await glove.client.write_gatt_char(
                        config.CHAR_CONTROL_UUID, 
                        bytearray([0x05, 0x00])
                    )
                except Exception:
                    pass  # Ignore MTU errors
                
                return True
                
            except Exception as e:
                print(f"⚠️  Attempt {attempt} error: {str(e)[:50]}...")
                
                # Try to disconnect if partially connected
                try:
                    if glove.client and glove.client.is_connected:
                        await glove.client.disconnect()
                except Exception:
                    pass
                
                if attempt < retry_count:
                    print(f"   Retrying in 2 seconds...")
                    await asyncio.sleep(2)
                else:
                    print(f"❌ Failed to connect to {glove.hand} glove: {e}")
                    return False
        
        return False

    async def setup_notifications(self, glove: GloveDevice):
        """Enable notifications on ee01 and ff01 characteristics"""
        try:
            # Notification handler for CONTROL characteristic (ee01)
            async def control_handler(sender, data):
                """Handle control characteristic notifications (button press)"""
                
                # ⭐ LOG ALL CONTROL DATA
                print(f"\n📥 [{glove.hand}] Control data: {list(data)} (len={len(data)})")
                
                # Check for button press [64]
                is_button_press = False
                
                # Method 1: Single byte [64]
                if len(data) == 1 and data[0] == config.BUTTON_TRIGGER:
                    is_button_press = True
                    print(f"✓ Button detected: Single [64]")
                
                # Method 2: Check if 64 is in data
                elif config.BUTTON_TRIGGER in data:
                    is_button_press = True
                    print(f"✓ Button detected: [64] in array")
                
                if is_button_press:
                    print(f"🔘 BUTTON PRESSED on {glove.hand} glove")
                    
                    # ⭐ ONLY trigger callback if RIGHT glove
                    if glove.hand == "Right" and self.button_callback:
                        print(f"   → Calling button callback...")
                        try:
                            await self.button_callback(glove.hand)
                        except Exception as e:
                            print(f"❌ Callback error: {e}")
                            import traceback
                            traceback.print_exc()
                    elif glove.hand == "Left":
                        print(f"   ⚠️  Left button ignored (RIGHT glove has button)")
                else:
                    # Not a button press
                    pass

            # Notification handler for DATA characteristic (ff01)
            async def data_handler(sender, data):
                """Handle data characteristic notifications (sensor data)"""
                
                # ⭐ SAFETY: Ignore if looks like button press
                if len(data) == 1 and data[0] == config.BUTTON_TRIGGER:
                    print(f"⚠️  [{glove.hand}] [64] on DATA characteristic - ignoring")
                    return
                
                # Process only if recording
                if glove.is_recording:
                    uint16_array = self._bytes_to_uint16_list(data)
                    
                    # ⭐ MUST be exactly 36 values
                    if len(uint16_array) == config.EXPECTED_FRAME_LENGTH:
                        glove.data_buffer.append(uint16_array)
                        glove.frame_count += 1
                        
                        # Send to live plotter
                        if self.live_plotter and self.live_plotter.is_running:
                            self.live_plotter.add_data(glove.hand, uint16_array)
                        
                        # ⭐ REDUCED SPAM: Frame counter every 100 frames
                        if glove.frame_count % 100 == 0:
                            print(f"  [{glove.hand}] Frames: {glove.frame_count}")
                    else:
                        # Wrong length - not valid sensor data
                        if glove.frame_count < 3:  # Only show first few
                            print(f"⚠️  [{glove.hand}] Invalid frame: len={len(uint16_array)} (expected 36)")


            
            # Subscribe to notifications
            print(f"🔔 Subscribing to notifications for {glove.hand} glove...")
            
            await glove.client.start_notify(config.CHAR_CONTROL_UUID, control_handler)
            print(f"   ✓ Control characteristic (ee01) subscribed")
            
            await glove.client.start_notify(config.CHAR_DATA_UUID, data_handler)
            print(f"   ✓ Data characteristic (ff01) subscribed")
            
            print(f"✅ Notifications enabled for {glove.hand} glove")
            
        except Exception as e:
            print(f"❌ Error setting up notifications for {glove.hand}: {e}")
            import traceback
            traceback.print_exc()


    
    def _bytes_to_uint16_list(self, data: bytearray) -> List[int]:
        """
        Convert raw bytes to Uint16 array (matching Flutter logic)
        """
        # Convert to signed int8 first
        int8_array = struct.unpack(f'{len(data)}b', data)
        
        # Convert to bytes buffer
        byte_buffer = bytearray()
        for val in int8_array:
            byte_buffer.append(val & 0xFF)
        
        # Read as little-endian uint16
        uint16_count = len(byte_buffer) // 2
        uint16_array = struct.unpack(f'<{uint16_count}H', byte_buffer[:uint16_count*2])
        
        return list(uint16_array)
    
    async def start_recording(self, glove: GloveDevice):
        """Send START command to glove"""
        try:
            # Send command (matches Flutter's [0x01, 1])
            await glove.client.write_gatt_char(
                config.CHAR_CONTROL_UUID, 
                bytearray(config.CMD_START_BROADCAST)
            )
            
            glove.is_recording = True
            # Don't clear buffer here - do it in handle_button_press
            glove.frame_count = 0
            
            print(f"✓ {glove.hand} glove started broadcasting")
            
        except Exception as e:
            print(f"❌ Error starting {glove.hand} glove: {e}")


    async def stop_recording(self, glove: GloveDevice):
        """Send STOP command to glove"""
        try:
            # Send command (matches Flutter's [0x01, 0x02])
            await glove.client.write_gatt_char(
                config.CHAR_CONTROL_UUID, 
                bytearray(config.CMD_STOP_BROADCAST)
            )
            
            glove.is_recording = False
            
            print(f"\n✓ {glove.hand} glove stopped broadcasting (Frames: {glove.frame_count})")
            
        except Exception as e:
            print(f"❌ Error stopping {glove.hand} glove: {e}")

    
    async def disconnect_all(self):
        """Disconnect both gloves"""
        for glove in [self.left_glove, self.right_glove]:
            if glove and glove.client and glove.client.is_connected:
                try:
                    await glove.client.disconnect()
                    print(f"✓ Disconnected {glove.hand} glove")
                except Exception as e:
                    print(f"❌ Error disconnecting {glove.hand}: {e}")
