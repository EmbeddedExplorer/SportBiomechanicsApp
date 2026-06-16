import cv2
import numpy as np

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

from modules.biomechanics import compute_pose_metrics
from modules.barbell_tracker import BarbellTracker
from modules.phase_detector import PhaseDetector


class VideoThread(QThread):
    frame_ready = pyqtSignal(QImage)
    status_ready = pyqtSignal(str)
    metrics_ready = pyqtSignal(dict)

    def __init__(
        self,
        source_type="video_file",
        file_path="",
        camera_index=0,
        sport="",
        exercise="",
        camera_view="",
        barbell_roi=None
    ):
        super().__init__()

        self.source_type = source_type
        self.file_path = file_path
        self.camera_index = camera_index

        self.sport = sport
        self.exercise = exercise
        self.camera_view = camera_view
        self.barbell_roi = barbell_roi

        self.current_phase = "Not Detected"
        self.running = False

        self.mp_pose = None
        self.pose = None
        self.mp_drawing = None

        self.barbell_tracker = BarbellTracker()
        self.phase_detector = PhaseDetector()

    def setup_mediapipe(self):
        try:
            import mediapipe as mp

            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils

            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )

            return True

        except Exception as e:
            self.status_ready.emit(f"MediaPipe not available: {e}")
            return False

    def close_mediapipe(self):
        try:
            if self.pose is not None:
                self.pose.close()
        except Exception:
            pass

        self.pose = None

    def run(self):
        self.running = True

        self.setup_mediapipe()

        if self.source_type in ["realsense_live", "realsense_bag"]:
            self.run_realsense()
        elif self.source_type == "video_file":
            self.run_opencv_video(self.file_path)
        else:
            self.status_ready.emit("Invalid video source.")

        self.close_mediapipe()

    def run_opencv_video(self, source):
        cap = None

        try:
            cap = cv2.VideoCapture(source)

            if not cap.isOpened():
                self.status_ready.emit("Could not open video source.")
                return

            self.status_ready.emit("Video feed started. Depth: Not available.")

            while self.running:
                ret, frame = cap.read()

                if not ret:
                    self.status_ready.emit("Video ended or frame not available.")
                    break

                frame = cv2.resize(frame, (640, 480))

                frame = self.process_pose_overlay(
                    frame=frame,
                    depth_frame=None,
                    depth_available=False,
                    depth_intrinsics=None
                )

                self.frame_ready.emit(self.convert_cv_to_qimage(frame))
                self.msleep(30)

        except Exception as e:
            self.status_ready.emit(f"Video error: {e}")

        finally:
            if cap is not None:
                try:
                    cap.release()
                except Exception:
                    pass

            self.metrics_ready.emit(self.empty_metrics())
            self.status_ready.emit("Video feed stopped.")
            self.running = False

    def run_realsense(self):
        pipeline = None
        started = False

        try:
            import pyrealsense2 as rs

            pipeline = rs.pipeline()
            config = rs.config()

            if self.source_type == "realsense_bag":
                if not self.file_path:
                    self.status_ready.emit("No .bag file selected.")
                    return

                rs.config.enable_device_from_file(
                    config,
                    self.file_path,
                    repeat_playback=False
                )

                config.enable_all_streams()

            else:
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

            profile = pipeline.start(config)
            started = True

            if self.source_type == "realsense_bag":
                try:
                    playback = profile.get_device().as_playback()
                    playback.set_real_time(False)
                except Exception:
                    pass

            align = rs.align(rs.stream.color)
            self.status_ready.emit("RealSense feed started. RGB + depth available.")

            while self.running:
                try:
                    frames = pipeline.wait_for_frames(timeout_ms=300)
                except Exception:
                    if self.running:
                        self.status_ready.emit("No more RealSense frames available.")
                    break

                try:
                    aligned_frames = align.process(frames)
                except Exception:
                    aligned_frames = frames

                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()

                if not color_frame:
                    continue

                color_image = np.asanyarray(color_frame.get_data())

                if self.source_type == "realsense_bag":
                    try:
                        color_image = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)
                    except Exception:
                        pass

                depth_intrinsics = None

                if depth_frame is not None:
                    try:
                        depth_intrinsics = (
                            depth_frame.profile
                            .as_video_stream_profile()
                            .intrinsics
                        )
                    except Exception:
                        depth_intrinsics = None

                color_image = self.process_pose_overlay(
                    frame=color_image,
                    depth_frame=depth_frame,
                    depth_available=depth_frame is not None,
                    depth_intrinsics=depth_intrinsics
                )

                self.frame_ready.emit(self.convert_cv_to_qimage(color_image))

                if depth_frame:
                    h, w, _ = color_image.shape
                    center_depth = self.get_depth_value(depth_frame, w // 2, h // 2)

                    if center_depth is not None:
                        self.status_ready.emit(
                            f"RealSense RGB-D running | Center depth: {center_depth:.2f} m"
                        )
                    else:
                        self.status_ready.emit("RealSense RGB-D running | Center depth: N/A")
                else:
                    self.status_ready.emit("RealSense color running | Depth frame not available.")

                self.msleep(30)

        except Exception as e:
            self.status_ready.emit(f"RealSense error: {e}")

        finally:
            if pipeline is not None and started:
                try:
                    pipeline.stop()
                except Exception:
                    pass

            try:
                del pipeline
            except Exception:
                pass

            self.metrics_ready.emit(self.empty_metrics())
            self.status_ready.emit("RealSense feed stopped.")
            self.running = False

    def process_pose_overlay(
        self,
        frame,
        depth_frame=None,
        depth_available=False,
        depth_intrinsics=None
    ):
        display_frame = frame.copy()
        clean_frame_for_tracking = frame.copy()

        h, w, _ = display_frame.shape

        center_x = w // 2
        center_y = h // 2

        center_depth = None
        athlete_depth = None

        if depth_available and depth_frame is not None:
            center_depth = self.get_depth_value(depth_frame, center_x, center_y)

            cv2.circle(display_frame, (center_x, center_y), 6, (255, 255, 0), -1)

            cv2.putText(
                display_frame,
                f"Center Depth: {center_depth:.2f} m" if center_depth else "Center Depth: N/A",
                (20, 115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2
            )
        else:
            cv2.putText(
                display_frame,
                "Depth: Not available",
                (20, 115),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2
            )

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if self.pose is not None:
            results = self.pose.process(rgb_frame)

            if results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    display_frame,
                    results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS
                )

                landmarks = results.pose_landmarks.landmark

                ids = [
                    self.mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                    self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
                    self.mp_pose.PoseLandmark.LEFT_HIP.value,
                    self.mp_pose.PoseLandmark.RIGHT_HIP.value
                ]

                xs = []
                ys = []

                for idx in ids:
                    lm = landmarks[idx]

                    if lm.visibility > 0.5:
                        xs.append(int(lm.x * w))
                        ys.append(int(lm.y * h))

                if xs and ys:
                    athlete_x = int(sum(xs) / len(xs))
                    athlete_y = int(sum(ys) / len(ys))

                    cv2.circle(display_frame, (athlete_x, athlete_y), 8, (0, 165, 255), -1)

                    cv2.putText(
                        display_frame,
                        "Athlete COM",
                        (athlete_x + 10, athlete_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 165, 255),
                        2
                    )

                    if depth_available and depth_frame is not None:
                        athlete_depth = self.get_depth_value(
                            depth_frame,
                            athlete_x,
                            athlete_y
                        )

                        if athlete_depth is not None:
                            cv2.putText(
                                display_frame,
                                f"Athlete Depth: {athlete_depth:.2f} m",
                                (20, 145),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.65,
                                (0, 165, 255),
                                2
                            )

                metrics = compute_pose_metrics(
                    landmarks=landmarks,
                    pose_landmark_enum=self.mp_pose.PoseLandmark,
                    image_width=w,
                    image_height=h,
                    athlete_depth=athlete_depth,
                    center_depth=center_depth
                )

                if self.sport == "Weightlifting":

                    # Side View: ROI-based barbell trajectory tracking.
                    if self.camera_view == "Side View" and self.barbell_roi is not None:
                        barbell_metrics = self.barbell_tracker.update(
                            frame=clean_frame_for_tracking,
                            depth_frame=depth_frame if depth_available else None,
                            depth_intrinsics=depth_intrinsics,
                            initial_bbox=self.barbell_roi
                        )

                        self.current_phase = self.phase_detector.update(
                            exercise=self.exercise,
                            barbell_metrics=barbell_metrics
                        )

                        metrics.update(barbell_metrics)

                        self.barbell_tracker.draw_overlay(
                            display_frame,
                            camera_view=self.camera_view
                        )

                    # Front View: no barbell trajectory tracking.
                    else:
                        barbell_metrics = self.barbell_tracker.empty_metrics()
                        metrics.update(barbell_metrics)

                        if self.camera_view == "Front View":
                            self.current_phase = "Front View Analysis"
                        else:
                            self.current_phase = "Not Detected"

                    metrics["Phase"] = self.current_phase
                    metrics["Exercise"] = self.exercise
                    metrics["Camera View"] = self.camera_view

                    self.draw_context_overlay(display_frame)

                else:
                    metrics["Phase"] = "N/A"

                self.metrics_ready.emit(metrics)

            else:
                metrics = self.empty_metrics()
                metrics["Pose"] = "Not Detected"
                metrics["Center Depth (m)"] = center_depth
                self.metrics_ready.emit(metrics)

        return display_frame

    def draw_context_overlay(self, frame):
        if self.sport != "Weightlifting":
            return

        overlay_lines = [
            f"Exercise: {self.exercise if self.exercise else 'N/A'}",
            f"View: {self.camera_view if self.camera_view else 'N/A'}",
            f"Phase: {self.current_phase}"
        ]

        y = 30

        for line in overlay_lines:
            cv2.putText(
                frame,
                line,
                (20, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2
            )
            y += 28

    def get_depth_value(self, depth_frame, x, y):
        try:
            depth_width = depth_frame.get_width()
            depth_height = depth_frame.get_height()

            x = max(0, min(int(x), depth_width - 1))
            y = max(0, min(int(y), depth_height - 1))

            depth = depth_frame.get_distance(x, y)

            if depth <= 0:
                return None

            return round(depth, 3)

        except Exception:
            return None

    def empty_metrics(self):
        return {
            "Pose": "Not Detected",
            "Phase": self.current_phase,

            "Left Hip Angle": None,
            "Right Hip Angle": None,
            "Left Knee Angle": None,
            "Right Knee Angle": None,
            "Left Ankle Angle": None,
            "Right Ankle Angle": None,
            "Left Shoulder Angle": None,
            "Right Shoulder Angle": None,
            "Left Elbow Angle": None,
            "Right Elbow Angle": None,
            "Trunk Lean Angle": None,

            "Athlete Depth (m)": None,
            "Center Depth (m)": None,

            "Barbell Detected": False,
            "Barbell X (px)": None,
            "Barbell Y (px)": None,
            "Barbell Horizontal Displacement (px)": None,
            "Barbell Vertical Displacement (px)": None,
            "Barbell Vertical Velocity (px/s)": None,
            "Barbell Horizontal Velocity (px/s)": None,
            "Barbell Max Height (px)": None,

            "Barbell X (m)": None,
            "Barbell Y (m)": None,
            "Barbell Z Depth (m)": None,
            "Barbell Horizontal Displacement (m)": None,
            "Barbell Vertical Displacement (m)": None,
            "Barbell Vertical Velocity (m/s)": None,
            "Barbell Horizontal Velocity (m/s)": None,
            "Barbell Max Height (m)": None,
        }

    def convert_cv_to_qimage(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w

        q_img = QImage(
            rgb_image.data,
            w,
            h,
            bytes_per_line,
            QImage.Format.Format_RGB888
        )

        return q_img.copy()

    def stop(self):
        self.running = False

        try:
            cv2.destroyAllWindows()
            cv2.waitKey(1)
        except Exception:
            pass