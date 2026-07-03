# BioMotion Studio User Guide

**Version:** v0.90 Beta  
**Application Type:** Desktop biomechanics analysis platform  
**Main Modules:** Weightlifting Analysis, Sprinting Analysis, Results Dashboard, Analysis History

---

## 1. Introduction

BioMotion Studio is a biomechanics analysis application designed for movement analysis in weightlifting and sprinting.

The application can record movement metrics, detect movement phases, generate CSV files, create plots, and produce TXT/HTML reports. It is designed mainly for research, teaching, and demonstration purposes.

This guide explains how to use the current stable version of the application.

---

## 2. Important Notes Before Use

Before using the application, please note:

1. This is a beta version of the software.
2. Tracking quality depends on camera angle, lighting condition, video quality, and full-body visibility.
3. For the current stable testing stage, file-based testing is recommended first.
4. Live RealSense camera validation is planned as a later development/testing step.
5. The tick-style selection box update is also planned as a later UI improvement.
6. Do not change app files while an analysis is running.
7. Always stop and save the analysis before closing the application or changing input files.

---

## 3. Application Startup

### 3.1 Open the Project Folder

Open a terminal or command prompt inside the project folder.

Example:

```bash
cd SportsBiomechanicsApp
```

### 3.2 Activate the Virtual Environment

#### Windows

```bash
.biomec\Scripts\activate
```

#### macOS / Linux

```bash
source .biomec/bin/activate
```

### 3.3 Run the Application

```bash
python main.py
```

or on macOS:

```bash
python3 main.py
```

After running the command, the BioMotion Studio home screen should open.

---

## 4. Home Screen

The Home screen is the main navigation page of the application.

### Main Buttons

| Button | Purpose |
|---|---|
| Weightlifting Analysis | Open the weightlifting biomechanics module |
| Sprinting Analysis | Open the sprinting biomechanics module |
| Results Dashboard | Open the results viewing page |
| Analysis History | View and reopen previous analysis sessions |
| About | View project and developer information |
| Exit | Close the application |

### Recommended First Step

Start by selecting one of the main analysis modules:

- **Weightlifting Analysis**
- **Sprinting Analysis**

---

## 5. Weightlifting Analysis Module

The Weightlifting module is used for Snatch and Clean & Jerk analysis.

### 5.1 Available Selections

#### Exercise Selection

Select one exercise:

- Snatch
- Clean & Jerk

#### Camera View Selection

Select one camera view:

- Side View
- Front View

#### Input Source Selection

Select one input source:

- Live RealSense RGB-D Camera
- Pre-recorded RealSense `.bag` File

For the current stable testing stage, use a pre-recorded `.bag` file if available.

---

## 6. Weightlifting Analysis Workflow

### Step 1: Open Weightlifting Page

From the Home screen, click:

```text
Weightlifting Analysis
```

### Step 2: Select Exercise

Choose either:

```text
Snatch
```

or

```text
Clean & Jerk
```

### Step 3: Select Camera View

Choose:

```text
Side View
```

or

```text
Front View
```

Use **Side View** when you want barbell trajectory analysis.

### Step 4: Select Input Source

For file-based testing, select:

```text
Pre-recorded RealSense .bag File
```

Then click:

```text
Select .bag File
```

Choose the required `.bag` file.

The selected file name should appear on the page. The full path is available as a tooltip.

### Step 5: Select or Correct Barbell ROI

For Side View analysis, the app can use automatic barbell detection. If needed, you can manually select the barbell disk region.

Click:

```text
Select / Correct Barbell ROI
```

Use this mainly when automatic barbell tracking is not stable.

For Front View, ROI is not required.

### Step 6: Start Preview

Click:

```text
Start Preview
```

Check that:

- Video preview appears
- Pose tracking is visible
- Phase status updates
- Metrics update in the live metrics panel

### Step 7: Start Recording

When the preview is working correctly, click:

```text
Start Analysis Recording
```

The status should change to recording mode, and the sample count should increase.

