import cv2
import numpy as np

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

from modules.biomechanics import compute_pose_metrics


class VideoThread(QThread):
    frame_ready = pyqtSignal(QImage)
    status_ready = pyqtSignal(str)
    metrics_ready = pyqtSignal(dict)

    def __init__(self, source_type="webcam", file_path="", camera_index=0):
        super().__init__()

        self.source_type = source_type
        self.file_path = file_path
        self.camera_index = camera_index
        self.running = False

        self.use_pose = True

        self.mp_pose = None
        self.pose = None
        self.mp_drawing = None

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

    def run(self):
        self.running = True

        if self.use_pose:
            self.setup_mediapipe()

        if self.source_type in ["realsense_live", "realsense_bag"]:
            self.run_realsense()
        elif self.source_type == "video_file":
            self.run_opencv_video(self.file_path)
        else:
            self.run_opencv_video(self.camera_index)

    def run_opencv_video(self, source):
        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            self.status_ready.emit("Could not open webcam/video source.")
            return

        self.status_ready.emit("OpenCV video feed started. Depth: Not available.")

        while self.running:
            ret, frame = cap.read()

            if not ret:
                self.status_ready.emit("Video ended or frame not available.")
                break

            frame = cv2.resize(frame, (640, 480))

            frame = self.process_pose_overlay(
                frame=frame,
                depth_frame=None,
                depth_available=False
            )

            q_img = self.convert_cv_to_qimage(frame)
            self.frame_ready.emit(q_img)

            self.msleep(30)

        cap.release()

        self.metrics_ready.emit(self.empty_metrics())
        self.status_ready.emit("Video feed stopped.")

    def run_realsense(self):
        pipeline = None
        started = False

        try:
            import pyrealsense2 as rs

            pipeline = rs.pipeline()
            config = rs.config()

            # ================= BAG FILE MODE =================
            if self.source_type == "realsense_bag":
                if not self.file_path:
                    self.status_ready.emit("No .bag file selected.")
                    return

                rs.config.enable_device_from_file(
                    config,
                    self.file_path,
                    repeat_playback=False
                )

                # Use recorded stream settings from the bag file.
                config.enable_all_streams()

            # ================= LIVE REALSENSE MODE =================
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
                playback = profile.get_device().as_playback()
                playback.set_real_time(False)

            align = rs.align(rs.stream.color)

            self.status_ready.emit("RealSense feed started. RGB + depth available.")

            while self.running:
                try:
                    frames = pipeline.wait_for_frames(timeout_ms=5000)
                except Exception:
                    self.status_ready.emit("No more RealSense frames available.")
                    break

                try:
                    aligned_frames = align.process(frames)
                except Exception:
                    aligned_frames = frames

                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()

                if not color_frame:
                    self.status_ready.emit("Color frame not available in this stream.")
                    continue

                color_image = np.asanyarray(color_frame.get_data())

                # Some .bag files store color as RGB instead of BGR.
                # This fixes blue/red swapped preview for recorded bags.
                if self.source_type == "realsense_bag":
                    color_image = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)

                color_image = self.process_pose_overlay(
                    frame=color_image,
                    depth_frame=depth_frame,
                    depth_available=depth_frame is not None
                )

                q_img = self.convert_cv_to_qimage(color_image)
                self.frame_ready.emit(q_img)

                if depth_frame:
                    h, w, _ = color_image.shape
                    center_x = w // 2
                    center_y = h // 2
                    center_depth = self.get_depth_value(depth_frame, center_x, center_y)

                    if center_depth is not None:
                        self.status_ready.emit(
                            f"RealSense RGB-D running | Center depth: {center_depth:.2f} m"
                        )
                    else:
                        self.status_ready.emit("RealSense RGB-D running | Center depth: N/A")
                else:
                    self.status_ready.emit(
                        "RealSense color running | Depth frame not available."
                    )

                self.msleep(30)

            self.metrics_ready.emit(self.empty_metrics())

            if started:
                pipeline.stop()

            self.status_ready.emit("RealSense feed stopped.")

        except Exception as e:
            if pipeline is not None and started:
                try:
                    pipeline.stop()
                except Exception:
                    pass

            self.metrics_ready.emit(self.empty_metrics())
            self.status_ready.emit(f"RealSense error: {e}")

    def process_pose_overlay(self, frame, depth_frame=None, depth_available=False):
        display_frame = frame.copy()
        h, w, _ = display_frame.shape

        center_x = w // 2
        center_y = h // 2

        center_depth = None
        athlete_depth = None

        if depth_available and depth_frame is not None:
            center_depth = self.get_depth_value(depth_frame, center_x, center_y)

            cv2.circle(display_frame, (center_x, center_y), 6, (255, 255, 0), -1)

            if center_depth is not None:
                cv2.putText(
                    display_frame,
                    f"Center Depth: {center_depth:.2f} m",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )
            else:
                cv2.putText(
                    display_frame,
                    "Center Depth: N/A",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )

        else:
            cv2.putText(
                display_frame,
                "Depth: Not available",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
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

                # Approximate athlete center using shoulders and hips
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
                        0.6,
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
                                (20, 70),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
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

                self.metrics_ready.emit(metrics)

            else:
                metrics = self.empty_metrics()
                metrics["Pose"] = "Not Detected"
                metrics["Center Depth (m)"] = center_depth
                self.metrics_ready.emit(metrics)

        return display_frame

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
            "Center Depth (m)": None
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

        if self.isRunning():
            if not self.wait(3000):
                self.terminate()
                self.wait()