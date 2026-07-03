# BioMotion Studio Testing Checklist

Use this checklist before committing major updates, preparing a demonstration, or creating a release build.

## Test Information

| Item | Details |
|---|---|
| App Version | v0.90 Beta |
| Tester | Kulunu Kaushal Nugawela |
| Date |  |
| Operating System |  |
| Python Version |  |
| RealSense Device Available | Yes / No |
| Test Dataset Used |  |

---

## 1. Application Startup

| Test | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Start app using `python main.py` | App opens without errors |  |  |
| Home page loads | Compact dashboard appears correctly |  |  |
| Navigation buttons visible | All main buttons are visible |  |  |
| About page opens | About page displays correctly |  |  |
| Back button from About page | Returns to Home page |  |  |

---

## 2. Home Page

| Test | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Home page fits screen | No excessive scrolling required |  |  |
| System status displayed | Status text is readable |  |  |
| Recent sessions displayed | Recent sessions list appears |  |  |
| Navigation to Weightlifting | Opens Weightlifting page |  |  |
| Navigation to Sprinting | Opens Sprinting page |  |  |
| Navigation to Results Dashboard | Opens Results Dashboard |  |  |
| Navigation to History | Opens History page |  |  |

---

## 3. Weightlifting Page UI

| Test | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Page opens | Weightlifting page loads without crash |  |  |
| Select Snatch | Snatch can be selected |  |  |
| Select Clean & Jerk | Clean & Jerk can be selected |  |  |
| Select Side View | Side View can be selected |  |  |
| Select Front View | Front View can be selected |  |  |
| Select Live RealSense | Live mode can be selected |  |  |
| Select `.bag` file mode | Bag mode can be selected |  |  |
| Select `.bag` file | File name displays clearly |  |  |
| File label tooltip | Full file path is available |  |  |

---

## 4. Weightlifting Preview Test

| Test | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Start preview with no `.bag` selected in bag mode | Warning message appears |  |  |
| Start preview with selected `.bag` | Preview starts |  |  |
| Pose tracking visible | Skeleton/overlay appears when pose is detected |  |  |
| Metrics update | Live metrics show values |  |  |
| Status updates | Status text updates clearly |  |  |
| Stop preview | Preview stops safely |  |  |
| Back while preview active | Confirmation message appears |  |  |

---

## 5. Weightlifting Recording Test

| Test | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Start recording | Recording starts and button states update |  |  |
| Metrics recorded | Sample count increases |  |  |
| Stop and save | Outputs are saved |  |  |
| Results Dashboard opens | Dashboard opens after saving |  |  |
| CSV files generated | CSV files appear in results folder |  |  |
| Plots generated | Plot files appear in Plots folder |  |  |
| Reports generated | TXT and HTML reports appear |  |  |
| Open HTML report | HTML report opens |  |  |
| Open TXT report | TXT report opens |  |  |

---

## 6. Weightlifting Barbell ROI Test

| Test | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Select ROI before file | Warning shown if required file is missing |  |  |
| Select ROI from `.bag` first frame | ROI selection window opens |  |  |
| Select ROI during preview | Current frame can be used |  |  |
| Side View ROI behavior | ROI is used for side-view tracking |  |  |
| Front View ROI behavior | App says ROI is not required |  |  |

---

## 7. Sprinting Page UI

| Test | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Page opens | Sprinting page loads without crash |  |  |
| Select Live RealSense | Live mode can be selected |  |  |
| Select `.bag` file mode | Bag mode can be selected |  |  |
| Select video file mode | Video file mode can be selected |  |  |
| Select video or `.bag` file | File name displays clearly |  |  |
| File label tooltip | Full file path is available |  |  |

---

## 8. Sprinting Preview Test

| Test | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Start preview with no file in video/bag mode | Warning message appears |  |  |
| Start preview with selected video | Preview starts |  |  |
| Pose tracking visible | Skeleton/overlay appears when pose is detected |  |  |
| Sprinting phases update | Phase label changes during movement |  |  |
| Metrics update | Live metrics show values |  |  |
| Stop preview | Preview stops safely |  |  |
| Back while preview active | Confirmation message appears |  |  |

---

## 9. Sprinting Recording Test

| Test | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Start recording | Recording starts and button states update |  |  |
| Metrics recorded | Sample count increases |  |  |
| Stop and save | Outputs are saved |  |  |
| Results Dashboard opens | Dashboard opens after saving |  |  |
| CSV files generated | Sprinting CSV files appear |  |  |
| Plots generated | Sprinting plots appear |  |  |
| Reports generated | TXT and HTML reports appear |  |  |
| Open HTML report | HTML report opens |  |  |
| Open TXT report | TXT report opens |  |  |

---

## 10. Results Dashboard Test

| Test | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Open dashboard after weightlifting | Weightlifting summary appears |  |  |
| Open dashboard after sprinting | Sprinting summary appears |  |  |
| CSV viewer loads files | CSV tabs/content appear |  |  |
| Plot viewer loads images | Plots appear correctly |  |  |
| Open results folder | Folder opens in file explorer |  |  |
| Open HTML report | HTML report opens |  |  |
| Open TXT report | TXT report opens |  |  |
| Missing report auto-generation | Old session report is generated if possible |  |  |

---

## 11. History Page Test

| Test | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Open History page | Previous sessions are listed |  |  |
| Select old session | Details are displayed |  |  |
| Open selected session in dashboard | Session loads into Results Dashboard |  |  |
| Open session folder | Folder opens correctly |  |  |
| Delete test session | Session is deleted after confirmation |  |  |
| Refresh history | List updates correctly |  |  |

---

## 12. File and Folder Output Test

Check one saved session folder.

| Expected Folder/File | Exists? | Notes |
|---|---|---|
| `CSV/` |  |  |
| `Plots/` |  |  |
| `Reports/` |  |  |
| `recording_metadata.json` |  |  |
| `CSV/joint_angles_2d.csv` |  |  |
| `CSV/depth_data.csv` |  |  |
| `CSV/phase_summary.csv` |  |  |
| `CSV/analysis_summary.csv` |  |  |
| `CSV/lift_summary.csv` or sprint summary |  |  |
| `Reports/analysis_report.txt` |  |  |
| `Reports/analysis_report.html` |  |  |

---

## 13. Error Handling Test

| Test | Expected Result | Pass/Fail | Notes |
|---|---|---|---|
| Start recording without file in file mode | Warning appears |  |  |
| Stop recording without active recording | Warning appears |  |  |
| Change file while recording | Warning appears |  |  |
| Stop preview while recording | Warning appears |  |  |
| Back while recording | Warning appears |  |  |
| Back while preview active | Confirmation appears |  |  |

---

## 14. Final Commit Checklist

Before committing:

```bash
git status
python main.py
```

Confirm:

| Item | Done |
|---|---|
| App starts correctly |  |
| Weightlifting test passed |  |
| Sprinting test passed |  |
| Reports open correctly |  |
| History reload works |  |
| No unwanted generated files are staged |  |
| `.gitignore` is working |  |

Commit command:

```bash
git add .
git commit -m "Add README and testing checklist"
git push origin main
```

---

## Final Notes

Any failed test should be fixed before creating a release tag or packaging the application.