### Step 8: Stop and Save

After the movement is completed, click:

```text
Stop & Save Analysis
```

The app will save:

- CSV files
- Plots
- Reports
- Metadata

Then it will open the Results Dashboard.

---

## 7. Weightlifting Outputs

A saved weightlifting session may include:

### CSV Files

- `joint_angles_2d.csv`
- `depth_data.csv`
- `barbell_trajectory.csv`
- `phase_summary.csv`
- `analysis_summary.csv`
- `lift_summary.csv`
- `phase_biomechanics_summary.csv`

### Plot Files

Examples:

- Hip/knee angle plot
- Upper limb angle plot
- Trunk lean plot
- Barbell trajectory plot
- Barbell velocity plot
- Phase-highlighted plots

### Reports

- `analysis_report.txt`
- `analysis_report.html`

---

## 8. Sprinting Analysis Module

The Sprinting module is used for side-view sprinting biomechanics analysis.

### 8.1 Available Input Sources

- Live RealSense RGB-D Camera
- Pre-recorded RealSense `.bag` File
- Side-view video file

For the current stable testing stage, a side-view video file is recommended.

Supported video formats include:

- `.mp4`
- `.avi`
- `.mov`
- `.mkv`

---

## 9. Sprinting Analysis Workflow

### Step 1: Open Sprinting Page

From the Home screen, click:

```text
Sprinting Analysis
```

### Step 2: Select Input Source

For normal video testing, select:

```text
Side-view Video File
```

Then click:

```text
Select Video / .bag File
```

Choose the sprinting video file.

The selected file name should appear on the page. The full path is available as a tooltip.

### Step 3: Start Preview

Click:

```text
Start Preview
```

Check that:

- Video preview appears
- Pose tracking is visible
- Sprinting phase status updates
- Joint angle metrics update

### Step 4: Start Recording

When tracking is working correctly, click:

```text
Start Analysis Recording
```

The sample count should increase while recording.

### Step 5: Stop and Save

After the required movement section is recorded, click:

```text
Stop & Save Analysis
```

The app will save the results and open the Results Dashboard.

---

## 10. Sprinting Phases

The current sprinting module identifies these phases:

| Phase | Meaning |
|---|---|
| Initial Contact | Foot contacts the ground |
| Support Phase | Body is supported over the stance leg |
| Toe-Off | Foot leaves the ground |
| Flight / Swing | Athlete is in flight or swing phase |

---

## 11. Sprinting Outputs

A saved sprinting session may include:

### CSV Files

- `joint_angles_2d.csv`
- `depth_data.csv`
- `phase_summary.csv`
- `analysis_summary.csv`
- `lift_summary.csv`
- `sprint_summary.csv`
- `phase_biomechanics_summary.csv`

### Plot Files

Examples:

- Sprinting phase timeline
- Knee/ankle angle plot
- Hip/knee angle plot
- Trunk lean plot
- Depth profile plot
- Upper limb angle plot

### Reports

- `analysis_report.txt`
- `analysis_report.html`
- `sprinting_summary_report.txt`

---

## 12. Results Dashboard

The Results Dashboard displays the output of the most recent or selected analysis session.

### Main Functions

| Function | Description |
|---|---|
| Summary View | Shows key results and session information |
| CSV Viewer | Opens generated CSV files inside the app |
| Plot Viewer | Displays generated plot images |
| Open HTML Report | Opens the generated HTML report |
| Open TXT Report | Opens the generated text report |
| Open Results Folder | Opens the saved result folder |

### Using the Results Dashboard

After saving an analysis, the Results Dashboard opens automatically.

You can also open it from the Home screen using:

```text
Results Dashboard
```

If an older session does not have reports, the app may try to generate missing reports automatically.

---

## 13. Analysis History

The Analysis History page allows users to reopen previous analysis sessions.

### Main Functions

| Function | Description |
|---|---|
| Refresh | Reload the session list |
| Open in Results Dashboard | Load selected session into dashboard |
| Open Folder | Open selected session folder |
| Delete Session | Delete an unwanted session |
| Back | Return to Home screen |

