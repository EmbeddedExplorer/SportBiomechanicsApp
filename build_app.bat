@echo off
setlocal

echo ============================================================
echo BioMotion Studio - Windows Build Script
echo ============================================================
echo.

cd /d "%~dp0"

if not exist ".biomec\Scripts\python.exe" (
    echo Creating virtual environment: .biomec
    py -3 -m venv .biomec
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call ".biomec\Scripts\activate.bat"

echo.
echo Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo Failed to upgrade pip tools.
    pause
    exit /b 1
)

echo.
echo Installing Windows requirements...
python -m pip install -r requirements_windows.txt
if errorlevel 1 (
    echo Failed to install requirements.
    pause
    exit /b 1
)

echo.
echo Installing PyInstaller...
python -m pip install pyinstaller
if errorlevel 1 (
    echo Failed to install PyInstaller.
    pause
    exit /b 1
)

echo.
echo Cleaning previous build outputs...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Building BioMotion Studio...
pyinstaller --clean --noconfirm BioMotionStudio.spec
if errorlevel 1 (
    echo.
    echo Build failed.
    echo Check the error messages above.
    pause
    exit /b 1
)

echo.
echo Copying release notes and first-run instructions...
if exist README_FIRST.txt copy /Y README_FIRST.txt "dist\BioMotionStudio_Release\README_FIRST.txt" >nul
if exist release_notes.md copy /Y release_notes.md "dist\BioMotionStudio_Release\release_notes.md" >nul

echo.
echo ============================================================
echo Build complete.
echo.
echo Run:
echo dist\BioMotionStudio_Release\BioMotion Studio.exe
echo ============================================================
echo.

pause
endlocal
