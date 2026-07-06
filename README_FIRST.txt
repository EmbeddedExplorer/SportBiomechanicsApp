BioMotion Studio - First Run Guide
=================================

How to run the packaged app
---------------------------

Open this file:

    BioMotion Studio.exe

Expected release folder:

    BioMotionStudio_Release/
        BioMotion Studio.exe
        assets/
        README_FIRST.txt
        release_notes.md


Important notes
---------------

1. Keep the full BioMotionStudio_Release folder together.
   Do not move only the .exe file away from the folder.

2. Intel RealSense live mode requires:
   - Intel RealSense camera connected
   - RealSense drivers/runtime installed on the PC
   - A Windows environment that supports pyrealsense2

3. Recorded video/.bag analysis can be tested without a live camera.

4. Generated results are saved in the app results/session folders.

5. If Windows SmartScreen appears, choose:
   More info -> Run anyway
   This happens because the app is not code-signed yet.


Recommended testing after build
-------------------------------

1. Open the app.
2. Confirm Home page loads.
3. Open Weightlifting page.
4. Test one Snatch/Clean & Jerk recorded file.
5. Open Results Dashboard.
6. Open generated HTML report.
7. Open Sprinting page.
8. Run one sprinting analysis.
9. Confirm interlimb coordination plots appear in the report.


Troubleshooting
---------------

If the app does not start:
- Run from Command Prompt to see errors.
- Rebuild using build_app.bat.
- Confirm requirements_windows.txt installed correctly.
- Confirm assets/app_icon.ico exists before building.

If RealSense does not work:
- Confirm camera is connected.
- Confirm Intel RealSense Viewer can see the camera.
- Confirm pyrealsense2 is installed in the build environment.
