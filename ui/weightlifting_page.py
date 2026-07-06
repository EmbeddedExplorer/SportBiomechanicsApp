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
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QFont

from modules.video_thread import VideoThread
from modules.result_manager import create_session_folder
from modules.analysis_recorder import AnalysisRecorder
from modules.roi_selector import (
    get_first_frame_from_bag,
    select_roi_from_frame
)



class TickRadioButton(QRadioButton):
    """
    Custom radio button that behaves like a normal QRadioButton
    but displays a clear green tick when selected.

    This keeps the existing .isChecked() logic unchanged.
    """

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(28)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        indicator_size = 22
        indicator_x = 2
        indicator_y = (self.height() - indicator_size) // 2

        indicator_rect = QRect(
            indicator_x,
            indicator_y,
            indicator_size,
            indicator_size
        )

        if self.isChecked():
            painter.setBrush(QColor("#00E676"))
            painter.setPen(QPen(QColor("#80FFB0"), 2))
            painter.drawRoundedRect(indicator_rect, 5, 5)

            tick_pen = QPen(QColor("#FFFFFF"), 3)
            tick_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            tick_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(tick_pen)

            painter.drawLine(
                indicator_x + 6,
                indicator_y + 12,
                indicator_x + 10,
                indicator_y + 17
            )
            painter.drawLine(
                indicator_x + 10,
                indicator_y + 17,
                indicator_x + 18,
                indicator_y + 7
            )

            text_color = QColor("#00E676")
            font = QFont(self.font())
            font.setBold(True)

        else:
            painter.setBrush(QColor("#101820"))
            painter.setPen(QPen(QColor("#00D4FF"), 2))
            painter.drawRoundedRect(indicator_rect, 5, 5)

            text_color = QColor("#EAF2F8")
            font = QFont(self.font())
            font.setBold(False)

        painter.setFont(font)
        painter.setPen(text_color)

        text_rect = self.rect().adjusted(indicator_size + 12, 0, 0, 0)

        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.text()
        )


