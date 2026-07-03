import time
from pathlib import Path

import pandas as pd

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QGroupBox,
    QFileDialog,
    QMessageBox,
    QGridLayout,
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from modules.video_thread import VideoThread
from modules.result_manager import create_session_folder
from modules.analysis_recorder import AnalysisRecorder


class SprintingPage(QWidget):
    def __init__(self, on_back, on_start_analysis):
        super().__init__()

        self.on_back = on_back
        self.on_start_analysis = on_start_analysis

        self.selected_file = ""
        self.video_thread = None

        self.metric_labels = {}

        self.is_recording = False
        self.recorder = None
        self.current_session_path = None

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(6)

        title = QLabel("SPRINTING BIOMECHANICS ANALYSIS")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("PageTitle")

        input_group = QGroupBox("Select Input Source")
        input_layout = QVBoxLayout()
        input_layout.setSpacing(4)

        self.radio_realsense_live = QRadioButton("Live RealSense RGB-D Camera")
        self.radio_bag = QRadioButton("Pre-recorded RealSense .bag File")
        self.radio_video = QRadioButton("Side-view Video File")

        self.radio_realsense_live.setChecked(True)

        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("FileLabel")
        self.file_label.setWordWrap(True)

        btn_select_file = QPushButton("Select Video / .bag File")
        btn_select_file.clicked.connect(self.select_input_file)

        input_layout.addWidget(self.radio_realsense_live)
        input_layout.addWidget(self.radio_bag)
        input_layout.addWidget(self.radio_video)
        input_layout.addWidget(btn_select_file)
        input_layout.addWidget(self.file_label)

        input_group.setLayout(input_layout)

        preview_group = QGroupBox("Live Preview / Tracking View")
        preview_group.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        preview_layout = QVBoxLayout()
        preview_layout.setSpacing(6)

        self.video_label = QLabel("Video preview will appear here.")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 300)
        self.video_label.setMaximumHeight(430)
        self.video_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Ignored
        )
        self.video_label.setScaledContents(False)
        self.video_label.setObjectName("VideoLabel")

        self.status_label = QLabel("Status: Ready")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)

        preview_buttons = QHBoxLayout()
        preview_buttons.setSpacing(8)

        btn_start_preview = QPushButton("Start Preview")
        btn_stop_preview = QPushButton("Stop Preview")

        btn_start_preview.clicked.connect(self.start_preview)
        btn_stop_preview.clicked.connect(self.stop_preview)

        preview_buttons.addWidget(btn_start_preview)
        preview_buttons.addWidget(btn_stop_preview)

        preview_layout.addWidget(self.video_label, 1)
        preview_layout.addWidget(self.status_label)
        preview_layout.addLayout(preview_buttons)

        preview_group.setLayout(preview_layout)

        metrics_group = self.create_metrics_group()
        metrics_group.setMinimumWidth(300)
        metrics_group.setMaximumWidth(360)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)
        content_layout.addWidget(preview_group, 4)
        content_layout.addWidget(metrics_group, 1)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        btn_back = QPushButton("Back")
        self.btn_start_recording = QPushButton("Start Analysis Recording")
        self.btn_stop_recording = QPushButton("Stop & Save Analysis")

        self.btn_stop_recording.setEnabled(False)

        btn_back.clicked.connect(self.go_back)
        self.btn_start_recording.clicked.connect(self.start_analysis_recording)
        self.btn_stop_recording.clicked.connect(self.stop_and_save_analysis)

        button_layout.addWidget(btn_back)
        button_layout.addWidget(self.btn_start_recording)
        button_layout.addWidget(self.btn_stop_recording)

        main_layout.addWidget(title)
        main_layout.addWidget(input_group)
        main_layout.addLayout(content_layout, 1)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.apply_styles()

    # ==========================================================
    # FILE DIALOG
    # ==========================================================
    def open_file_dialog_non_native(self, title, file_filter):
        dialog = QFileDialog(self)
        dialog.setWindowTitle(title)
        dialog.setNameFilter(file_filter)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)

        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_files = dialog.selectedFiles()

            if selected_files:
                return selected_files[0]

        return ""

    # ==========================================================
    # METRICS UI
    # ==========================================================
    def create_metrics_group(self):
        metrics_group = QGroupBox("Live Biomechanics Metrics")
        metrics_group.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding
        )

        metrics_layout = QGridLayout()
        metrics_layout.setContentsMargins(8, 8, 8, 8)
        metrics_layout.setHorizontalSpacing(8)
        metrics_layout.setVerticalSpacing(4)

        metric_names = [
            "Pose",
            "Phase",

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

    # ==========================================================
    # INPUT SOURCE
    # ==========================================================
    def select_input_file(self):
        if self.is_recording:
            QMessageBox.warning(
                self,
                "Recording Active",
                "Please stop and save the analysis before changing the input file."
            )
            return

        if self.video_thread is not None:
            if not self._stop_preview_internal(reset_metrics=True):
                QMessageBox.warning(
                    self,
                    "Preview Still Closing",
                    "Please wait until the current preview fully stops before changing the file."
                )
                return

        if self.radio_bag.isChecked():
            file_filter = "RealSense Bag Files (*.bag);;All Files (*)"
            title = "Select RealSense Bag File"
        else:
            file_filter = (
                "Video Files (*.mp4 *.avi *.mov *.mkv);;"
                "RealSense Bag Files (*.bag);;"
                "All Files (*)"
            )
            title = "Select Sprinting Video / Bag File"

        file_path = self.open_file_dialog_non_native(
            title=title,
            file_filter=file_filter
        )

        if file_path:
            self.selected_file = file_path
            self.file_label.setText(file_path)

            if file_path.lower().endswith(".bag"):
                self.radio_bag.setChecked(True)
            else:
                self.radio_video.setChecked(True)

            self.status_label.setText("Status: Input file selected.")

    def get_source_type(self):
        if self.radio_realsense_live.isChecked():
            return "realsense_live"

        if self.radio_bag.isChecked():
            return "realsense_bag"

        return "video_file"

    def get_input_mode(self):
        source_type = self.get_source_type()

        if source_type == "realsense_live":
            return "Live RealSense RGB-D Camera"

        if source_type == "realsense_bag":
            return "RealSense Bag File"

        return "Side-view Video File"

    # ==========================================================
    # PREVIEW CONTROL
    # ==========================================================
    def start_preview(self):
        if self.is_recording:
            QMessageBox.warning(
                self,
                "Recording Active",
                "Please stop and save the analysis before restarting preview."
            )
            return

        if self.video_thread is not None:
            if not self._stop_preview_internal(reset_metrics=False):
                QMessageBox.warning(
                    self,
                    "Preview Still Closing",
                    "Please wait until the current preview fully stops before starting again."
                )
                return

        source_type = self.get_source_type()

        if source_type in ["realsense_bag", "video_file"] and not self.selected_file:
            QMessageBox.warning(
                self,
                "File Required",
                "Please select a video or .bag file first."
            )
            return

        self.video_thread = VideoThread(
            source_type=source_type,
            file_path=self.selected_file,
            sport="Sprinting",
            exercise="Sprinting",
            camera_view="Side View",
            barbell_roi=None
        )

        self.video_thread.frame_ready.connect(self.update_video_frame)
        self.video_thread.status_ready.connect(self.update_status)
        self.video_thread.metrics_ready.connect(self.update_metrics)

        self.video_thread.start()

    def stop_preview(self):
        if self.is_recording:
            QMessageBox.warning(
                self,
                "Recording Active",
                "Please use Stop & Save Analysis before stopping preview."
            )
            return

        self._stop_preview_internal(reset_metrics=True)

    def _stop_preview_internal(self, reset_metrics=True):
        if self.video_thread is not None:
            thread = self.video_thread
            thread.stop()

            deadline = time.time() + 3.0

            while thread.isRunning() and time.time() < deadline:
                QApplication.processEvents()
                thread.wait(100)

            if thread.isRunning():
                self.status_label.setText(
                    "Status: Previous preview is still closing. Please wait."
                )
                return False

            self.video_thread = None

        self.video_label.clear()
        self.video_label.setText("Video preview will appear here.")

        if reset_metrics:
            self.reset_metrics()

        self.status_label.setText("Status: Preview stopped.")

        return True

    # ==========================================================
    # LIVE DISPLAY
    # ==========================================================
    def update_video_frame(self, q_img):
        pixmap = QPixmap.fromImage(q_img)

        label_width = self.video_label.width()
        label_height = self.video_label.height()

        if label_width <= 0 or label_height <= 0:
            label_width = 640
            label_height = 360

        scaled_pixmap = pixmap.scaled(
            label_width,
            label_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.video_label.setPixmap(scaled_pixmap)

    def update_status(self, text):
        self.status_label.setText(f"Status: {text}")

    def update_metrics(self, metrics):
        for name, label in self.metric_labels.items():
            value = metrics.get(name, None)
            label.setText(self.format_metric_value(name, value))

        if self.is_recording and self.recorder is not None:
            self.recorder.add_metrics(metrics)

            self.status_label.setText(
                f"Status: Recording analysis... Samples: {self.recorder.record_count()}"
            )

    def reset_metrics(self):
        for label in self.metric_labels.values():
            label.setText("N/A")

    def format_metric_value(self, name, value):
        if value is None:
            return "N/A"

        if name in ["Pose", "Phase"]:
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

    # ==========================================================
    # ANALYSIS RECORDING
    # ==========================================================
    def start_analysis_recording(self):
        source_type = self.get_source_type()

        if source_type in ["realsense_bag", "video_file"] and not self.selected_file:
            QMessageBox.warning(
                self,
                "File Required",
                "Please select a video or .bag file before starting analysis."
            )
            return

        if self.video_thread is None:
            self.start_preview()

        if self.video_thread is None:
            return

        input_mode = self.get_input_mode()

        self.current_session_path = create_session_folder(
            sport="Sprinting",
            exercise="Sprinting",
            input_mode=input_mode,
            source_file=self.selected_file
        )

        self.recorder = AnalysisRecorder(
            session_path=self.current_session_path,
            sport="Sprinting",
            exercise="Sprinting",
            input_mode=input_mode,
            source_file=self.selected_file,
            camera_view="Side View"
        )

        self.recorder.start()
        self.is_recording = True

        self.btn_start_recording.setEnabled(False)
        self.btn_stop_recording.setEnabled(True)

        self.status_label.setText("Status: Recording analysis started.")

    def stop_and_save_analysis(self):
        if not self.is_recording or self.recorder is None:
            QMessageBox.warning(
                self,
                "No Active Recording",
                "There is no active analysis recording to save."
            )
            return

        self.is_recording = False

        if self.recorder.record_count() == 0:
            QMessageBox.warning(
                self,
                "No Data Recorded",
                "No metrics were recorded. Please make sure pose detection is working."
            )

            self.btn_start_recording.setEnabled(True)
            self.btn_stop_recording.setEnabled(False)
            return

        output_info = self.recorder.save_outputs()

        self.btn_start_recording.setEnabled(True)
        self.btn_stop_recording.setEnabled(False)

        self._stop_preview_internal(reset_metrics=False)

        session_info = self.build_enhanced_session_info(output_info)

        self.on_start_analysis(session_info)

    # ==========================================================
    # ENHANCED SESSION INFO FOR RESULTS DASHBOARD
    # ==========================================================
    def safe_csv_value(self, value):
        try:
            if pd.isna(value):
                return ""
        except Exception:
            pass

        try:
            if hasattr(value, "item"):
                return value.item()
        except Exception:
            pass

        return value

    def read_first_row_csv(self, csv_path):
        csv_path = Path(csv_path)

        if not csv_path.exists():
            return {}

        try:
            df = pd.read_csv(csv_path)

            if df.empty:
                return {}

            row = df.iloc[0].to_dict()
            clean_row = {}

            for key, value in row.items():
                clean_row[key] = self.safe_csv_value(value)

            return clean_row

        except Exception:
            return {}

    def existing_file_path(self, *path_parts):
        if self.current_session_path is None:
            return ""

        file_path = Path(self.current_session_path)

        for part in path_parts:
            file_path = file_path / part

        if file_path.exists():
            return str(file_path)

        return ""

    def build_phase_list_from_csv(self, csv_path):
        csv_path = Path(csv_path)

        if not csv_path.exists():
            return ""

        try:
            df = pd.read_csv(csv_path)

            if df.empty:
                return ""

            possible_phase_columns = [
                "phase",
                "Phase",
                "phase_name",
                "Phase Name"
            ]

            phase_column = None

            for column in possible_phase_columns:
                if column in df.columns:
                    phase_column = column
                    break

            if phase_column is None:
                return ""

            phases = []

            for value in df[phase_column].dropna().tolist():
                value = str(value).strip()

                if value and value not in phases and value != "Not Detected":
                    phases.append(value)

            return ", ".join(phases)

        except Exception:
            return ""

    def build_enhanced_session_info(self, output_info):
        if output_info is None:
            output_info = {}

        session_path = Path(
            output_info.get("session_path")
            or self.current_session_path
            or ""
        )

        self.current_session_path = session_path

        csv_folder = session_path / "CSV"
        plots_folder = session_path / "Plots"
        reports_folder = session_path / "Reports"

        lift_summary_path = csv_folder / "lift_summary.csv"
        phase_summary_path = csv_folder / "phase_summary.csv"
        phase_biomechanics_path = csv_folder / "phase_biomechanics_summary.csv"
        analysis_summary_path = csv_folder / "analysis_summary.csv"
        joint_angles_path = csv_folder / "joint_angles_2d.csv"
        depth_data_path = csv_folder / "depth_data.csv"
        barbell_trajectory_path = csv_folder / "barbell_trajectory.csv"

        lift_summary = self.read_first_row_csv(lift_summary_path)

        detected_phases = lift_summary.get("detected_phases", "")

        if not detected_phases:
            detected_phases = self.build_phase_list_from_csv(phase_summary_path)

        csv_files = {
            "sprint_summary": str(lift_summary_path) if lift_summary_path.exists() else "",
            "phase_biomechanics_summary": str(phase_biomechanics_path) if phase_biomechanics_path.exists() else "",
            "phase_summary": str(phase_summary_path) if phase_summary_path.exists() else "",
            "analysis_summary": str(analysis_summary_path) if analysis_summary_path.exists() else "",
            "joint_angles_2d": str(joint_angles_path) if joint_angles_path.exists() else "",
            "depth_data": str(depth_data_path) if depth_data_path.exists() else "",
            "trajectory_data": str(barbell_trajectory_path) if barbell_trajectory_path.exists() else ""
        }

        plot_files = {}

        if plots_folder.exists():
            for plot_path in sorted(plots_folder.glob("*.png")):
                plot_files[plot_path.stem] = str(plot_path)

        record_count = (
            output_info.get("record_count")
            or lift_summary.get("record_count")
            or 0
        )

        session_info = {
            "sport": "Sprinting",
            "exercise": "Sprinting",
            "camera_view": "Side View",
            "input_mode": self.get_input_mode(),
            "source_file": self.selected_file,
            "results_folder": str(session_path),
            "session_path": str(session_path),
            "csv_folder": str(csv_folder),
            "plots_folder": str(plots_folder),
            "reports_folder": str(reports_folder),
            "record_count": record_count,
            "csv_file": output_info.get("csv_file", str(joint_angles_path)),
            "csv_files": csv_files,
            "plot_files": plot_files,

            # Keep this key because ResultsPage already reads lift_summary.csv.
            "lift_summary": lift_summary,

            # Sprinting-specific dashboard values.
            "total_duration_s": lift_summary.get("total_duration_s", ""),
            "detected_phase_count": lift_summary.get("detected_phase_count", ""),
            "detected_phases": detected_phases,

            # Depth-related values are useful for RealSense sprinting analysis.
            "mean_athlete_depth_m": lift_summary.get("mean_athlete_depth_m", ""),
            "mean_center_depth_m": lift_summary.get("mean_center_depth_m", ""),

            # Barbell fields are intentionally left empty for sprinting.
            # ResultsPage will show N/A for these unless later customized for sprinting.
            "barbell_detected_samples": lift_summary.get("barbell_detected_samples", ""),
            "max_barbell_height_px": lift_summary.get("max_barbell_height_px", ""),
            "max_barbell_height_m": lift_summary.get("max_barbell_height_m", ""),
            "max_vertical_velocity_px_s": lift_summary.get("max_vertical_velocity_px_s", ""),
            "max_vertical_velocity_m_s": lift_summary.get("max_vertical_velocity_m_s", ""),
            "max_horizontal_velocity_px_s": lift_summary.get("max_horizontal_velocity_px_s", ""),
            "max_horizontal_velocity_m_s": lift_summary.get("max_horizontal_velocity_m_s", "")
        }

        return session_info

    # ==========================================================
    # NAVIGATION
    # ==========================================================
    def go_back(self):
        if self.is_recording:
            QMessageBox.warning(
                self,
                "Recording Active",
                "Please stop and save the analysis before going back."
            )
            return

        self._stop_preview_internal(reset_metrics=True)
        self.on_back()

    def closeEvent(self, event):
        self._stop_preview_internal(reset_metrics=True)
        event.accept()

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
                font-size: 27px;
                font-weight: bold;
                color: #00D4FF;
                margin: 4px;
            }

            QGroupBox {
                border: 2px solid #0078D7;
                border-radius: 10px;
                margin: 5px;
                padding: 10px;
                font-size: 15px;
                font-weight: bold;
            }

            QRadioButton {
                font-size: 14px;
                padding: 3px;
            }

            QLabel#VideoLabel {
                background-color: #000000;
                color: #AAAAAA;
                border: 2px solid #0078D7;
                border-radius: 8px;
            }

            QLabel#StatusLabel {
                color: #00D4FF;
                font-size: 13px;
            }

            QLabel#MetricName {
                color: #D0D0D0;
                font-size: 12px;
            }

            QLabel#MetricValue {
                color: #00D4FF;
                font-size: 12px;
                font-weight: bold;
            }

            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 8px;
                padding: 7px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #0099FF;
            }

            QPushButton:disabled {
                background-color: #555555;
                color: #AAAAAA;
            }

            QLabel#FileLabel {
                color: #CFCFCF;
                font-size: 12px;
            }
        """)