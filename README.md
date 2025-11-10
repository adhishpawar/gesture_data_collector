# Advanced Plotter

`advanced_plotter.py` is a sophisticated Python utility designed to
visualize and compare time-series gesture data recorded in JSON files.
It provides single-file plots, 2-way comparisons, and 4-way grid
comparisons for deep analysis and validation of gesture recordings.

------------------------------------------------------------------------

## 🚀 Features

-   Convert raw JSON gesture sensor data into structured pandas
    DataFrames\
-   Transform signed 16-bit integer sensor values into physical units\
-   Generate:
    -   Single-file detailed plots
    -   2-way side‑by‑side comparison plots
    -   4-way (2x2) comparison grids\
-   Automatically process all sensor ranges and generate complete
    comparison sets\
-   Save all plots as PNG images inside organized folders

------------------------------------------------------------------------

## 📚 Key Libraries Used

-   **pandas** --- DataFrame creation and manipulation\
-   **matplotlib** --- Plot generation\
-   **os** --- File and directory handling\
-   **json** --- Parsing raw gesture recordings\
-   **numpy** --- Underlying numerical support

------------------------------------------------------------------------

## 🧠 Core Workflow

### 1️⃣ Data Processing

The script loads JSON gesture files and converts them into clean
DataFrames.

**Main functions involved:**

### `json_to_dataframe(json_file)`

-   Reads the JSON file\
-   Extracts `leftHandDataList` and `rightHandDataList`\
-   Flattens nested sensor structures using:
    -   `flatten_hand_data`
    -   `parse_hand_data`
-   Converts raw integer sensor values into meaningful units using:
    -   `transform_value`
-   Produces a pandas DataFrame with clear column names such as:
    -   `IndexFinger_AccX`, `MiddleFinger_GyroZ`, etc.

------------------------------------------------------------------------

### 2️⃣ Visualization

The script includes multiple plotting utilities.

### ✅ `plot_4way_comparison(json_files, column_range, hand, ...)`

-   Creates a **2x2 grid** comparing four JSON files\
-   Plots identical sensor ranges for all files\
-   Saves the figure in `plots/comparisons/`

### ✅ `batch_plot_all_ranges(json_files, hand, ...)`

-   Automatically generates **all 12 standard sensor range comparisons**
-   Calls `plot_4way_comparison` repeatedly
-   Ideal for complete dataset comparisons

### ✅ `plot_2way_comparison(...)`

-   Generates **side-by-side comparison** for two recordings
-   Useful for checking gesture consistency across users or sessions

------------------------------------------------------------------------

## 📝 How It Works (Summary)

1.  **Load Data** --- Parses raw JSON recordings\
2.  **Clean & Structure** --- Converts nested sensor readings into a
    DataFrame\
3.  **Transform Values** --- Applies physical unit conversions\
4.  **Visualize** --- Produces line plots using matplotlib\
5.  **Save Outputs** --- Stores PNG images in organized directories

------------------------------------------------------------------------

## 📂 Folder Structure

    advanced_plotter/
    │
    ├── advanced_plotter.py
    ├── plots/
    │   ├── comparisons/
    │   └── singles/
    └── README.md

------------------------------------------------------------------------

## 🧪 Example Usage

``` python
from advanced_plotter import json_to_dataframe, plot_4way_comparison

files = [
    "gesture1.json",
    "gesture2.json",
    "gesture3.json",
    "gesture4.json"
]

plot_4way_comparison(
    json_files=files,
    column_range=(0, 3),
    hand="Left"
)
```

------------------------------------------------------------------------

## 🛠 Requirements

Install dependencies:

``` bash
pip install pandas matplotlib numpy
```

------------------------------------------------------------------------

## ✅ Purpose

This tool is essential for validating sensor data quality, comparing
gesture patterns across users, and improving ML model training for the
**gesture_data_collector** ecosystem.

------------------------------------------------------------------------

## Author

Developed for **GlovaTrix**.
