from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QMessageBox,
    QSizePolicy,
    QScrollArea
)

from modules.live_tracking_thread import LiveTrackingThread


class ClickableVideoLabel(QLabel):
    clicked = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(500, 370)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self._image_width = 0
        self._image_height = 0

    def set_source_image_size(self, width, height):
        self._image_width = int(width)
        self._image_height = int(height)

    def mousePressEvent(self, event):
        if (
            self._image_width <= 0
            or self._image_height <= 0
            or self.pixmap() is None
        ):
            return

        label_width = self.width()
        label_height = self.height()

        scale = min(
            label_width / self._image_width,
            label_height / self._image_height
        )

        display_width = self._image_width * scale
        display_height = self._image_height * scale

        offset_x = (label_width - display_width) / 2.0
        offset_y = (label_height - display_height) / 2.0

        mouse_x = event.position().x()
        mouse_y = event.position().y()

        if not (
            offset_x <= mouse_x <= offset_x + display_width
            and offset_y <= mouse_y <= offset_y + display_height
        ):
            return

        normalized_x = (mouse_x - offset_x) / display_width
        normalized_y = (mouse_y - offset_y) / display_height

        self.clicked.emit(
            float(normalized_x),
            float(normalized_y)
        )


class LiveTrackingPage(QWidget):
    """
    Exhibition live tracking page.

    Left:
        RGB frame with pose landmarks and selected angles.

    Right:
        RealSense SDK-style aligned depth heat map.

    Bottom:
        Manual landmark selection and live angle values.
    """

    PRESET_ANGLES = {
        "Left Knee": (23, 25, 27),
        "Right Knee": (24, 26, 28),
        "Left Hip": (11, 23, 25),
        "Right Hip": (12, 24, 26),
        "Left Ankle": (25, 27, 31),
        "Right Ankle": (26, 28, 32),
        "Left Shoulder": (23, 11, 13),
        "Right Shoulder": (24, 12, 14),
        "Left Elbow": (11, 13, 15),
        "Right Elbow": (12, 14, 16),
    }

    def __init__(self, on_back):
        super().__init__()

        self.on_back = on_back

        self.tracking_thread = None

        self.latest_rgb_image = None
        self.latest_depth_image = None
        self.latest_landmarks = []

        self.pending_landmarks = []
        self.angle_definitions = []

        self.selection_mode = False

        self.build_ui()
        self.apply_styles()

    # ==========================================================
    # UI
    # ==========================================================
    def build_ui(self):
        # The Live Tracking page uses its own scroll area because the two
        # large camera panels and the control groups may be taller than
        # smaller laptop/exhibition displays.
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.page_scroll = QScrollArea()
        self.page_scroll.setWidgetResizable(True)
        self.page_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.page_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.page_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.scroll_content = QWidget()
        self.scroll_content.setMinimumSize(1080, 800)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(14, 10, 14, 10)
        main_layout.setSpacing(8)

        title = QLabel("LIVE POSE TRACKING")
        title.setObjectName("PageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(
            "Intel RealSense RGB + aligned depth heat map with manual landmark angle tracking"
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # ======================================================
        # CAMERA PANELS
        # ======================================================
        camera_layout = QHBoxLayout()
        camera_layout.setSpacing(12)

        rgb_group = QGroupBox("RGB Pose Tracking")
        rgb_layout = QVBoxLayout()

        self.rgb_label = ClickableVideoLabel()
        self.rgb_label.setObjectName("VideoLabel")
        self.rgb_label.setText(
            "Start the RealSense camera to view RGB pose tracking."
        )
        self.rgb_label.setWordWrap(True)
        self.rgb_label.clicked.connect(self.handle_rgb_click)

        rgb_layout.addWidget(self.rgb_label)
        rgb_group.setLayout(rgb_layout)

        depth_group = QGroupBox("Aligned Depth Heat Map")
        depth_layout = QVBoxLayout()

        self.depth_label = QLabel()
        self.depth_label.setObjectName("VideoLabel")
        self.depth_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.depth_label.setMinimumSize(500, 370)
        self.depth_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.depth_label.setText(
            "The RealSense depth heat map will appear here."
        )
        self.depth_label.setWordWrap(True)

        depth_layout.addWidget(self.depth_label)
        depth_group.setLayout(depth_layout)

        camera_layout.addWidget(rgb_group, 1)
        camera_layout.addWidget(depth_group, 1)
        camera_layout.setStretch(0, 1)
        camera_layout.setStretch(1, 1)

        # Camera area is intentionally the main visual focus.
        main_layout.addLayout(camera_layout, 10)

        # ======================================================
        # LOWER CONTROL AREA
        # ======================================================
        lower_layout = QHBoxLayout()
        lower_layout.setSpacing(12)

        # Camera/status panel
        camera_controls_group = QGroupBox("Camera and Tracking Status")
        camera_controls_group.setMaximumHeight(190)
        camera_controls_layout = QVBoxLayout()
        camera_controls_layout.setContentsMargins(8, 7, 8, 7)
        camera_controls_layout.setSpacing(4)

        self.status_label = QLabel("Camera: Stopped")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)

        self.pose_status_label = QLabel("Pose: Not detected")
        self.pose_status_label.setWordWrap(True)

        self.depth_status_label = QLabel("Person depth: N/A")
        self.depth_status_label.setWordWrap(True)

        camera_button_layout = QHBoxLayout()

        self.start_button = QPushButton("Start Camera")
        self.stop_button = QPushButton("Stop Camera")
        self.stop_button.setEnabled(False)

        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)

        camera_button_layout.addWidget(self.start_button)
        camera_button_layout.addWidget(self.stop_button)

        camera_controls_layout.addWidget(self.status_label)
        camera_controls_layout.addWidget(self.pose_status_label)
        camera_controls_layout.addWidget(self.depth_status_label)
        camera_controls_layout.addLayout(camera_button_layout)

        camera_controls_group.setLayout(camera_controls_layout)

        # Manual selection panel
        selection_group = QGroupBox("Landmark and Angle Selection")
        selection_group.setMaximumHeight(190)
        selection_layout = QVBoxLayout()
        selection_layout.setContentsMargins(8, 7, 8, 7)
        selection_layout.setSpacing(4)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(self.PRESET_ANGLES.keys())

        self.add_preset_button = QPushButton("Add Preset Angle")
        self.add_preset_button.clicked.connect(self.add_preset_angle)

        self.selection_mode_button = QPushButton(
            "Enable Manual Landmark Selection"
        )
        self.selection_mode_button.setCheckable(True)
        self.selection_mode_button.toggled.connect(
            self.set_selection_mode
        )

        self.selection_instruction = QLabel(
            "Select three RGB landmarks; the second point is the angle vertex."
        )
        self.selection_instruction.setWordWrap(True)

        self.pending_label = QLabel("Selected landmarks: None")
        self.pending_label.setWordWrap(True)

        selection_button_layout = QHBoxLayout()

        self.undo_selection_button = QPushButton("Undo")
        self.clear_selection_button = QPushButton("Clear Selection")
        self.add_custom_button = QPushButton("Add Custom Angle")

        self.undo_selection_button.clicked.connect(
            self.undo_pending_landmark
        )
        self.clear_selection_button.clicked.connect(
            self.clear_pending_selection
        )
        self.add_custom_button.clicked.connect(
            self.add_custom_angle
        )

        selection_button_layout.addWidget(
            self.undo_selection_button
        )
        selection_button_layout.addWidget(
            self.clear_selection_button
        )
        selection_button_layout.addWidget(
            self.add_custom_button
        )

        selection_layout.addWidget(self.preset_combo)
        selection_layout.addWidget(self.add_preset_button)
        selection_layout.addWidget(self.selection_mode_button)
        selection_layout.addWidget(self.selection_instruction)
        selection_layout.addWidget(self.pending_label)
        selection_layout.addLayout(selection_button_layout)

        selection_group.setLayout(selection_layout)

        # Angle list panel
        angle_group = QGroupBox("Tracked Angles")
        angle_group.setMaximumHeight(190)
        angle_layout = QVBoxLayout()
        angle_layout.setContentsMargins(8, 7, 8, 7)
        angle_layout.setSpacing(4)

        self.angle_list = QListWidget()
        self.angle_list.setMinimumHeight(72)
        self.angle_list.setMaximumHeight(96)

        angle_button_layout = QHBoxLayout()

        self.remove_angle_button = QPushButton("Remove Selected")
        self.clear_angles_button = QPushButton("Clear All Angles")

        self.remove_angle_button.clicked.connect(
            self.remove_selected_angle
        )
        self.clear_angles_button.clicked.connect(
            self.clear_all_angles
        )

        angle_button_layout.addWidget(self.remove_angle_button)
        angle_button_layout.addWidget(self.clear_angles_button)

        angle_layout.addWidget(self.angle_list)
        angle_layout.addLayout(angle_button_layout)

        angle_group.setLayout(angle_layout)

        lower_layout.addWidget(camera_controls_group, 1)
        lower_layout.addWidget(selection_group, 2)
        lower_layout.addWidget(angle_group, 2)

        main_layout.addLayout(lower_layout, 2)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        back_button = QPushButton("Back to Home")
        back_button.setObjectName("BackButton")
        back_button.clicked.connect(self.go_back)

        bottom_layout.addWidget(back_button)

        main_layout.addLayout(bottom_layout)

        self.scroll_content.setLayout(main_layout)
        self.page_scroll.setWidget(self.scroll_content)

        root_layout.addWidget(self.page_scroll)
        self.setLayout(root_layout)

    # ==========================================================
    # CAMERA
    # ==========================================================
    def start_camera(self):
        if (
            self.tracking_thread is not None
            and self.tracking_thread.isRunning()
        ):
            return

        self.tracking_thread = LiveTrackingThread(self)

        self.tracking_thread.frame_ready.connect(
            self.update_live_frames
        )

        self.tracking_thread.status_changed.connect(
            self.update_thread_status
        )

        self.tracking_thread.error_occurred.connect(
            self.handle_tracking_error
        )

        self.tracking_thread.finished.connect(
            self.handle_thread_finished
        )

        self.tracking_thread.set_angle_definitions(
            self.angle_definitions
        )

        self.tracking_thread.set_pending_landmarks(
            self.pending_landmarks
        )

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.status_label.setText("Camera: Connecting...")
        self.tracking_thread.start()

    def stop_camera(self):
        if self.tracking_thread is None:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            return

        if self.tracking_thread.isRunning():
            self.tracking_thread.request_stop()
            self.tracking_thread.wait(3500)

        self.tracking_thread.deleteLater()
        self.tracking_thread = None

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self.status_label.setText("Camera: Stopped")
        self.pose_status_label.setText("Pose: Not detected")
        self.depth_status_label.setText("Person depth: N/A")

    def handle_thread_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_thread_status(self, message):
        self.status_label.setText(f"Camera: {message}")

    def handle_tracking_error(self, message):
        self.status_label.setText(message)

        QMessageBox.critical(
            self,
            "Live Tracking Error",
            message
        )

    # ==========================================================
    # FRAME DISPLAY
    # ==========================================================
    def update_live_frames(
        self,
        rgb_image,
        depth_image,
        metadata
    ):
        self.latest_rgb_image = rgb_image
        self.latest_depth_image = depth_image

        self.latest_landmarks = metadata.get(
            "landmarks",
            []
        )

        frame_width = metadata.get(
            "frame_width",
            rgb_image.width()
        )

        frame_height = metadata.get(
            "frame_height",
            rgb_image.height()
        )

        self.rgb_label.set_source_image_size(
            frame_width,
            frame_height
        )

        self.refresh_video_pixmaps()

        pose_detected = metadata.get(
            "pose_detected",
            False
        )

        person_centered = metadata.get(
            "person_centered",
            False
        )

        if not pose_detected:
            self.pose_status_label.setText(
                "Pose: Not detected"
            )
        elif person_centered:
            self.pose_status_label.setText(
                "Pose: Detected — person centred"
            )
        else:
            self.pose_status_label.setText(
                "Pose: Detected — move person towards centre"
            )

        center_depth_m = metadata.get(
            "center_depth_m"
        )

        if center_depth_m is None:
            self.depth_status_label.setText(
                "Person depth: N/A"
            )
        else:
            self.depth_status_label.setText(
                f"Person depth: {center_depth_m:.2f} m"
            )

        self.refresh_angle_list(
            metadata.get("angle_values", {})
        )

    def refresh_video_pixmaps(self):
        if (
            self.latest_rgb_image is not None
            and not self.latest_rgb_image.isNull()
        ):
            rgb_pixmap = QPixmap.fromImage(
                self.latest_rgb_image
            )

            self.rgb_label.setPixmap(
                rgb_pixmap.scaled(
                    self.rgb_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

        if (
            self.latest_depth_image is not None
            and not self.latest_depth_image.isNull()
        ):
            depth_pixmap = QPixmap.fromImage(
                self.latest_depth_image
            )

            self.depth_label.setPixmap(
                depth_pixmap.scaled(
                    self.depth_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.refresh_video_pixmaps()

    # ==========================================================
    # MANUAL LANDMARK SELECTION
    # ==========================================================
    def set_selection_mode(self, enabled):
        self.selection_mode = bool(enabled)

        if enabled:
            self.selection_mode_button.setText(
                "Manual Selection Active — Click RGB Landmarks"
            )
        else:
            self.selection_mode_button.setText(
                "Enable Manual Landmark Selection"
            )

    def handle_rgb_click(self, normalized_x, normalized_y):
        if not self.selection_mode:
            return

        if not self.latest_landmarks:
            self.status_label.setText(
                "Camera: Pose landmarks are not available."
            )
            return

        visible_landmarks = [
            landmark
            for landmark in self.latest_landmarks
            if landmark.get("visibility", 0.0) >= 0.45
        ]

        if not visible_landmarks:
            return

        nearest_landmark = min(
            visible_landmarks,
            key=lambda landmark: (
                (landmark["x"] - normalized_x) ** 2
                + (landmark["y"] - normalized_y) ** 2
            )
        )

        distance = (
            (nearest_landmark["x"] - normalized_x) ** 2
            + (nearest_landmark["y"] - normalized_y) ** 2
        ) ** 0.5

        if distance > 0.085:
            self.status_label.setText(
                "Camera: Click closer to a visible pose landmark."
            )
            return

        landmark_index = int(
            nearest_landmark["index"]
        )

        if landmark_index in self.pending_landmarks:
            self.status_label.setText(
                "Camera: That landmark is already selected."
            )
            return

        if len(self.pending_landmarks) >= 3:
            self.status_label.setText(
                "Camera: Three landmarks already selected. "
                "Add or clear the custom angle."
            )
            return

        self.pending_landmarks.append(
            landmark_index
        )

        self.update_pending_display()

        if self.tracking_thread is not None:
            self.tracking_thread.set_pending_landmarks(
                self.pending_landmarks
            )

    def update_pending_display(self):
        if not self.pending_landmarks:
            self.pending_label.setText(
                "Selected landmarks: None"
            )
            return

        names = []

        landmark_lookup = {
            int(item["index"]): item["name"]
            for item in self.latest_landmarks
        }

        for position, landmark_index in enumerate(
            self.pending_landmarks,
            start=1
        ):
            landmark_name = landmark_lookup.get(
                landmark_index,
                f"Landmark {landmark_index}"
            )

            vertex_text = (
                " (vertex)" if position == 2 else ""
            )

            names.append(
                f"{position}. {landmark_name}{vertex_text}"
            )

        self.pending_label.setText(
            "Selected landmarks:\n" + "\n".join(names)
        )

    def undo_pending_landmark(self):
        if self.pending_landmarks:
            self.pending_landmarks.pop()

        self.update_pending_display()
        self.push_pending_selection_to_thread()

    def clear_pending_selection(self):
        self.pending_landmarks = []
        self.update_pending_display()
        self.push_pending_selection_to_thread()

    def push_pending_selection_to_thread(self):
        if self.tracking_thread is not None:
            self.tracking_thread.set_pending_landmarks(
                self.pending_landmarks
            )

    # ==========================================================
    # ANGLES
    # ==========================================================
    def add_preset_angle(self):
        name = self.preset_combo.currentText()
        points = self.PRESET_ANGLES.get(name)

        if points is None:
            return

        self.add_angle_definition(
            name=name,
            points=points
        )

    def add_custom_angle(self):
        if len(self.pending_landmarks) != 3:
            QMessageBox.information(
                self,
                "Select Three Landmarks",
                "Select exactly three landmarks on the RGB frame. "
                "The second landmark is used as the angle vertex."
            )
            return

        landmark_lookup = {
            int(item["index"]): item["name"]
            for item in self.latest_landmarks
        }

        point_names = [
            landmark_lookup.get(
                index,
                f"Landmark {index}"
            )
            for index in self.pending_landmarks
        ]

        custom_name = (
            f"{point_names[0]} / "
            f"{point_names[1]} / "
            f"{point_names[2]}"
        )

        self.add_angle_definition(
            name=custom_name,
            points=tuple(self.pending_landmarks)
        )

        self.clear_pending_selection()

    def add_angle_definition(self, name, points):
        if len(points) != 3:
            return

        for definition in self.angle_definitions:
            if tuple(definition["points"]) == tuple(points):
                self.status_label.setText(
                    f"Camera: {name} is already being tracked."
                )
                return

        if len(self.angle_definitions) >= 8:
            QMessageBox.information(
                self,
                "Angle Limit",
                "A maximum of eight angles can be displayed at once."
            )
            return

        self.angle_definitions.append({
            "name": str(name),
            "points": tuple(points)
        })

        self.push_angles_to_thread()
        self.refresh_angle_list({})

    def remove_selected_angle(self):
        selected_row = self.angle_list.currentRow()

        if not 0 <= selected_row < len(
            self.angle_definitions
        ):
            return

        self.angle_definitions.pop(selected_row)

        self.push_angles_to_thread()
        self.refresh_angle_list({})

    def clear_all_angles(self):
        self.angle_definitions = []

        self.push_angles_to_thread()
        self.refresh_angle_list({})

    def push_angles_to_thread(self):
        if self.tracking_thread is not None:
            self.tracking_thread.set_angle_definitions(
                self.angle_definitions
            )

    def refresh_angle_list(self, angle_values):
        current_row = self.angle_list.currentRow()

        self.angle_list.clear()

        for definition in self.angle_definitions:
            name = definition["name"]
            value = angle_values.get(name)

            if value is None:
                display_text = f"{name}: N/A"
            else:
                display_text = f"{name}: {value:.1f}°"

            item = QListWidgetItem(display_text)
            item.setToolTip(
                f"Landmarks: {definition['points']}"
            )

            self.angle_list.addItem(item)

        if 0 <= current_row < self.angle_list.count():
            self.angle_list.setCurrentRow(current_row)

    # ==========================================================
    # PAGE NAVIGATION
    # ==========================================================
    def go_back(self):
        self.stop_camera()
        self.on_back()

    def shutdown(self):
        self.stop_camera()

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

            QLabel#PageTitle {
                color: #00D4FF;
                font-size: 25px;
                font-weight: bold;
                letter-spacing: 2px;
                background-color: #0B141D;
                padding: 5px;
            }

            QLabel#PageSubtitle {
                color: #D8E4EE;
                font-size: 13px;
                background-color: #111D28;
                padding: 4px;
            }

            QLabel#VideoLabel {
                background-color: #05090D;
                color: #AEBECB;
                border: 1px solid #0078D7;
                border-radius: 8px;
                padding: 6px;
            }

            QLabel#StatusLabel {
                color: #00D4FF;
                font-weight: bold;
            }

            QGroupBox {
                border: 2px solid #0078D7;
                border-radius: 9px;
                margin-top: 8px;
                padding: 7px;
                font-size: 13px;
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 7px;
                color: #00D4FF;
            }

            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 7px;
                font-size: 12px;
                font-weight: bold;
                min-height: 28px;
                padding: 3px 8px;
            }

            QPushButton:hover {
                background-color: #0099FF;
            }

            QPushButton:pressed {
                background-color: #005A9E;
            }

            QPushButton:disabled {
                background-color: #43515E;
                color: #AAB3BB;
            }

            QPushButton:checked {
                background-color: #00A86B;
            }

            QPushButton#BackButton {
                min-width: 150px;
            }

            QComboBox,
            QListWidget {
                background-color: #1E2A35;
                color: white;
                border: 1px solid #0078D7;
                border-radius: 6px;
                font-size: 12px;
                padding: 4px;
            }

            QScrollArea {
                border: none;
                background-color: #101820;
            }

            QScrollBar:vertical {
                background: #16222E;
                width: 12px;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background: #0078D7;
                min-height: 35px;
                border-radius: 5px;
            }

            QScrollBar:horizontal {
                background: #16222E;
                height: 12px;
                margin: 0;
            }

            QScrollBar::handle:horizontal {
                background: #0078D7;
                min-width: 35px;
                border-radius: 5px;
            }

            QListWidget::item {
                padding: 4px;
            }

            QListWidget::item:selected {
                background-color: #0078D7;
            }
        """)