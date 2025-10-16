"""
Advanced Plotter - Multiple plotting modes for gesture data
Supports: Single file, Comparison, 4-way comparison
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Tuple


FINGER_NAMES = ["IndexFinger", "MiddleFinger", "RingFinger", "LittleFinger", "Thumb", "Palm"]
COMPONENT_NAMES = ["AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"]


def transform_value(val, is_accelerometer):
    """Transform raw sensor value to converted value"""
    try:
        val = float(val)
        if is_accelerometer:
            if val >= 32768:
                return (val - 65536) / 4096
            else:
                return val / 4096
        else:  # Gyroscope
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


def json_to_dataframe(json_file):
    """Convert JSON to DataFrame with converted values"""
    with open(json_file, "r") as f:
        data = json.load(f)
    
    left_hand_raw = data["gesture_recording"]["leftHandDataList"]
    right_hand_raw = data["gesture_recording"]["rightHandDataList"]
    
    left_hand_cleaned = flatten_hand_data(left_hand_raw)
    right_hand_cleaned = flatten_hand_data(right_hand_raw)
    left_hand_parsed = parse_hand_data(left_hand_cleaned)
    right_hand_parsed = parse_hand_data(right_hand_cleaned)
    
    df_left = pd.DataFrame(left_hand_parsed)
    df_right = pd.DataFrame(right_hand_parsed)
    num_rows = max(len(df_left), len(df_right))
    
    df_left = df_left.reindex(range(num_rows)).reset_index(drop=True)
    df_right = df_right.reindex(range(num_rows)).reset_index(drop=True)
    
    combined = {}
    for col in df_left.columns:
        combined[col + "_Left"] = df_left[col]
        combined[col + "_Right"] = df_right[col] if col in df_right.columns else [None]*num_rows
        if "Acc" in col:
            combined[col + "_Left_Converted"] = df_left[col].apply(lambda x: transform_value(x, True))
            combined[col + "_Right_Converted"] = df_right[col].apply(lambda x: transform_value(x, True)) if col in df_right.columns else [None]*num_rows
        elif "Gyro" in col:
            combined[col + "_Left_Converted"] = df_left[col].apply(lambda x: transform_value(x, False))
            combined[col + "_Right_Converted"] = df_right[col].apply(lambda x: transform_value(x, False)) if col in df_right.columns else [None]*num_rows
    
    combined["FrameIndex"] = list(range(num_rows))
    return pd.DataFrame(combined)


def get_filtered_columns(df, hand):
    """Get only converted columns filtered by hand"""
    all_cols = [col for col in df.columns if col != "FrameIndex"]
    filtered = [col for col in all_cols if f"_{hand}" in col and "Converted" in col]
    return filtered


def extract_finger_names(columns):
    """Extract unique finger names from column list"""
    fingers = set()
    for col in columns:
        for finger in FINGER_NAMES:
            if finger in col:
                short_names = {
                    "IndexFinger": "Index",
                    "MiddleFinger": "Middle",
                    "RingFinger": "Ring",
                    "LittleFinger": "Little",
                    "Thumb": "Thumb",
                    "Palm": "Palm"
                }
                fingers.add(short_names.get(finger, finger))
                break
    return '_'.join(sorted(fingers))


def plot_4way_comparison(json_files, column_range, hand, output_folder="plots/comparisons"):
    """
    Create a 2x2 grid comparing 4 JSON files with the same columns
    
    Args:
        json_files: List of 4 JSON file paths
        column_range: Tuple (start, end) e.g., (1, 3) for columns 1-3
        hand: "Left" or "Right"
        output_folder: Folder to save plots
    """
    if len(json_files) != 4:
        print(f"❌ Error: Need exactly 4 JSON files, got {len(json_files)}")
        return
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Convert all JSON files to DataFrames
    print(f"\n⏳ Processing {len(json_files)} JSON files...")
    dfs = []
    json_names = []
    for json_file in json_files:
        print(f"  - Processing: {os.path.basename(json_file)}")
        df = json_to_dataframe(json_file)
        dfs.append(df)
        json_names.append(os.path.splitext(os.path.basename(json_file))[0])
    
    # Get columns for the specified hand
    columns = get_filtered_columns(dfs[0], hand)
    
    if not columns:
        print(f"❌ Error: No converted columns found for {hand} hand")
        return
    
    # Extract the column range
    start_idx, end_idx = column_range
    if start_idx < 1 or end_idx > len(columns) or start_idx > end_idx:
        print(f"❌ Error: Invalid range {start_idx}-{end_idx}. Available: 1-{len(columns)}")
        return
    
    selected_columns = columns[start_idx-1:end_idx]
    
    print(f"\n✓ Selected columns ({start_idx}-{end_idx}):")
    for col in selected_columns:
        print(f"  - {col}")
    
    # Create 2x2 subplot
    fig, axes = plt.subplots(2, 2, figsize=(20, 12))
    axes = axes.flatten()
    
    # Plot each JSON file in a subplot
    for i, (df, json_name, ax) in enumerate(zip(dfs, json_names, axes)):
        for col in selected_columns:
            if col in df.columns:
                ax.plot(df["FrameIndex"], df[col], label=col, linewidth=1.5)
        
        ax.set_xlabel("FrameIndex", fontsize=11)
        ax.set_ylabel("Sensor Value", fontsize=11)
        ax.set_title(f"File {i+1}: {json_name}", fontsize=12, fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # Overall title
    finger_str = extract_finger_names(selected_columns)
    sensor_type = "Acc_Gyro" if any("Acc" in c for c in selected_columns) and any("Gyro" in c for c in selected_columns) else ("Acc" if any("Acc" in c for c in selected_columns) else "Gyro")
    
    fig.suptitle(f"4-Way Comparison: {hand} Hand - {finger_str} - {sensor_type} (Columns {start_idx}-{end_idx})", 
                 fontsize=16, fontweight='bold', y=0.995)
    
    # Generate filename
    filename = f"4way_compare_{hand}_{finger_str}_{sensor_type}_cols{start_idx}-{end_idx}.png"
    output_path = os.path.join(output_folder, filename)
    
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n✓ 4-way comparison plot saved: {output_path}")
    return output_path


def batch_plot_all_ranges(json_files, hand, output_folder="plots/comparisons"):
    """Create comparison plots for all default ranges"""
    # Default ranges (12 groups of 3 columns each)
    ranges = [
        (1, 3), (4, 6), (7, 9), (10, 12), (13, 15), (16, 18),
        (19, 21), (22, 24), (25, 27), (28, 30), (31, 33), (34, 36)
    ]
    
    print(f"\n{'='*70}")
    print(f"Creating 4-way comparison plots for all {len(ranges)} ranges")
    print(f"{'='*70}")
    
    created_plots = []
    for i, (start, end) in enumerate(ranges, 1):
        print(f"\n[{i}/{len(ranges)}] Processing columns {start}-{end}...")
        try:
            plot_path = plot_4way_comparison(json_files, (start, end), hand, output_folder)
            if plot_path:
                created_plots.append(plot_path)
        except Exception as e:
            print(f"  ⚠️ Error: {e}")
    
    print(f"\n{'='*70}")
    print(f"✓ Created {len(created_plots)}/{len(ranges)} comparison plots successfully!")
    print(f"✓ Output folder: {output_folder}")
    print(f"{'='*70}")
    
    return created_plots


def plot_2way_comparison(json_file1, json_file2, column_range, hand, output_folder="plots/comparisons"):
    """Create side-by-side comparison of 2 JSON files"""
    os.makedirs(output_folder, exist_ok=True)
    
    # Convert to DataFrames
    print(f"\n⏳ Processing files...")
    df1 = json_to_dataframe(json_file1)
    df2 = json_to_dataframe(json_file2)
    
    json1_name = os.path.splitext(os.path.basename(json_file1))[0]
    json2_name = os.path.splitext(os.path.basename(json_file2))[0]
    
    # Get columns
    columns = get_filtered_columns(df1, hand)
    
    if not columns:
        print(f"❌ Error: No converted columns found for {hand} hand")
        return
    
    # Extract range
    start_idx, end_idx = column_range
    if start_idx < 1 or end_idx > len(columns) or start_idx > end_idx:
        print(f"❌ Error: Invalid range {start_idx}-{end_idx}. Available: 1-{len(columns)}")
        return
    
    selected_columns = columns[start_idx-1:end_idx]
    
    # Create 1x2 subplot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7), sharey=True)
    
    # Plot file 1
    for col in selected_columns:
        if col in df1.columns:
            ax1.plot(df1["FrameIndex"], df1[col], label=col, linewidth=1.5)
    
    ax1.set_xlabel("FrameIndex", fontsize=12)
    ax1.set_ylabel("Sensor Value", fontsize=12)
    ax1.set_title(f"File 1: {json1_name}", fontsize=12, fontweight='bold')
    ax1.legend(loc='best', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Plot file 2
    for col in selected_columns:
        if col in df2.columns:
            ax2.plot(df2["FrameIndex"], df2[col], label=col, linewidth=1.5)
    
    ax2.set_xlabel("FrameIndex", fontsize=12)
    ax2.set_title(f"File 2: {json2_name}", fontsize=12, fontweight='bold')
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # Overall title
    finger_str = extract_finger_names(selected_columns)
    sensor_type = "Acc_Gyro" if any("Acc" in c for c in selected_columns) and any("Gyro" in c for c in selected_columns) else ("Acc" if any("Acc" in c for c in selected_columns) else "Gyro")
    
    fig.suptitle(f"2-Way Comparison: {hand} Hand - {finger_str} - {sensor_type}", 
                 fontsize=14, fontweight='bold')
    
    # Save
    filename = f"2way_{json1_name}_vs_{json2_name}_{hand}_{finger_str}_{sensor_type}.png"
    output_path = os.path.join(output_folder, filename)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n✓ 2-way comparison saved: {output_path}")
    return output_path


# Integration function for main.py
def advanced_plot_menu():
    """Menu for advanced plotting features"""
    print("\n" + "="*70)
    print("ADVANCED PLOTTING")
    print("="*70)
    
    print("\n  1. 2-Way Comparison (Side-by-side)")
    print("  2. 4-Way Comparison (2x2 grid)")
    print("  3. 4-Way Batch (All 12 ranges)")
    print("  4. Back to main menu")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        _menu_2way_comparison()
    elif choice == "2":
        _menu_4way_comparison()
    elif choice == "3":
        _menu_4way_batch()
    elif choice == "4":
        return
    else:
        print("❌ Invalid choice!")


def _menu_2way_comparison():
    """2-way comparison menu"""
    json1 = input("\nEnter first JSON file path: ").strip()
    json2 = input("Enter second JSON file path: ").strip()
    
    if not (os.path.exists(json1) and os.path.exists(json2)):
        print("❌ One or both files not found!")
        return
    
    hand = input("Hand (Left/Right): ").strip().capitalize()
    range_input = input("Column range (e.g., 1-3): ").strip()
    
    try:
        start, end = map(int, range_input.split('-'))
        plot_2way_comparison(json1, json2, (start, end), hand)
    except ValueError:
        print("❌ Invalid range format!")


def _menu_4way_comparison():
    """4-way comparison menu"""
    print("\nEnter 4 JSON file paths:")
    json_files = []
    for i in range(4):
        path = input(f"  File {i+1}: ").strip()
        if not os.path.exists(path):
            print(f"❌ File not found: {path}")
            return
        json_files.append(path)
    
    hand = input("\nHand (Left/Right): ").strip().capitalize()
    range_input = input("Column range (e.g., 1-3): ").strip()
    
    try:
        start, end = map(int, range_input.split('-'))
        plot_4way_comparison(json_files, (start, end), hand)
    except ValueError:
        print("❌ Invalid range format!")


def _menu_4way_batch():
    """4-way batch menu"""
    print("\nEnter 4 JSON file paths:")
    json_files = []
    for i in range(4):
        path = input(f"  File {i+1}: ").strip()
        if not os.path.exists(path):
            print(f"❌ File not found: {path}")
            return
        json_files.append(path)
    
    hand = input("\nHand (Left/Right): ").strip().capitalize()
    
    batch_plot_all_ranges(json_files, hand)


if __name__ == "__main__":
    advanced_plot_menu()
