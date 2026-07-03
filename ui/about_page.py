from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QSizePolicy
)

from PyQt6.QtCore import Qt


class AboutPage(QWidget):
    def __init__(self, on_back):
        super().__init__()

        self.on_back = on_back

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(18, 12, 18, 12)
        main_layout.setSpacing(12)

        title = QLabel("ABOUT BIOMOTION STUDIO")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("PageTitle")

        subtitle = QLabel(
            "Biomechanics Analysis Platform for Weightlifting and Sprinting"
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("SubtitleLabel")

        # ======================================================
        # SCROLLABLE CONTENT
        # ======================================================
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("AboutScrollArea")

        content_widget = QWidget()
        content_widget.setObjectName("AboutContentWidget")

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(12)

        content_layout.addWidget(
            self.create_section(
                "Application Overview",
                """
                <p>
                    <b>BioMotion Studio</b> is a biomechanics analysis application designed for
                    motion tracking, phase detection, joint-angle analysis, depth-based measurement,
                    and movement-performance visualization.
                </p>
                <p>
                    The application supports analysis workflows for <b>Olympic weightlifting</b>
                    and <b>sprinting biomechanics</b> using video files, RealSense RGB-D recordings,
                    and live RealSense camera streams.
                </p>
                """
            )
        )

        content_layout.addWidget(
            self.create_section(
                "Version Information",
                """
                <table>
                    <tr><td><b>Application Name</b></td><td>BioMotion Studio</td></tr>
                    <tr><td><b>Version</b></td><td>v0.90 Beta</td></tr>
                    <tr><td><b>Development Stage</b></td><td>Final refinement and testing phase</td></tr>
                    <tr><td><b>Platform</b></td><td>Python, PyQt6, OpenCV, MediaPipe, Intel RealSense</td></tr>
                    <tr><td><b>Output Support</b></td><td>CSV files, plots, TXT reports, HTML reports, and session history</td></tr>
                </table>
                """
            )
        )

        content_layout.addWidget(
            self.create_section(
                "Built By",
                """
                <p>
                    Built by the <b>Department of Physics, University of Sri Jayewardenepura</b>.
                </p>
                <p>
                    This application was developed as a biomechanics analysis and research-support
                    tool for movement evaluation, teaching demonstrations, experimental analysis,
                    and academic research.
                </p>
                """
            )
        )

        content_layout.addWidget(
            self.create_section(
                "Developer / Contact",
                """
                <table>
                    <tr><td><b>Developer</b></td><td>Kulunu Kaushal Nugawela</td></tr>
                    <tr><td><b>Email</b></td><td>kknugawela@gmail.com</td></tr>
                    <tr><td><b>Affiliation</b></td><td>Department of Physics, University of Sri Jayewardenepura</td></tr>
                </table>
                """
            )
        )

        content_layout.addWidget(
            self.create_section(
                "Main Features",
                """
                <p><b>Weightlifting Analysis</b></p>
                <ul>
                    <li>Snatch and Clean & Jerk analysis workflows</li>
                    <li>Side-view and front-view support</li>
                    <li>Barbell trajectory tracking</li>
                    <li>Weightlifting phase detection</li>
                    <li>Joint-angle, trunk-lean, displacement, and velocity analysis</li>
                </ul>

                <p><b>Sprinting Analysis</b></p>
                <ul>
                    <li>Sprinting phase detection</li>
                    <li>Initial Contact, Support Phase, Toe-Off, and Flight / Swing identification</li>
                    <li>Hip, knee, ankle, shoulder, elbow, and trunk-angle tracking</li>
                    <li>Depth profile analysis when RGB-D data is available</li>
                    <li>Sprinting-specific CSV files, plots, and reports</li>
                </ul>

                <p><b>Result Management</b></p>
                <ul>
                    <li>Automatic session folder creation</li>
                    <li>CSV export for raw and summarized data</li>
                    <li>Phase-wise biomechanics summary generation</li>
                    <li>Sport-aware Results Dashboard</li>
                    <li>History page for reopening previous sessions</li>
                    <li>TXT and HTML report generation</li>
                </ul>
                """
            )
        )

        content_layout.addWidget(
            self.create_section(
                "Supported Input Sources",
                """
                <ul>
                    <li>Live Intel RealSense RGB-D camera</li>
                    <li>Pre-recorded RealSense .bag files</li>
                    <li>Standard video files such as MP4, AVI, MOV, and MKV</li>
                </ul>
                """
            )
        )

        content_layout.addWidget(
            self.create_section(
                "Generated Outputs",
                """
                <ul>
                    <li><b>CSV files</b> for joint angles, depth data, phase summaries, and movement metrics</li>
                    <li><b>Plots</b> for joint angles, barbell trajectory, sprinting phases, and depth profiles</li>
                    <li><b>Reports</b> in TXT and HTML formats</li>
                    <li><b>History records</b> for accessing previous analysis sessions</li>
                </ul>
                """
            )
        )

        content_layout.addWidget(
            self.create_section(
                "Research and Teaching Use",
                """
                <p>
                    BioMotion Studio is intended for biomechanics learning, laboratory demonstrations,
                    prototype research, and experimental movement analysis. The system helps visualize
                    motion patterns and summarize biomechanical variables from video or RGB-D sources.
                </p>
                <p>
                    For formal research use, the generated outputs should be reviewed together with
                    the original video, phase labels, tracking quality, and experimental conditions.
                </p>
                """
            )
        )

        content_layout.addWidget(
            self.create_section(
                "Important Note",
                """
                <p>
                    This software is a research and educational tool. Measurement accuracy depends on
                    camera position, lighting, pose visibility, calibration quality, input video quality,
                    and tracking stability. Results should be validated before formal biomechanical conclusions.
                </p>
                """
            )
        )

        content_layout.addStretch()

        content_widget.setLayout(content_layout)
        self.scroll_area.setWidget(content_widget)

        # ======================================================
        # BUTTONS
        # ======================================================
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        btn_back = QPushButton("Back to Home")
        btn_back.clicked.connect(self.on_back)

        button_layout.addStretch()
        button_layout.addWidget(btn_back)
        button_layout.addStretch()

        footer = QLabel(
            "BioMotion Studio  |  Department of Physics, University of Sri Jayewardenepura"
        )
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setObjectName("FooterLabel")

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)
        main_layout.addWidget(self.scroll_area, 1)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(footer)

        self.setLayout(main_layout)

        self.apply_styles()

    # ==========================================================
    # SECTION CARD
    # ==========================================================
    def create_section(self, heading, body_html):
        frame = QFrame()
        frame.setObjectName("SectionCard")
        frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        heading_label = QLabel(heading)
        heading_label.setObjectName("SectionHeading")
        heading_label.setWordWrap(True)

        body_label = QLabel(body_html)
        body_label.setObjectName("SectionBody")
        body_label.setTextFormat(Qt.TextFormat.RichText)
        body_label.setWordWrap(True)
        body_label.setOpenExternalLinks(False)

        layout.addWidget(heading_label)
        layout.addWidget(body_label)

        frame.setLayout(layout)

        return frame

    # ==========================================================
    # STYLES
    # ==========================================================
    def apply_styles(self):
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
                margin: 8px;
            }

            QLabel#SubtitleLabel {
                font-size: 17px;
                color: #C9D6DF;
                margin-bottom: 8px;
            }

            QScrollArea#AboutScrollArea {
                background-color: #101820;
                border: 1px solid #0078D7;
                border-radius: 8px;
            }

            QWidget#AboutContentWidget {
                background-color: #101820;
            }

            QFrame#SectionCard {
                background-color: #16232E;
                border: 1px solid #0078D7;
                border-radius: 10px;
            }

            QLabel#SectionHeading {
                color: #00D4FF;
                font-size: 18px;
                font-weight: bold;
            }

            QLabel#SectionBody {
                color: #E8F0F5;
                font-size: 14px;
                line-height: 1.5;
            }

            QLabel#SectionBody table {
                color: #E8F0F5;
            }

            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 8px;
                padding: 12px;
                font-size: 15px;
                font-weight: bold;
                min-width: 180px;
            }

            QPushButton:hover {
                background-color: #0099FF;
            }

            QPushButton:disabled {
                background-color: #555555;
                color: #AAAAAA;
            }

            QLabel#FooterLabel {
                color: #B8C7D3;
                font-size: 12px;
                padding: 4px;
            }
        """)