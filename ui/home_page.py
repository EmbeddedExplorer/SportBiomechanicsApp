from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QListWidget, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


class HomePage(QWidget):
    def __init__(
        self,
        on_weightlifting,
        on_sprinting,
        on_results,
        on_history,
        on_about,
        on_exit
    ):
        super().__init__()

        self.recent_list = QListWidget()
        self.status_label = QLabel("System status loading...")
        self.status_label.setWordWrap(True)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(30)

        # ================= LEFT NAVIGATION PANEL =================
        nav_panel = QFrame()
        nav_panel.setObjectName("NavPanel")
        nav_layout = QVBoxLayout()
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        nav_layout.setSpacing(15)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_path = Path("assets") / "logo.png"

        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            logo_label.setPixmap(
                pixmap.scaled(
                    150,
                    150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            logo_label.setText("BM")
            logo_label.setObjectName("LogoText")

        title = QLabel("BIOMOTION\nSTUDIO")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("SideTitle")

        btn_weightlifting = QPushButton("Weightlifting Analysis")
        btn_sprinting = QPushButton("Sprinting Analysis")
        btn_history = QPushButton("Analysis History")
        btn_results = QPushButton("Results Dashboard")
        btn_about = QPushButton("About Project")
        btn_exit = QPushButton("Exit")

        buttons = [
            btn_weightlifting,
            btn_sprinting,
            btn_history,
            btn_results,
            btn_about,
            btn_exit
        ]

        for btn in buttons:
            btn.setMinimumHeight(48)
            btn.setObjectName("MainButton")

        btn_weightlifting.clicked.connect(on_weightlifting)
        btn_sprinting.clicked.connect(on_sprinting)
        btn_history.clicked.connect(on_history)
        btn_results.clicked.connect(on_results)
        btn_about.clicked.connect(on_about)
        btn_exit.clicked.connect(on_exit)

        nav_layout.addWidget(logo_label)
        nav_layout.addWidget(title)
        nav_layout.addSpacing(20)

        for btn in buttons:
            nav_layout.addWidget(btn)

        nav_layout.addStretch()
        nav_panel.setLayout(nav_layout)

        # ================= RIGHT DASHBOARD AREA =================
        dashboard_panel = QFrame()
        dashboard_panel.setObjectName("DashboardPanel")
        dashboard_layout = QVBoxLayout()
        dashboard_layout.setSpacing(20)

        heading = QLabel("BIOMOTION STUDIO")
        heading.setObjectName("DashboardTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(
            "Weightlifting & Sprinting Analysis using Computer Vision and RGB-D Sensing"
        )
        subtitle.setObjectName("DashboardSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout()
        status_layout.addWidget(self.status_label)
        status_group.setLayout(status_layout)

        recent_group = QGroupBox("Recent Analysis Sessions")
        recent_layout = QVBoxLayout()
        recent_layout.addWidget(self.recent_list)
        recent_group.setLayout(recent_layout)

        quick_info_group = QGroupBox("Platform Modules")
        quick_info_layout = QVBoxLayout()

        quick_info = QLabel(
            "✓ RGB-D Weightlifting Analysis\n"
            "✓ Snatch and Clean & Jerk Workflow\n"
            "✓ Sprinting Biomechanics Workflow\n"
            "✓ CSV Data Viewer\n"
            "✓ Plot Viewer\n"
            "✓ Automatic Result Folder Creation\n"
            "✓ SQLite Session Database"
        )
        quick_info.setObjectName("InfoText")

        quick_info_layout.addWidget(quick_info)
        quick_info_group.setLayout(quick_info_layout)

        dashboard_layout.addWidget(heading)
        dashboard_layout.addWidget(subtitle)
        dashboard_layout.addWidget(status_group)
        dashboard_layout.addWidget(recent_group)
        dashboard_layout.addWidget(quick_info_group)

        dashboard_panel.setLayout(dashboard_layout)

        main_layout.addWidget(nav_panel, 1)
        main_layout.addWidget(dashboard_panel, 3)

        self.setLayout(main_layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #101820;
                color: white;
                font-family: Segoe UI;
            }

            QFrame#NavPanel {
                background-color: #1E2A35;
                border-radius: 18px;
                padding: 20px;
            }

            QFrame#DashboardPanel {
                background-color: #16222E;
                border-radius: 18px;
                padding: 25px;
            }

            QLabel#LogoText {
                background-color: #0078D7;
                color: white;
                font-size: 42px;
                font-weight: bold;
                border-radius: 60px;
                min-width: 120px;
                min-height: 120px;
            }

            QLabel#SideTitle {
                color: #00D4FF;
                font-size: 24px;
                font-weight: bold;
            }

            QLabel#DashboardTitle {
                color: #00D4FF;
                font-size: 34px;
                font-weight: bold;
                letter-spacing: 2px;
            }

            QLabel#DashboardSubtitle {
                color: #D0D0D0;
                font-size: 17px;
            }

            QLabel#InfoText {
                color: #E0E0E0;
                font-size: 16px;
                line-height: 1.5;
            }

            QGroupBox {
                border: 2px solid #0078D7;
                border-radius: 10px;
                margin-top: 12px;
                padding: 15px;
                font-size: 17px;
                font-weight: bold;
                color: white;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: #00D4FF;
            }

            QListWidget {
                background-color: #1E2A35;
                color: white;
                border: 1px solid #0078D7;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }

            QPushButton#MainButton {
                background-color: #0078D7;
                color: white;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
                padding: 8px;
            }

            QPushButton#MainButton:hover {
                background-color: #0099FF;
            }
        """)

    def set_recent_sessions(self, sessions):
        self.recent_list.clear()

        if not sessions:
            self.recent_list.addItem("No previous sessions found.")
            return

        for session in sessions:
            text = (
                f"{session.get('created_at', '')} | "
                f"{session.get('sport', '')} | "
                f"{session.get('exercise', '')}"
            )
            self.recent_list.addItem(text)

    def set_system_status(self, status_text):
        self.status_label.setText(status_text)