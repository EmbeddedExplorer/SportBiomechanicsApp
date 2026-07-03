# BioMotion Studio

**BioMotion Studio** is a desktop biomechanics analysis platform for weightlifting and sprinting.  
It uses computer vision and RGB-D sensing workflows to record movement data, detect key movement phases, generate biomechanics metrics, and export CSV files, plots, and final reports.

## Project Status

Current version: **v0.90 Beta**

The current version supports:

- Weightlifting biomechanics analysis
- Snatch and Clean & Jerk workflows
- Side-view and front-view weightlifting analysis
- Sprinting biomechanics analysis
- RealSense live camera input
- Pre-recorded RealSense `.bag` file input
- Side-view video file input for sprinting
- Live preview and tracking view
- Phase detection
- Joint angle calculation
- Depth data recording
- Barbell trajectory tracking for weightlifting side view
- CSV export
- Plot generation
- TXT and HTML report generation
- Analysis history
- Results dashboard reload from previous sessions

## Main Features

### 1. Weightlifting Analysis

The weightlifting module supports:

- Snatch
- Clean & Jerk
- Side View
- Front View
- Live RealSense RGB-D camera
- Pre-recorded RealSense `.bag` file
- Manual or automatic barbell ROI tracking for side view
- Pose-based phase detection
- Joint angle tracking
- Barbell displacement and velocity analysis
- Phase-wise biomechanics summary

Generated outputs include:

- Joint angles CSV
- Depth data CSV
- Barbell trajectory CSV
- Phase summary CSV
- Analysis summary CSV
- Lift summary CSV
- Phase-highlighted plots
- TXT and HTML reports

### 2. Sprinting Analysis

The sprinting module supports:

- Live RealSense RGB-D camera
- Pre-recorded RealSense `.bag` file
- Side-view video file
- Sprinting phase detection
- Joint angle tracking
- Athlete depth profile
- Sprinting-specific plots and reports

Detected sprinting phases include:

- Initial Contact
- Support Phase
- Toe-Off
- Flight / Swing

Generated outputs include:

- Joint angles CSV
- Depth data CSV
- Sprint summary CSV
- Phase summary CSV
- Sprinting plots
- TXT and HTML reports

### 3. Results Dashboard

The Results Dashboard provides:

- Key session summary
- CSV file viewer
- Plot viewer
- Open HTML report
- Open TXT report
- Open results folder
- Sport-aware display for weightlifting and sprinting

### 4. Analysis History

The History page allows users to:

- View previous sessions
- Open old sessions in the Results Dashboard
- Open result folders
- Delete unwanted analysis sessions

## Supported Input Sources

| Module | Input Source |
|---|---|
| Weightlifting | Live RealSense RGB-D Camera |
| Weightlifting | Pre-recorded RealSense `.bag` File |
| Sprinting | Live RealSense RGB-D Camera |
| Sprinting | Pre-recorded RealSense `.bag` File |
| Sprinting | Side-view Video File |

## Output Folder Structure

Generated analysis results are saved inside the `results/` folder.

Typical folder structure:

```text
results/
└── Sport/
    └── Exercise/
        └── Camera_View/
            └── Session_Timestamp/
                ├── CSV/
                │   ├── joint_angles_2d.csv
                │   ├── depth_data.csv
                │   ├── phase_summary.csv
                │   ├── analysis_summary.csv
                │   ├── lift_summary.csv
                │   └── phase_biomechanics_summary.csv
                ├── Plots/
                │   └── generated_plot_files.png
                ├── Reports/
                │   ├── analysis_report.txt
                │   └── analysis_report.html
                └── recording_metadata.json
```

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd SportsBiomechanicsApp
```

### 2. Create a virtual environment

#### Windows

```bash
python -m venv .biomec
.biomec\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv .biomec
source .biomec/bin/activate
```

### 3. Install requirements

#### General installation

```bash
python -m pip install -r requirements.txt
```

#### Windows with RealSense support

```bash
python -m pip install -r requirements_windows.txt
```

#### macOS testing

```bash
python3 -m pip install -r requirements_macos.txt
```

> Note: Intel RealSense support on macOS can be difficult depending on Python version, system architecture, and RealSense SDK support. For macOS, video-file testing is recommended first.

## How to Run

From the project root:

```bash
python main.py
```

or on macOS:

```bash
python3 main.py
```

## Basic Usage Workflow

1. Open the application.
2. Select either **Weightlifting Analysis** or **Sprinting Analysis**.
3. Choose the input source.
4. Select the required exercise and camera view when using weightlifting.
5. Start preview and confirm that tracking is working.
6. Start analysis recording.
7. Stop and save analysis.
8. Review the Results Dashboard.
9. Open CSV files, plots, and generated reports.
10. Reopen previous sessions from Analysis History when needed.

## Recommended Testing Before Demonstration

Before a final demonstration, test:

- Weightlifting with a `.bag` file
- Sprinting with a video file
- Sprinting or weightlifting with RealSense live input if hardware is available
- Results Dashboard
- HTML/TXT report opening
- Analysis History reload
- Delete session function
- App close and restart

See:

```text
docs/testing_checklist.md
```

## Known Limitations

- Tracking accuracy depends on video quality, lighting, camera angle, and pose visibility.
- RealSense live input requires compatible hardware and driver support.
- Barbell trajectory tracking is mainly intended for weightlifting side-view analysis.
- Sprinting analysis is currently designed for side-view videos.
- macOS RealSense support may require additional setup and may not work on all systems.
- This version is a beta research/development tool and should be validated before formal scientific use.

## Suggested Git Ignore Policy

The following files/folders should not normally be committed:

- `results/`
- `database/`
- virtual environments
- videos
- `.bag` files
- generated CSV files
- generated plots
- generated reports
- Python cache files

## Developer

**Kulunu Kaushal Nugawela**  
Department of Physics  
University of Sri Jayewardenepura  

Contact: `kknugawela@gmail.com`

## Version

```text
BioMotion Studio v0.90 Beta
```