class WeightliftingPage(QWidget):
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

        self.barbell_roi = None
        self.last_roi_key = None

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(6)

        title = QLabel("WEIGHTLIFTING BIOMECHANICS ANALYSIS")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("PageTitle")

        # ================= EXERCISE =================
        exercise_group = QGroupBox("Select Exercise")
        exercise_layout = QVBoxLayout()
        exercise_layout.setSpacing(4)

        self.radio_snatch = TickRadioButton("Snatch")
        self.radio_clean_jerk = TickRadioButton("Clean & Jerk")
        self.radio_snatch.setChecked(True)

        exercise_layout.addWidget(self.radio_snatch)
        exercise_layout.addWidget(self.radio_clean_jerk)
        exercise_group.setLayout(exercise_layout)

        # ================= VIEW =================
        view_group = QGroupBox("Select Camera View")
        view_layout = QVBoxLayout()
        view_layout.setSpacing(4)

        self.radio_side_view = TickRadioButton("Side View")
        self.radio_front_view = TickRadioButton("Front View")
        self.radio_side_view.setChecked(True)

        view_layout.addWidget(self.radio_side_view)
        view_layout.addWidget(self.radio_front_view)
        view_group.setLayout(view_layout)

        # ================= INPUT =================
        input_group = QGroupBox("Select Input Source")
        input_layout = QVBoxLayout()
        input_layout.setSpacing(4)

        self.radio_realsense_live = TickRadioButton("Live RealSense RGB-D Camera")
        self.radio_bag = TickRadioButton("Pre-recorded RealSense .bag File")
        self.radio_realsense_live.setChecked(True)

        self.file_label = QLabel("No .bag file selected")
        self.file_label.setObjectName("FileLabel")
        self.file_label.setWordWrap(True)

        btn_select_file = QPushButton("Select .bag File")
        btn_select_file.clicked.connect(self.select_bag_file)

        btn_select_roi = QPushButton("Select / Correct Barbell ROI")
        btn_select_roi.clicked.connect(self.select_barbell_roi)

        input_layout.addWidget(self.radio_realsense_live)
        input_layout.addWidget(self.radio_bag)
        input_layout.addWidget(btn_select_file)
        input_layout.addWidget(btn_select_roi)
        input_layout.addWidget(self.file_label)

        input_group.setLayout(input_layout)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        controls_layout.addWidget(exercise_group)
        controls_layout.addWidget(view_group)
        controls_layout.addWidget(input_group)

        # ================= PREVIEW =================
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

        # ================= METRICS =================
        metrics_group = self.create_metrics_group()
        metrics_group.setMinimumWidth(300)
        metrics_group.setMaximumWidth(420)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)
        content_layout.addWidget(preview_group, 4)
        content_layout.addWidget(metrics_group, 1)

        # ================= BOTTOM BUTTONS =================
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
        main_layout.addLayout(controls_layout)
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
    # UI HELPERS
    # ==========================================================
    def set_status(self, message):
        self.status_label.setText(f"Status: {message}")

    def update_file_label(self, file_path):
        if not file_path:
            self.file_label.setText("No .bag file selected")
            self.file_label.setToolTip("")
            return

        file_name = Path(file_path).name
        self.file_label.setText(f"Selected .bag file: {file_name}")
        self.file_label.setToolTip(str(file_path))

    def is_preview_active(self):
        return self.video_thread is not None and self.video_thread.isRunning()

    def confirm_stop_preview_before_leaving(self):
        if not self.is_preview_active():
            return True

        reply = QMessageBox.question(
            self,
            "Preview Active",
            (
                "A preview is currently running.\n\n"
                "Do you want to stop the preview and go back to Home?"
            )
        )

        return reply == QMessageBox.StandardButton.Yes

    # ==========================================================
    # METRICS GROUP
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

            "Barbell X (px)",
            "Barbell Y (px)",
            "Barbell Horizontal Displacement (px)",
            "Barbell Vertical Displacement (px)",
            "Barbell Vertical Velocity (px/s)",

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
    # SELECTION HELPERS
    # ==========================================================
    def is_side_view(self):
        return self.get_camera_view() == "Side View"

    def get_source_type(self):
        if self.radio_realsense_live.isChecked():
            return "realsense_live"

        return "realsense_bag"

    def get_exercise(self):
        return "Snatch" if self.radio_snatch.isChecked() else "Clean & Jerk"

    def get_camera_view(self):
        return "Side View" if self.radio_side_view.isChecked() else "Front View"

    def get_input_mode(self):
        source_type = self.get_source_type()

        if source_type == "realsense_live":
            return "Live RealSense RGB-D Camera"

        return "RealSense Bag File"

    def current_roi_key(self):
        return (
            self.get_exercise(),
            self.get_camera_view(),
            self.get_source_type(),
            self.selected_file
        )

    # ==========================================================
    # FILE SELECTION
    # ==========================================================
    def select_bag_file(self):
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

        file_path = self.open_file_dialog_non_native(
            title="Select RealSense Bag File",
            file_filter="RealSense Bag Files (*.bag);;All Files (*)"
        )

        if file_path:
            self.selected_file = file_path
            self.update_file_label(file_path)
            self.radio_bag.setChecked(True)

            self.barbell_roi = None
            self.last_roi_key = None

            self.set_status(
                ".bag file selected. Start preview for automatic detection, or select ROI manually."
            )

    # ==========================================================
    # ROI SELECTION
    # ==========================================================
    def select_barbell_roi(self):
        if self.is_recording:
            QMessageBox.warning(
                self,
                "Recording Active",
                "Please stop and save analysis before selecting ROI."
            )
            return

        if not self.is_side_view():
            QMessageBox.information(
                self,
                "ROI Not Required",
                "Barbell ROI is only used for Side View trajectory tracking.\n\n"
                "Front View uses pose-based phase detection and does not need ROI."
            )
            return

        first_frame = None

        # Preferred method: select ROI from currently running preview.
        if self.video_thread is not None and self.video_thread.isRunning():
            first_frame = self.video_thread.get_latest_frame_copy()

            if first_frame is None:
                QMessageBox.warning(
                    self,
                    "Frame Not Ready",
                    "Preview frame is not ready yet. Please wait a moment and try again."
                )
                return

        else:
            source_type = self.get_source_type()

            if source_type == "realsense_live":
                QMessageBox.information(
                    self,
                    "Start Preview First",
                    "For live RealSense, start preview first.\n\n"
                    "Then click 'Select / Correct Barbell ROI' using the current preview frame."
                )
                return

            if source_type == "realsense_bag":
                if not self.selected_file:
                    QMessageBox.warning(
                        self,
                        "File Required",
                        "Please select a .bag file before selecting ROI."
                    )
                    return

                self.status_label.setText("Status: Reading first frame from .bag for ROI selection...")
                QApplication.processEvents()

                first_frame = get_first_frame_from_bag(self.selected_file)

        if first_frame is None:
            QMessageBox.warning(
                self,
                "ROI Selection Failed",
                "Could not read a frame for ROI selection."
            )
            self.status_label.setText("Status: ROI selection failed.")
            return

        roi = select_roi_from_frame(first_frame, "Select Barbell Disk ROI")

        if roi is None:
            QMessageBox.information(
                self,
                "No ROI Selected",
                "No ROI was selected."
            )
            self.status_label.setText("Status: No ROI selected.")
            return

        self.barbell_roi = roi
        self.last_roi_key = self.current_roi_key()

        if self.video_thread is not None and self.video_thread.isRunning():
            self.video_thread.set_manual_barbell_roi(roi)

        self.status_label.setText(f"Status: Manual barbell ROI selected: {roi}")

    # ==========================================================
    # PREVIEW
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

        if source_type == "realsense_bag" and not self.selected_file:
            QMessageBox.warning(
                self,
                "File Required",
                "Please select a RealSense .bag file first."
            )
            return

        if self.is_side_view():
            barbell_roi_for_thread = self.barbell_roi

            if self.barbell_roi is None:
                self.status_label.setText(
                    "Status: No manual ROI selected. Automatic barbell disk detection will be used."
                )
            else:
                self.status_label.setText(
                    "Status: Manual ROI selected. It will be used for barbell tracking."
                )

        else:
            barbell_roi_for_thread = None
            self.status_label.setText(
                "Status: Front View selected. Pose-based phase detection will be used."
            )

        self.set_status(
            f"Starting preview for {self.get_exercise()} - {self.get_camera_view()}..."
        )
        QApplication.processEvents()

        self.video_thread = VideoThread(
            source_type=source_type,
            file_path=self.selected_file,
            sport="Weightlifting",
            exercise=self.get_exercise(),
            camera_view=self.get_camera_view(),
            barbell_roi=barbell_roi_for_thread
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
                self.status_label.setText("Status: Previous preview is still closing. Please wait.")
                return False

            self.video_thread = None

        self.video_label.clear()
        self.video_label.setText("Video preview will appear here.")

        if reset_metrics:
            self.reset_metrics()

        self.status_label.setText("Status: Preview stopped.")

        return True

    # ==========================================================
    # FRAME + METRICS
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

        if "Velocity" in name:
            try:
                return f"{float(value):.1f} px/s"
            except Exception:
                return "N/A"

        if "(px)" in name:
            try:
                return f"{float(value):.1f} px"
            except Exception:
                return "N/A"

        try:
            return f"{float(value):.1f}°"
        except Exception:
            return str(value)

    # ==========================================================
    # RECORDING
    # ==========================================================
    def start_analysis_recording(self):
        source_type = self.get_source_type()

        if source_type == "realsense_bag" and not self.selected_file:
            QMessageBox.warning(
                self,
                "File Required",
                "Please select a RealSense .bag file before starting analysis."
            )
            return

        if self.video_thread is None:
            self.start_preview()

        if self.video_thread is None:
            return

        exercise = self.get_exercise()
        camera_view = self.get_camera_view()
        input_mode = self.get_input_mode()

        self.set_status("Preparing analysis session...")
        QApplication.processEvents()

        self.current_session_path = create_session_folder(
            sport="Weightlifting",
            exercise=exercise,
            camera_view=camera_view,
            input_mode=input_mode,
            source_file=self.selected_file
        )

        self.recorder = AnalysisRecorder(
            session_path=self.current_session_path,
            sport="Weightlifting",
            exercise=exercise,
            camera_view=camera_view,
            input_mode=input_mode,
            source_file=self.selected_file
        )

        self.recorder.start()
        self.is_recording = True

        self.btn_start_recording.setEnabled(False)
        self.btn_stop_recording.setEnabled(True)

        self.set_status("Recording started. Keep the movement visible until you stop and save.")

    # ==========================================================
    # ENHANCED SESSION INFO HELPERS
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

    def existing_file_path(self, file_path):
        file_path = Path(file_path)

        if file_path.exists():
            return str(file_path)

        return ""

    def build_enhanced_session_info(self, output_info):
        """
        Build richer session_info for the analysis dashboard.

        This keeps old keys unchanged:
            sport
            exercise
            camera_view
            input_mode
            source_file
            results_folder
            record_count

        Adds new useful keys from:
            CSV/lift_summary.csv
            CSV/phase_biomechanics_summary.csv
            Plots/*.png
        """

        session_path = Path(self.current_session_path)
        csv_folder = session_path / "CSV"
        plots_folder = session_path / "Plots"
        reports_folder = session_path / "Reports"

        lift_summary_path = csv_folder / "lift_summary.csv"
        phase_biomechanics_path = csv_folder / "phase_biomechanics_summary.csv"

        lift_summary = self.read_first_row_csv(lift_summary_path)

        csv_files = {
            "joint_angles_2d": self.existing_file_path(csv_folder / "joint_angles_2d.csv"),
            "depth_data": self.existing_file_path(csv_folder / "depth_data.csv"),
            "barbell_trajectory": self.existing_file_path(csv_folder / "barbell_trajectory.csv"),
            "phase_summary": self.existing_file_path(csv_folder / "phase_summary.csv"),
            "analysis_summary": self.existing_file_path(csv_folder / "analysis_summary.csv"),
            "lift_summary": self.existing_file_path(lift_summary_path),
            "phase_biomechanics_summary": self.existing_file_path(phase_biomechanics_path)
        }

        plot_files = {
            "hip_knee_angles": self.existing_file_path(plots_folder / "hip_knee_angles_phase_highlighted.png"),
            "upper_limb_angles": self.existing_file_path(plots_folder / "upper_limb_angles_phase_highlighted.png"),
            "trunk_lean": self.existing_file_path(plots_folder / "trunk_lean_phase_highlighted.png"),
            "barbell_velocity": self.existing_file_path(plots_folder / "barbell_velocity_phase_highlighted.png"),
            "barbell_trajectory_annotated": self.existing_file_path(plots_folder / "barbell_trajectory_annotated.png"),
            "barbell_trajectory_powerpoint": self.existing_file_path(plots_folder / "barbell_trajectory_powerpoint_style.png"),
            "barbell_trajectory_phase_highlighted": self.existing_file_path(plots_folder / "barbell_trajectory_phase_highlighted.png")
        }

        session_info = {
            "sport": "Weightlifting",
            "exercise": self.get_exercise(),
            "camera_view": self.get_camera_view(),
            "input_mode": self.get_input_mode(),
            "source_file": self.selected_file,
            "results_folder": str(session_path),
            "record_count": output_info.get("record_count", 0),

            "session_path": str(session_path),
            "csv_folder": str(csv_folder),
            "plots_folder": str(plots_folder),
            "reports_folder": str(reports_folder),

            "csv_file": output_info.get("csv_file", ""),
            "csv_files": csv_files,
            "plot_files": plot_files,
            "lift_summary": lift_summary,

            "detected_phases": lift_summary.get("detected_phases", ""),
            "detected_phase_count": lift_summary.get("detected_phase_count", ""),
            "total_duration_s": lift_summary.get("total_duration_s", ""),
            "barbell_detected_samples": lift_summary.get("barbell_detected_samples", ""),

            "max_barbell_height_px": lift_summary.get("max_barbell_height_px", ""),
            "max_barbell_height_m": lift_summary.get("max_barbell_height_m", ""),

            "max_vertical_velocity_px_s": lift_summary.get("max_vertical_velocity_px_s", ""),
            "max_vertical_velocity_m_s": lift_summary.get("max_vertical_velocity_m_s", ""),

            "max_horizontal_velocity_px_s": lift_summary.get("max_horizontal_velocity_px_s", ""),
            "max_horizontal_velocity_m_s": lift_summary.get("max_horizontal_velocity_m_s", "")
        }

        return session_info

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

        self.set_status("Saving analysis outputs. Please wait...")
        QApplication.processEvents()

        output_info = self.recorder.save_outputs()

        self.btn_start_recording.setEnabled(True)
        self.btn_stop_recording.setEnabled(False)

        self._stop_preview_internal(reset_metrics=False)

        session_info = self.build_enhanced_session_info(output_info)

        self.on_start_analysis(session_info)

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

        if not self.confirm_stop_preview_before_leaving():
            return

        self._stop_preview_internal(reset_metrics=True)
        self.on_back()

    def closeEvent(self, event):
        self._stop_preview_internal(reset_metrics=True)
        event.accept()

    # ==========================================================
    # STYLE
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
                background-color: transparent;
                font-size: 14px;
                padding: 4px;
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
                background-color: #16232E;
                border: 1px solid #2E5E78;
                border-radius: 5px;
                padding: 5px;
            }
        """)