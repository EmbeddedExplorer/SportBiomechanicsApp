from pathlib import Path
import sys

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QListWidget,
    QGroupBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


def resource_path(relative_path):
    """Return an asset path for source and PyInstaller builds."""

    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).resolve().parent.parent

    return base_path / relative_path


class HomePage(QWidget):
    def __init__(
        self,
        on_weightlifting,
        on_sprinting,
        on_live_tracking,
        on_results,
        on_history,
        on_about,
        on_exit
    ):
        super().__init__()

        self.recent_list = QListWidget()
        self.status_label = QLabel("System status loading...")
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("StatusText")

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(24, 18, 24, 18)
        main_layout.setSpacing(22)

        # ======================================================
        # LEFT NAVIGATION PANEL
        # ======================================================
        nav_panel = QFrame()
        nav_panel.setObjectName("NavPanel")
        nav_panel.setMinimumWidth(250)
        nav_panel.setMaximumWidth(300)

        nav_layout = QVBoxLayout()
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        nav_layout.setSpacing(11)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_path = resource_path("assets/logo.png")

        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            logo_label.setPixmap(
                pixmap.scaled(
                    105,
                    105,
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

        version = QLabel("v0.93 Beta")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setObjectName("VersionLabel")

        btn_weightlifting = QPushButton("Weightlifting Analysis")
        btn_sprinting = QPushButton("Sprinting Analysis")
        btn_live_tracking = QPushButton("Live Tracking")
        btn_results = QPushButton("Results Dashboard")
        btn_history = QPushButton("Analysis History")
        btn_about = QPushButton("About")
        btn_exit = QPushButton("Exit")

        buttons = [
            btn_weightlifting,
            btn_sprinting,
            btn_live_tracking,
            btn_results,
            btn_history,
            btn_about,
            btn_exit
        ]

        for btn in buttons:
            btn.setMinimumHeight(42)
            btn.setMaximumHeight(44)
            btn.setObjectName("MainButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_weightlifting.clicked.connect(on_weightlifting)
        btn_sprinting.clicked.connect(on_sprinting)
        btn_live_tracking.clicked.connect(on_live_tracking)
        btn_results.clicked.connect(on_results)
        btn_history.clicked.connect(on_history)
        btn_about.clicked.connect(on_about)
        btn_exit.clicked.connect(on_exit)

        nav_layout.addWidget(logo_label)
        nav_layout.addWidget(title)
        nav_layout.addWidget(version)
        nav_layout.addSpacing(6)

        nav_layout.addWidget(btn_weightlifting)
        nav_layout.addWidget(btn_sprinting)
        nav_layout.addWidget(btn_live_tracking)
        nav_layout.addWidget(btn_results)
        nav_layout.addWidget(btn_history)
        nav_layout.addWidget(btn_about)

        nav_layout.addStretch()
        nav_layout.addWidget(btn_exit)

        nav_panel.setLayout(nav_layout)

        # ======================================================
        # RIGHT DASHBOARD AREA
        # ======================================================
        dashboard_panel = QFrame()
        dashboard_panel.setObjectName("DashboardPanel")

        dashboard_layout = QVBoxLayout()
        dashboard_layout.setSpacing(10)

        heading = QLabel("BIOMOTION STUDIO")
        heading.setObjectName("DashboardTitle")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(
            "Biomechanics Analysis Platform for Weightlifting, Sprinting, and Live Pose Tracking"
        )
        subtitle.setObjectName("DashboardSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        department = QLabel(
            "Department of Physics, University of Sri Jayewardenepura"
        )
        department.setObjectName("DepartmentLabel")
        department.setAlignment(Qt.AlignmentFlag.AlignCenter)
        department.setWordWrap(True)

        # ======================================================
        # FEATURE CARDS
        # ======================================================
        feature_cards_layout = QHBoxLayout()
        feature_cards_layout.setSpacing(10)

        weightlifting_card = self.create_info_card(
            title="Weightlifting",
            body=(
                "Snatch and Clean & Jerk analysis with phase detection, "
                "barbell trajectory, joint angles, plots, and reports."
            )
        )

        sprinting_card = self.create_info_card(
            title="Sprinting",
            body=(
                "Sprinting phase detection with joint-angle tracking, "
                "depth profile analysis, sprinting plots, and reports."
            )
        )

        outputs_card = self.create_info_card(
            title="Outputs",
            body=(
                "Live RealSense RGB/depth review, CSV exports, plot viewer, "
                "HTML/TXT reports, and analysis history reload."
            )
        )

        feature_cards_layout.addWidget(weightlifting_card)
        feature_cards_layout.addWidget(sprinting_card)
        feature_cards_layout.addWidget(outputs_card)

        # ======================================================
        # STATUS + RECENT SESSIONS
        # ======================================================
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(10)

        status_group = QGroupBox("System Status")
        status_group.setMaximumHeight(170)
        status_layout = QVBoxLayout()
        status_layout.setSpacing(4)
        status_layout.addWidget(self.status_label)
        status_group.setLayout(status_layout)

        recent_group = QGroupBox("Recent Sessions")
        recent_group.setMaximumHeight(190)
        recent_layout = QVBoxLayout()
        recent_layout.setSpacing(4)
        self.recent_list.setMinimumHeight(110)
        self.recent_list.setMaximumHeight(130)
        recent_layout.addWidget(self.recent_list)
        recent_group.setLayout(recent_layout)

        middle_layout.addWidget(status_group, 1)
        middle_layout.addWidget(recent_group, 2)

        # ======================================================
        # QUICK GUIDE
        # ======================================================
        quick_group = QGroupBox("Quick Guide")
        quick_group.setMaximumHeight(105)
        quick_layout = QVBoxLayout()

        quick_text = QLabel(
            "Select an analysis module or Live Tracking → verify the camera and pose → "
            "track selected angles → review outputs, reports, and history."
        )
        quick_text.setObjectName("InfoText")
        quick_text.setWordWrap(True)

        quick_layout.addWidget(quick_text)
        quick_group.setLayout(quick_layout)

        footer = QLabel(
            "Built by Department of Physics, University of Sri Jayewardenepura  |  Contact: kknugawela@gmail.com"
        )
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setObjectName("FooterLabel")
        footer.setWordWrap(True)

        dashboard_layout.addWidget(heading)
        dashboard_layout.addWidget(subtitle)
        dashboard_layout.addWidget(department)
        dashboard_layout.addLayout(feature_cards_layout)
        dashboard_layout.addLayout(middle_layout)
        dashboard_layout.addWidget(quick_group)
        dashboard_layout.addStretch()
        dashboard_layout.addWidget(footer)

        dashboard_panel.setLayout(dashboard_layout)

        main_layout.addWidget(nav_panel, 1)
        main_layout.addWidget(dashboard_panel, 4)

        self.setLayout(main_layout)

        self.apply_styles()

    # ==========================================================
    # SMALL INFO CARD
    # ==========================================================
    def create_info_card(self, title, body):
        frame = QFrame()
        frame.setObjectName("InfoCard")
        frame.setMaximumHeight(120)
        frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)

        body_label = QLabel(body)
        body_label.setObjectName("CardBody")
        body_label.setWordWrap(True)
        body_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(title_label)
        layout.addWidget(body_label)

        frame.setLayout(layout)

        return frame

    # ==========================================================
    # UPDATE RECENT SESSIONS
    # ==========================================================
    def set_recent_sessions(self, sessions):
        self.recent_list.clear()

        if not sessions:
            self.recent_list.addItem("No previous sessions found.")
            return

        for session in sessions[:5]:
            created_at = session.get("created_at", "N/A")
            sport = session.get("sport", "N/A")
            exercise = session.get("exercise", "N/A")
            camera_view = session.get("camera_view", "N/A")

            text = (
                f"{created_at}  |  "
                f"{sport}  |  "
                f"{exercise}  |  "
                f"{camera_view}"
            )

            self.recent_list.addItem(text)

    # ==========================================================
    # UPDATE SYSTEM STATUS
    # ==========================================================
    def set_system_status(self, status_text):
        if not status_text:
            self.status_label.setText("System status unavailable.")
            return

        parts = [part.strip() for part in status_text.split("|") if part.strip()]

        if not parts:
            self.status_label.setText(status_text)
            return

        display_text = ""

        for part in parts:
            if "Ready" in part or "Connected" in part:
                display_text += f"✓ {part}\n"
            elif "Not Ready" in part:
                display_text += f"• {part}\n"
            else:
                display_text += f"• {part}\n"

        self.status_label.setText(display_text.strip())

    # ==========================================================
    # STYLES
    # ==========================================================
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #101820;
                color: white;
                font-family: Segoe UI;
            }

            QFrame#NavPanel {
                background-color: #1E2A35;
                border-radius: 16px;
                padding: 14px;
            }

            QFrame#DashboardPanel {
                background-color: #16222E;
                border-radius: 16px;
                padding: 18px;
            }

            QLabel#LogoText {
                background-color: #0078D7;
                color: white;
                font-size: 36px;
                font-weight: bold;
                border-radius: 48px;
                min-width: 96px;
                min-height: 96px;
                max-width: 96px;
                max-height: 96px;
            }

            QLabel#SideTitle {
                color: #00D4FF;
                font-size: 23px;
                font-weight: bold;
                letter-spacing: 1px;
            }

            QLabel#VersionLabel {
                color: #B8C7D3;
                font-size: 13px;
                font-weight: bold;
            }

            QLabel#DashboardTitle {
                color: #00D4FF;
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 2px;
            }

            QLabel#DashboardSubtitle {
                color: #E0E0E0;
                font-size: 16px;
                font-weight: bold;
            }

            QLabel#DepartmentLabel {
                color: #B8C7D3;
                font-size: 13px;
            }

            QFrame#InfoCard {
                background-color: #1E2A35;
                border: 1px solid #0078D7;
                border-radius: 10px;
            }

            QLabel#CardTitle {
                color: #00D4FF;
                font-size: 15px;
                font-weight: bold;
            }

            QLabel#CardBody {
                color: #E0E0E0;
                font-size: 12px;
                line-height: 1.3;
            }

            QLabel#InfoText {
                color: #E0E0E0;
                font-size: 13px;
                line-height: 1.4;
            }

            QLabel#StatusText {
                color: #E0E0E0;
                font-size: 13px;
                line-height: 1.4;
            }

            QLabel#FooterLabel {
                color: #B8C7D3;
                font-size: 11px;
                padding-top: 2px;
            }

            QGroupBox {
                border: 2px solid #0078D7;
                border-radius: 9px;
                margin-top: 10px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 7px;
                color: #00D4FF;
            }

            QListWidget {
                background-color: #1E2A35;
                color: white;
                border: 1px solid #0078D7;
                border-radius: 6px;
                padding: 6px;
                font-size: 12px;
            }

            QListWidget::item {
                padding: 4px;
            }

            QListWidget::item:selected {
                background-color: #0078D7;
                color: white;
            }

            QPushButton#MainButton {
                background-color: #0078D7;
                color: white;
                border-radius: 9px;
                font-size: 14px;
                font-weight: bold;
                padding: 7px;
            }

            QPushButton#MainButton:hover {
                background-color: #0099FF;
            }

            QPushButton#MainButton:pressed {
                background-color: #005A9E;
            }
        """)