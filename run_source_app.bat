@echo off
setlocal

cd /d "%~dp0"

if not exist ".biomec\Scripts\activate.bat" (
    echo Virtual environment not found.
    echo Please run build_app.bat first or create/install the environment manually.
    pause
    exit /b 1
)

call ".biomec\Scripts\activate.bat"

python main.py

pause
endlocal