### Recommended Use

Use History when you want to review a previous analysis without recording again.

---

## 14. Output Folder Structure

Generated outputs are saved inside the `results/` directory.

Typical structure:

```text
results/
└── Sport/
    └── Exercise/
        └── Camera_View/
            └── Session_Timestamp/
                ├── CSV/
                ├── Plots/
                ├── Reports/
                └── recording_metadata.json
```

For sprinting, the folder may use:

```text
results/
└── Sprinting/
    └── Sprinting/
        └── Side_View/
            └── Session_Timestamp/
```

---

## 15. Good Recording Practices

For better tracking quality:

1. Use a clear side-view video for sprinting.
2. Keep the full athlete body visible.
3. Avoid camera shaking.
4. Use good lighting.
5. Avoid motion blur.
6. Keep the barbell visible for side-view weightlifting.
7. Do not block the athlete or barbell.
8. Start recording only after preview tracking is stable.
9. Stop recording after the movement is complete.
10. Review plots and CSV files after saving.

---

## 16. Common Warning Messages

### File Required

This means you selected file input mode but did not choose a file.

Fix:

```text
Select a video or .bag file before starting preview or recording.
```

### Recording Active

This means an analysis recording is currently running.

Fix:

```text
Click Stop & Save Analysis before changing input, stopping preview, or going back.
```

### No Data Recorded

This means recording started, but no valid metrics were captured.

Possible reasons:

- Pose was not detected
- Video was not visible
- Preview was not running properly
- Person was outside the frame

Fix:

```text
Check preview and tracking quality, then record again.
```

### ROI Not Required

This appears when Front View is selected in weightlifting.

Reason:

```text
Barbell ROI is only needed for Side View trajectory tracking.
```

---

## 17. Recommended Testing Workflow

Before final demonstration, test in this order:

1. Open application.
2. Open Weightlifting page.
3. Select a `.bag` file.
4. Start preview.
5. Start recording.
6. Stop and save.
7. Confirm Results Dashboard opens.
8. Open HTML and TXT reports.
9. Open History and reload the session.
10. Open Sprinting page.
11. Select a side-view video file.
12. Start preview.
13. Start recording.
14. Stop and save.
15. Confirm sprinting results are generated.
16. Open sprinting reports.
17. Reload sprinting session from History.

Use the full checklist here:

```text
docs/testing_checklist.md
```

---

## 18. Halted / Planned Developments

The following developments are planned after testing the current stable version:

### 18.1 RealSense Live Camera Finalization

The app currently includes RealSense-related input options, but final live RealSense validation should be done later with the hardware connected.

Planned checks:

- Live RealSense RGB stream
- Live depth stream
- Device detection
- Stable frame reading
- Error handling when camera is not connected
- Windows RealSense SDK compatibility
- Live recording reliability

### 18.2 Tick-Style Selection UI

The current pages use radio buttons. A later UI update may replace or restyle the selection controls to make selected options more visible.

Planned areas:

- Weightlifting exercise selection
- Weightlifting camera view selection
- Weightlifting input source selection
- Sprinting input source selection

### 18.3 Final Packaging

Packaging will be done after the current beta version is fully tested.

Planned packaging tasks:

- PyInstaller setup
- App icon
- Windows executable
- macOS compatibility testing
- Release folder preparation

---

## 19. Closing the Application

To close the app safely:

1. Stop any active recording.
2. Stop preview if it is running.
3. Return to Home screen if needed.
4. Click:

```text
Exit
```

or close the window.

---

## 20. Support / Contact

Developer:

**Kulunu Kaushal Nugawela**  
Department of Physics  
University of Sri Jayewardenepura  

Email:

```text
kknugawela@gmail.com
```

---

## 21. Version Information

```text
BioMotion Studio v0.90 Beta
```

This user guide is written for the current stable beta version before the halted RealSense and tick-selection updates are completed.
