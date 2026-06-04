from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
)
from PyQt6.QtCore import Qt


class AboutPage(QWidget):
    def __init__(self, on_back):
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(20)

        title = QLabel("ABOUT BIOMOTION STUDIO")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("PageTitle")

        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setText("""
BioMotion Studio

Weightlifting & Sprinting Analysis

BioMotion Studio is a Python-based computer vision and biomechanics analysis platform designed for objective assessment of human movement in sports.

The system focuses on two major sports-analysis modules:

1. Weightlifting Analysis
   - Snatch analysis
   - Clean & Jerk analysis
   - RGB-D sensor input using Intel RealSense
   - RealSense .bag file support
   - Human pose estimation
   - Joint angle analysis
   - Barbell detection and tracking
   - Barbell trajectory and velocity estimation
   - Phase-wise biomechanical analysis

2. Sprinting Biomechanics Analysis
   - Side-view video analysis
   - Live camera tracking
   - Pose estimation
   - Joint angle analysis
   - Stride and motion analysis
   - Sprinting phase analysis

3. Results Management
   - Automatic session folder creation
   - CSV result saving
   - Plot generation
   - Results dashboard
   - Analysis history
   - SQLite database support

4. Future Development
   - Real-time feedback
   - Technique error detection
   - Athlete database
   - Machine-learning-based performance scoring
   - Coach feedback reports
   - Exhibition demonstration mode

Purpose

BioMotion Studio is developed for sports science demonstrations, physics exhibitions, biomechanical research, athlete technique analysis, and educational demonstrations of computer vision in human motion analysis.
        """)

        btn_back = QPushButton("Back to Home")
        btn_back.clicked.connect(on_back)

        layout.addWidget(title)
        layout.addWidget(about_text)
        layout.addWidget(btn_back)

        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #101820;
                color: white;
                font-family: Segoe UI;
                font-size: 15px;
            }

            QLabel#PageTitle {
                font-size: 30px;
                font-weight: bold;
                color: #00D4FF;
                margin: 20px;
            }

            QTextEdit {
                background-color: #1E2A35;
                color: white;
                border-radius: 10px;
                padding: 20px;
                font-size: 16px;
            }

            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #0099FF;
            }
        """)