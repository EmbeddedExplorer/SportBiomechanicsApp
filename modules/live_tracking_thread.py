import threading
from math import acos, degrees

import cv2
import numpy as np
import pyrealsense2 as rs
import mediapipe as mp

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage


class LiveTrackingThread(QThread):
    """
    RealSense live RGB + aligned depth tracking thread.

    Features:
    - Captures RGB and depth streams from Intel RealSense.
    - Aligns depth to the RGB frame.
    - Produces an SDK-style colorized depth heat map.
    - Detects one MediaPipe pose.
    - Checks whether the detected person is near the image centre.
    - Draws manually selected/custom joint angles.
    """

    frame_ready = pyqtSignal(object, object, object)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._running = False
        self._state_lock = threading.Lock()

        self._angle_definitions = []
        self._pending_landmarks = []

        self._pipeline = None

    # ==========================================================
    # PUBLIC CONTROL METHODS
    # ==========================================================
    def set_angle_definitions(self, angle_definitions):
        with self._state_lock:
            self._angle_definitions = [
                {
                    "name": str(item.get("name", "Custom Angle")),
                    "points": tuple(item.get("points", ()))
                }
                for item in angle_definitions
            ]

    def set_pending_landmarks(self, landmark_indices):
        with self._state_lock:
            self._pending_landmarks = list(landmark_indices)

    def request_stop(self):
        self._running = False
        self.requestInterruption()

    # ==========================================================
    # HELPERS
    # ==========================================================
    @staticmethod
    def calculate_angle(point_a, point_b, point_c):
        """
        Calculate the 2D angle ABC in degrees.
        The middle point B is the angle vertex.
        """

        vector_ba = np.array(point_a, dtype=float) - np.array(point_b, dtype=float)
        vector_bc = np.array(point_c, dtype=float) - np.array(point_b, dtype=float)

        norm_ba = np.linalg.norm(vector_ba)
        norm_bc = np.linalg.norm(vector_bc)

        if norm_ba <= 1e-9 or norm_bc <= 1e-9:
            return None

        cosine_value = float(
            np.dot(vector_ba, vector_bc) / (norm_ba * norm_bc)
        )

        cosine_value = max(-1.0, min(1.0, cosine_value))

        return degrees(acos(cosine_value))

    @staticmethod
    def bgr_to_qimage(frame_bgr):
        if frame_bgr is None or frame_bgr.size == 0:
            return QImage()

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        height, width, channels = frame_rgb.shape
        bytes_per_line = channels * width

        return QImage(
            frame_rgb.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888
        ).copy()

    @staticmethod
    def get_landmark_pixel(landmarks, index, frame_width, frame_height):
        landmark = landmarks[index]

        x = int(np.clip(landmark.x, 0.0, 1.0) * (frame_width - 1))
        y = int(np.clip(landmark.y, 0.0, 1.0) * (frame_height - 1))

        return x, y

    @staticmethod
    def get_person_centre(landmarks, frame_width, frame_height):
        """
        Prefer the midpoint between the hips.
        Fall back to the midpoint between the shoulders.
        """

        candidate_pairs = [
            (23, 24),  # hips
            (11, 12),  # shoulders
        ]

        for left_index, right_index in candidate_pairs:
            left = landmarks[left_index]
            right = landmarks[right_index]

            if left.visibility >= 0.45 and right.visibility >= 0.45:
                x = int(((left.x + right.x) / 2.0) * frame_width)
                y = int(((left.y + right.y) / 2.0) * frame_height)

                x = int(np.clip(x, 0, frame_width - 1))
                y = int(np.clip(y, 0, frame_height - 1))

                return x, y

        return frame_width // 2, frame_height // 2

    # ==========================================================
    # THREAD
    # ==========================================================
    def run(self):
        self._running = True

        pipeline = None
        pose = None

        try:
            pipeline = rs.pipeline()
            config = rs.config()

            config.enable_stream(
                rs.stream.color,
                640,
                480,
                rs.format.bgr8,
                30
            )

            config.enable_stream(
                rs.stream.depth,
                640,
                480,
                rs.format.z16,
                30
            )

            self.status_changed.emit("Connecting to Intel RealSense camera...")

            pipeline.start(config)
            self._pipeline = pipeline

            align = rs.align(rs.stream.color)
            colorizer = rs.colorizer()

            # Use a true colour depth map similar to Intel RealSense Viewer.
            # RealSense colour scheme 0 is Jet. Scheme 2 is White-to-Black,
            # which produces the grayscale display seen previously.
            try:
                colorizer.set_option(rs.option.color_scheme, 0)
            except Exception:
                pass

            try:
                colorizer.set_option(
                    rs.option.histogram_equalization_enabled,
                    1
                )
            except Exception:
                pass

            mp_pose = mp.solutions.pose
            mp_drawing = mp.solutions.drawing_utils
            mp_styles = mp.solutions.drawing_styles

            landmark_names = {
                landmark.value: landmark.name.replace("_", " ").title()
                for landmark in mp_pose.PoseLandmark
            }

            pose = mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                enable_segmentation=False,
                min_detection_confidence=0.55,
                min_tracking_confidence=0.55
            )

            self.status_changed.emit("RealSense connected. Live tracking started.")

            while self._running and not self.isInterruptionRequested():
                try:
                    frames = pipeline.wait_for_frames(timeout_ms=1500)
                except Exception:
                    if self._running:
                        self.status_changed.emit(
                            "Waiting for RealSense frames..."
                        )
                    continue

                aligned_frames = align.process(frames)

                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()

                if not color_frame or not depth_frame:
                    continue

                color_bgr = np.asanyarray(color_frame.get_data()).copy()

                depth_color_frame = colorizer.colorize(depth_frame)
                depth_colour = np.asanyarray(
                    depth_color_frame.get_data()
                ).copy()

                # The RealSense colorizer normally returns RGB8. Convert it
                # for OpenCV display. A fallback colour map is included to
                # guarantee a colour heat map on systems that expose a
                # single-channel colorized frame.
                if depth_colour.ndim == 2:
                    depth_bgr = cv2.applyColorMap(
                        depth_colour,
                        cv2.COLORMAP_JET
                    )
                elif (
                    depth_colour.ndim == 3
                    and depth_colour.shape[2] == 1
                ):
                    depth_bgr = cv2.applyColorMap(
                        depth_colour[:, :, 0],
                        cv2.COLORMAP_JET
                    )
                else:
                    depth_bgr = cv2.cvtColor(
                        depth_colour,
                        cv2.COLOR_RGB2BGR
                    )

                frame_height, frame_width = color_bgr.shape[:2]

                # Central guide region for exhibition positioning.
                guide_left = int(frame_width * 0.35)
                guide_right = int(frame_width * 0.65)

                cv2.rectangle(
                    color_bgr,
                    (guide_left, int(frame_height * 0.08)),
                    (guide_right, int(frame_height * 0.92)),
                    (80, 180, 255),
                    1
                )

                color_rgb = cv2.cvtColor(color_bgr, cv2.COLOR_BGR2RGB)
                color_rgb.flags.writeable = False

                pose_result = pose.process(color_rgb)

                color_rgb.flags.writeable = True

                pose_detected = pose_result.pose_landmarks is not None
                person_centered = False
                centre_depth_m = None
                landmark_metadata = []
                angle_values = {}

                if pose_detected:
                    landmarks = pose_result.pose_landmarks.landmark

                    mp_drawing.draw_landmarks(
                        color_bgr,
                        pose_result.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=mp_styles.get_default_pose_landmarks_style()
                    )

                    person_centre_x, person_centre_y = self.get_person_centre(
                        landmarks,
                        frame_width,
                        frame_height
                    )

                    centre_ratio_x = person_centre_x / max(frame_width, 1)

                    person_centered = 0.35 <= centre_ratio_x <= 0.65

                    try:
                        depth_value = depth_frame.get_distance(
                            person_centre_x,
                            person_centre_y
                        )

                        if depth_value > 0:
                            centre_depth_m = float(depth_value)
                    except Exception:
                        centre_depth_m = None

                    centre_colour = (
                        (0, 255, 0) if person_centered else (0, 165, 255)
                    )

                    cv2.circle(
                        color_bgr,
                        (person_centre_x, person_centre_y),
                        7,
                        centre_colour,
                        -1
                    )

                    cv2.circle(
                        depth_bgr,
                        (person_centre_x, person_centre_y),
                        7,
                        (255, 255, 255),
                        2
                    )

                    if centre_depth_m is not None:
                        cv2.putText(
                            depth_bgr,
                            f"Person Depth: {centre_depth_m:.2f} m",
                            (18, 34),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.72,
                            (255, 255, 255),
                            2,
                            cv2.LINE_AA
                        )

                    for index, landmark in enumerate(landmarks):
                        landmark_metadata.append({
                            "index": index,
                            "name": landmark_names.get(
                                index,
                                f"Landmark {index}"
                            ),
                            "x": float(landmark.x),
                            "y": float(landmark.y),
                            "visibility": float(landmark.visibility)
                        })

                    with self._state_lock:
                        angle_definitions = list(self._angle_definitions)
                        pending_landmarks = list(self._pending_landmarks)

                    # Show pending manual landmark selections.
                    pending_colours = [
                        (255, 255, 0),
                        (0, 255, 255),
                        (0, 255, 0)
                    ]

                    for pending_position, landmark_index in enumerate(
                        pending_landmarks[:3]
                    ):
                        if not 0 <= landmark_index < len(landmarks):
                            continue

                        landmark = landmarks[landmark_index]

                        if landmark.visibility < 0.35:
                            continue

                        point = self.get_landmark_pixel(
                            landmarks,
                            landmark_index,
                            frame_width,
                            frame_height
                        )

                        colour = pending_colours[pending_position]

                        cv2.circle(color_bgr, point, 10, colour, 3)

                        cv2.putText(
                            color_bgr,
                            str(pending_position + 1),
                            (point[0] + 9, point[1] - 9),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            colour,
                            2,
                            cv2.LINE_AA
                        )

                    # Draw all active angle definitions.
                    for angle_definition in angle_definitions:
                        points = tuple(angle_definition.get("points", ()))

                        if len(points) != 3:
                            continue

                        index_a, index_b, index_c = points

                        if any(
                            index < 0 or index >= len(landmarks)
                            for index in points
                        ):
                            continue

                        selected_landmarks = [
                            landmarks[index_a],
                            landmarks[index_b],
                            landmarks[index_c]
                        ]

                        if any(
                            landmark.visibility < 0.35
                            for landmark in selected_landmarks
                        ):
                            angle_values[angle_definition["name"]] = None
                            continue

                        point_a = self.get_landmark_pixel(
                            landmarks,
                            index_a,
                            frame_width,
                            frame_height
                        )

                        point_b = self.get_landmark_pixel(
                            landmarks,
                            index_b,
                            frame_width,
                            frame_height
                        )

                        point_c = self.get_landmark_pixel(
                            landmarks,
                            index_c,
                            frame_width,
                            frame_height
                        )

                        angle_value = self.calculate_angle(
                            point_a,
                            point_b,
                            point_c
                        )

                        angle_values[angle_definition["name"]] = angle_value

                        if angle_value is None:
                            continue

                        cv2.line(
                            color_bgr,
                            point_a,
                            point_b,
                            (0, 255, 255),
                            3
                        )

                        cv2.line(
                            color_bgr,
                            point_b,
                            point_c,
                            (0, 255, 255),
                            3
                        )

                        for point in [point_a, point_b, point_c]:
                            cv2.circle(
                                color_bgr,
                                point,
                                6,
                                (0, 255, 0),
                                -1
                            )

                        label_x = min(point_b[0] + 10, frame_width - 220)
                        label_y = max(point_b[1] - 10, 24)

                        cv2.putText(
                            color_bgr,
                            f"{angle_definition['name']}: {angle_value:.1f} deg",
                            (label_x, label_y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55,
                            (0, 255, 255),
                            2,
                            cv2.LINE_AA
                        )

                    centre_message = (
                        "Person Centred"
                        if person_centered
                        else "Move Person to Centre"
                    )

                    centre_message_colour = (
                        (0, 255, 0)
                        if person_centered
                        else (0, 165, 255)
                    )

                    cv2.putText(
                        color_bgr,
                        centre_message,
                        (18, 34),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.72,
                        centre_message_colour,
                        2,
                        cv2.LINE_AA
                    )

                else:
                    cv2.putText(
                        color_bgr,
                        "Pose Not Detected",
                        (18, 34),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.72,
                        (0, 0, 255),
                        2,
                        cv2.LINE_AA
                    )

                metadata = {
                    "pose_detected": pose_detected,
                    "person_centered": person_centered,
                    "center_depth_m": centre_depth_m,
                    "landmarks": landmark_metadata,
                    "angle_values": angle_values,
                    "frame_width": frame_width,
                    "frame_height": frame_height
                }

                rgb_qimage = self.bgr_to_qimage(color_bgr)
                depth_qimage = self.bgr_to_qimage(depth_bgr)

                self.frame_ready.emit(
                    rgb_qimage,
                    depth_qimage,
                    metadata
                )

        except Exception as error:
            self.error_occurred.emit(
                f"Live tracking failed: {error}"
            )

        finally:
            self._running = False

            if pose is not None:
                try:
                    pose.close()
                except Exception:
                    pass

            if pipeline is not None:
                try:
                    pipeline.stop()
                except Exception:
                    pass

            self._pipeline = None
            self.status_changed.emit("Live tracking stopped.")