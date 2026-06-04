import cv2
import numpy as np

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage


class VideoThread(QThread):
    frame_ready = pyqtSignal(QImage)
    status_ready = pyqtSignal(str)

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
        self.status_ready.emit("Video feed stopped.")

    def run_realsense(self):
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

                aligned_frames = align.process(frames)

                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()

                if not color_frame or not depth_frame:
                    continue

                color_image = np.asanyarray(color_frame.get_data())

                color_image = self.process_pose_overlay(
                    frame=color_image,
                    depth_frame=depth_frame,
                    depth_available=True
                )

                q_img = self.convert_cv_to_qimage(color_image)
                self.frame_ready.emit(q_img)

                center_depth = depth_frame.get_distance(320, 240)

                self.status_ready.emit(
                    f"RealSense RGB-D running | Center depth: {center_depth:.2f} m"
                )

                self.msleep(30)

            pipeline.stop()
            self.status_ready.emit("RealSense feed stopped.")

        except Exception as e:
            self.status_ready.emit(f"RealSense error: {e}")

    def process_pose_overlay(self, frame, depth_frame=None, depth_available=False):
        display_frame = frame.copy()

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        athlete_depth = None

        if self.pose is not None:
            results = self.pose.process(rgb_frame)

            if results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    display_frame,
                    results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS
                )

                h, w, _ = display_frame.shape

                # Use approximate torso center from shoulders and hips
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
                    cx = int(sum(xs) / len(xs))
                    cy = int(sum(ys) / len(ys))

                    cv2.circle(display_frame, (cx, cy), 8, (0, 165, 255), -1)
                    cv2.putText(
                        display_frame,
                        "Athlete Center",
                        (cx + 10, cy),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 165, 255),
                        2
                    )

                    if depth_available and depth_frame is not None:
                        athlete_depth = depth_frame.get_distance(cx, cy)

        if depth_available and depth_frame is not None:
            center_depth = depth_frame.get_distance(320, 240)

            cv2.circle(display_frame, (320, 240), 6, (255, 255, 0), -1)

            cv2.putText(
                display_frame,
                f"Center Depth: {center_depth:.2f} m",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            if athlete_depth is not None and athlete_depth > 0:
                cv2.putText(
                    display_frame,
                    f"Athlete Depth: {athlete_depth:.2f} m",
                    (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 165, 255),
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

        return display_frame

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
        self.wait()