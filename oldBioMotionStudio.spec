# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

project_root = Path.cwd()

datas = []
binaries = []
hiddenimports = []

# App assets
if (project_root / "assets").exists():
    datas.append(("assets", "assets"))

# MediaPipe often needs model/data files and hidden imports.
try:
    datas += collect_data_files("mediapipe")
    hiddenimports += collect_submodules("mediapipe")
except Exception:
    pass

# Matplotlib needs its mpl-data folder when bundled.
try:
    datas += collect_data_files("matplotlib")
except Exception:
    pass

# RealSense runtime DLLs, when available in the environment.
try:
    binaries += collect_dynamic_libs("pyrealsense2")
    hiddenimports += collect_submodules("pyrealsense2")
except Exception:
    hiddenimports += ["pyrealsense2"]

# OpenCV binaries, when available.
try:
    binaries += collect_dynamic_libs("cv2")
except Exception:
    pass

hiddenimports += [
    "cv2",
    "numpy",
    "pandas",
    "matplotlib",
    "matplotlib.backends.backend_agg",
    "matplotlib.backends.backend_qtagg",
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "pyqtgraph",
    "scipy",
    "reportlab",
    "PIL",
    "modules.interlimb_coordination_analyzer",
    "modules.report_generator",
    "modules.database_manager",
    "modules.phase_definitions",
]

# Remove duplicates while preserving order.
hiddenimports = list(dict.fromkeys(hiddenimports))

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "tkinter",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BioMotion Studio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/app_icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="BioMotionStudio_Release",
)
