from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QGroupBox, QFileDialog, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from modules.video_thread import VideoThread


class WeightliftingPage(QWidget):
    def __init__(self, on_back, on_start_analysis):
        super().__init__()

        self.on_back = on_back
        self.on_start_analysis = on_start_analysis
        self.selected_file = ""
        self.video_thread = None
        self.metric_labels = {}

        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)

        title = QLabel("WEIGHTLIFTING BIOMECHANICS ANALYSIS")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("PageTitle")

        # ================= EXERCISE SELECTION =================
        exercise_group = QGroupBox("Select Exercise")
        exercise_layout = QVBoxLayout()

        self.radio_snatch = QRadioButton("Snatch")
        self.radio_clean_jerk = QRadioButton("Clean & Jerk")
        self.radio_snatch.setChecked(True)

        exercise_layout.addWidget(self.radio_snatch)
        exercise_layout.addWidget(self.radio_clean_jerk)
        exercise_group.setLayout(exercise_layout)

        # ================= INPUT SOURCE =================
        input_group = QGroupBox("Select Input Source")
        input_layout = QVBoxLayout()

        self.radio_realsense_live = QRadioButton("Live RealSense RGB-D Camera")
        self.radio_bag = QRadioButton("Pre-recorded RealSense .bag File")
        self.radio_webcam = QRadioButton("Webcam Fallback")
        self.radio_realsense_live.setChecked(True)

        self.file_label = QLabel("No .bag file selected")
        self.file_label.setObjectName("FileLabel")

        btn_select_file = QPushButton("Select .bag File")
        btn_select_file.clicked.connect(self.select_bag_file)

        input_layout.addWidget(self.radio_realsense_live)
        input_layout.addWidget(self.radio_bag)
        input_layout.addWidget(self.radio_webcam)
        input_layout.addWidget(btn_select_file)
        input_layout.addWidget(self.file_label)

        input_group.setLayout(input_layout)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(exercise_group)
        controls_layout.addWidget(input_group)

        # ================= VIDEO PREVIEW =================
        preview_group = QGroupBox("Live Preview / Tracking View")
        preview_layout = QVBoxLayout()

        self.video_label = QLabel("Video preview will appear here.")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 360)
        self.video_label.setObjectName("VideoLabel")

        self.status_label = QLabel("Status: Ready")
        self.status_label.setObjectName("StatusLabel")

        preview_buttons = QHBoxLayout()

        btn_start_preview = QPushButton("Start Preview")
        btn_stop_preview = QPushButton("Stop Preview")

        btn_start_preview.clicked.connect(self.start_preview)
        btn_stop_preview.clicked.connect(self.stop_preview)

        preview_buttons.addWidget(btn_start_preview)
        preview_buttons.addWidget(btn_stop_preview)

        preview_layout.addWidget(self.video_label)
        preview_layout.addWidget(self.status_label)
        preview_layout.addLayout(preview_buttons)

        preview_group.setLayout(preview_layout)

        # ================= METRICS PANEL =================
        metrics_group = self.create_metrics_group()

        content_layout = QHBoxLayout()
        content_layout.addWidget(preview_group, 3)
        content_layout.addWidget(metrics_group, 1)

        # ================= ACTION BUTTONS =================
        button_layout = QHBoxLayout()

        btn_back = QPushButton("Back")
        btn_start = QPushButton("Start Analysis")

        btn_back.clicked.connect(self.go_back)
        btn_start.clicked.connect(self.start_analysis)

        button_layout.addWidget(btn_back)
        button_layout.addWidget(btn_start)

        main_layout.addWidget(title)
        main_layout.addLayout(controls_layout)
        main_layout.addLayout(content_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.apply_styles()

    def create_metrics_group(self):
        metrics_group = QGroupBox("Live Biomechanics Metrics")
        metrics_layout = QGridLayout()

        metric_names = [
            "Pose",
            "Left Hip Angle",
            "Right Hip Angle",
            "Left Knee Angle",
            "Right Knee Angle",
            "Left Ankle Angle",
            "Right Ankle Angle",
            "Left Shoulder Angle",
            "Right Shoulder Angle",
            "Left Elbow Angle",
            "Right Elbow Angle",
            "Trunk Lean Angle",
            "Athlete Depth (m)",
            "Center Depth (m)"
        ]

        for row, name in enumerate(metric_names):
            name_label = QLabel(name)
            name_label.setObjectName("MetricName")

            value_label = QLabel("N/A")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            value_label.setObjectName("MetricValue")

            metrics_layout.addWidget(name_label, row, 0)
            metrics_layout.addWidget(value_label, row, 1)

            self.metric_labels[name] = value_label

        metrics_group.setLayout(metrics_layout)

        return metrics_group

    def select_bag_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select RealSense Bag File",
            "",
            "RealSense Bag Files (*.bag);;All Files (*)"
        )

        if file_path:
            self.selected_file = file_path
            self.file_label.setText(file_path)
            self.radio_bag.setChecked(True)

    def get_source_type(self):
        if self.radio_realsense_live.isChecked():
            return "realsense_live"

        if self.radio_bag.isChecked():
            return "realsense_bag"

        return "webcam"

    def start_preview(self):
        self.stop_preview()

        source_type = self.get_source_type()

        if source_type == "realsense_bag" and not self.selected_file:
            QMessageBox.warning(
                self,
                "File Required",
                "Please select a RealSense .bag file first."
            )
            return

        self.video_thread = VideoThread(
            source_type=source_type,
            file_path=self.selected_file
        )

        self.video_thread.frame_ready.connect(self.update_video_frame)
        self.video_thread.status_ready.connect(self.update_status)
        self.video_thread.metrics_ready.connect(self.update_metrics)

        self.video_thread.start()

    def stop_preview(self):
        if self.video_thread is not None:
            self.video_thread.stop()
            self.video_thread = None

        self.status_label.setText("Status: Preview stopped.")
        self.reset_metrics()

    def update_video_frame(self, q_img):
        pixmap = QPixmap.fromImage(q_img)

        self.video_label.setPixmap(
            pixmap.scaled(
                self.video_label.width(),
                self.video_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    def update_status(self, text):
        self.status_label.setText(f"Status: {text}")

    def update_metrics(self, metrics):
        for name, label in self.metric_labels.items():
            value = metrics.get(name, None)
            label.setText(self.format_metric_value(name, value))

    def reset_metrics(self):
        for label in self.metric_labels.values():
            label.setText("N/A")

    def format_metric_value(self, name, value):
        if value is None:
            return "N/A"

        if name == "Pose":
            return str(value)

        if "(m)" in name:
            try:
                return f"{float(value):.2f} m"
            except Exception:
                return "N/A"

        try:
            return f"{float(value):.1f}°"
        except Exception:
            return str(value)

    def start_analysis(self):
        exercise = "Snatch" if self.radio_snatch.isChecked() else "Clean & Jerk"

        source_type = self.get_source_type()

        if source_type == "realsense_live":
            input_mode = "Live RealSense RGB-D Camera"
        elif source_type == "realsense_bag":
            input_mode = "RealSense Bag File"
        else:
            input_mode = "Webcam Fallback"

        if source_type == "realsense_bag" and not self.selected_file:
            QMessageBox.warning(
                self,
                "File Required",
                "Please select a RealSense .bag file before starting analysis."
            )
            return

        self.on_start_analysis(exercise, input_mode, self.selected_file)

    def go_back(self):
        self.stop_preview()
        self.on_back()

    def closeEvent(self, event):
        self.stop_preview()
        event.accept()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #101820;
                color: white;
                font-family: Segoe UI;
                font-size: 15px;
            }

            QLabel#PageTitle {
                font-size: 28px;
                font-weight: bold;
                color: #00D4FF;
                margin: 8px;
            }

            QGroupBox {
                border: 2px solid #0078D7;
                border-radius: 10px;
                margin: 8px;
                padding: 14px;
                font-size: 16px;
                font-weight: bold;
            }

            QRadioButton {
                font-size: 14px;
                padding: 5px;
            }

            QLabel#VideoLabel {
                background-color: #000000;
                color: #AAAAAA;
                border: 2px solid #0078D7;
                border-radius: 8px;
            }

            QLabel#StatusLabel {
                color: #00D4FF;
                font-size: 14px;
            }

            QLabel#MetricName {
                color: #D0D0D0;
                font-size: 13px;
            }

            QLabel#MetricValue {
                color: #00D4FF;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 8px;
                padding: 9px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #0099FF;
            }

            QLabel#FileLabel {
                color: #CFCFCF;
                font-size: 13px;
            }
        """)