import cv2
import numpy as np

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

from modules.biomechanics import compute_pose_metrics
from modules.barbell_tracker import BarbellTracker
from modules.barbell_auto_detector import BarbellAutoDetector
from modules.phase_detector import PhaseDetector
from modules.sprinting_phase_detector import SprintingPhaseDetector


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
        self.barbell_auto_detector = BarbellAutoDetector()

        self.phase_detector = PhaseDetector()
        self.sprinting_phase_detector = SprintingPhaseDetector()

        self.auto_barbell_detection_reported = False

        # Used for selecting / correcting ROI from current preview frame.
        self.latest_frame_for_roi = None

    # ==========================================================
    # MEDIAPIPE
    # ==========================================================
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

    # ==========================================================
    # THREAD ENTRY
    # ==========================================================
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

    # ==========================================================
    # NORMAL VIDEO FILE
    # ==========================================================
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

    # ==========================================================
    # REALSENSE LIVE / BAG
    # ==========================================================
    def run_realsense(self):
        pipeline = None
        started = False

        try:
            import pyrealsense2 as rs

            pipeline = rs.pipeline()

            if self.source_type == "realsense_bag":
                config = rs.config()

                if not self.file_path:
                    self.status_ready.emit("No .bag file selected.")
                    return

                rs.config.enable_device_from_file(
                    config,
                    self.file_path,
                    repeat_playback=False
                )

                config.enable_all_streams()

                profile = pipeline.start(config)
                started = True

                try:
                    playback = profile.get_device().as_playback()
                    playback.set_real_time(False)
                except Exception:
                    pass

                self.status_ready.emit("RealSense .bag feed started.")

            else:
                profile = self.start_live_realsense_with_fallback(rs, pipeline)

                if profile is None:
                    self.status_ready.emit("Could not start live RealSense with available profiles.")
                    return

                started = True
                self.status_ready.emit("Live RealSense feed started.")

            align = rs.align(rs.stream.color)

            while self.running:
                try:
                    frames = pipeline.wait_for_frames(timeout_ms=600)

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
                color_image = self.normalize_realsense_color(
                    color_frame=color_frame,
                    color_image=color_image,
                    rs=rs
                )

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

                if depth_frame is not None:
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

    def start_live_realsense_with_fallback(self, rs, pipeline):
        """
        Tries several RealSense stream profiles.

        This helps when one profile is not supported by the connected camera
        or USB bandwidth is limited.
        """

        profiles_to_try = [
            {
                "name": "640x480 color + 640x480 depth @30",
                "color": (640, 480, rs.format.bgr8, 30),
                "depth": (640, 480, rs.format.z16, 30),
            },
            {
                "name": "640x480 color + 640x480 depth @15",
                "color": (640, 480, rs.format.bgr8, 15),
                "depth": (640, 480, rs.format.z16, 15),
            },
            {
                "name": "848x480 color + 848x480 depth @30",
                "color": (848, 480, rs.format.bgr8, 30),
                "depth": (848, 480, rs.format.z16, 30),
            },
            {
                "name": "640x480 color only @30",
                "color": (640, 480, rs.format.bgr8, 30),
                "depth": None,
            },
        ]

        last_error = None

        for item in profiles_to_try:
            config = rs.config()

            try:
                cw, ch, cf, cfps = item["color"]
                config.enable_stream(rs.stream.color, cw, ch, cf, cfps)

                if item["depth"] is not None:
                    dw, dh, df, dfps = item["depth"]
                    config.enable_stream(rs.stream.depth, dw, dh, df, dfps)

                profile = pipeline.start(config)

                self.status_ready.emit(f"Started RealSense profile: {item['name']}")
                return profile

            except Exception as e:
                last_error = e

                try:
                    pipeline.stop()
                except Exception:
                    pass

                continue

        if last_error is not None:
            self.status_ready.emit(f"RealSense profile error: {last_error}")

        return None

    def normalize_realsense_color(self, color_frame, color_image, rs):
        """
        Converts RealSense RGB frames to BGR only when needed.
        """

        try:
            fmt = color_frame.profile.as_video_stream_profile().format()

            if fmt == rs.format.rgb8:
                return cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)

            if fmt == rs.format.bgr8:
                return color_image

        except Exception:
            pass

        return color_image

    # ==========================================================
    # ROI SUPPORT
    # ==========================================================
    def get_latest_frame_copy(self):
        if self.latest_frame_for_roi is None:
            return None

        return self.latest_frame_for_roi.copy()

    def set_manual_barbell_roi(self, roi):
        """
        Allows the UI to update / correct the barbell ROI while preview is running.
        """

        if roi is None:
            return

        self.barbell_roi = roi
        self.barbell_tracker.reset()
        self.barbell_auto_detector.reset()
        self.auto_barbell_detection_reported = True

        self.status_ready.emit(f"Manual barbell ROI selected: {roi}")

    # ==========================================================
    # MAIN FRAME PROCESSING
    # ==========================================================
    def process_pose_overlay(
        self,
        frame,
        depth_frame=None,
        depth_available=False,
        depth_intrinsics=None
    ):
        display_frame = frame.copy()
        clean_frame_for_tracking = frame.copy()

        self.latest_frame_for_roi = clean_frame_for_tracking.copy()

        h, w, _ = display_frame.shape

        center_x = w // 2
        center_y = h // 2

        center_depth = None

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

        if self.pose is None:
            return display_frame

        results = self.pose.process(rgb_frame)

        if not results.pose_landmarks:
            metrics = self.empty_metrics()
            metrics["Pose"] = "Not Detected"
            metrics["Center Depth (m)"] = center_depth
            self.metrics_ready.emit(metrics)
            return display_frame

        self.mp_drawing.draw_landmarks(
            display_frame,
            results.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS
        )

        landmarks = results.pose_landmarks.landmark

        athlete_depth = self.draw_athlete_com(
            display_frame=display_frame,
            landmarks=landmarks,
            depth_frame=depth_frame,
            depth_available=depth_available,
            image_width=w,
            image_height=h
        )

        metrics = compute_pose_metrics(
            landmarks=landmarks,
            pose_landmark_enum=self.mp_pose.PoseLandmark,
            image_width=w,
            image_height=h,
            athlete_depth=athlete_depth,
            center_depth=center_depth
        )

        metrics["Pose"] = "Detected"

        # ======================================================
        # WEIGHTLIFTING
        # ======================================================
        if self.sport == "Weightlifting":

            if self.camera_view == "Side View":

                if self.barbell_roi is None:
                    auto_roi = self.barbell_auto_detector.detect(
                        frame=clean_frame_for_tracking,
                        landmarks=landmarks,
                        pose_landmark_enum=self.mp_pose.PoseLandmark
                    )

                    if auto_roi is not None:
                        self.barbell_roi = auto_roi

                        if not self.auto_barbell_detection_reported:
                            self.status_ready.emit(
                                f"Auto barbell disk detected: {auto_roi}"
                            )
                            self.auto_barbell_detection_reported = True

                if self.barbell_roi is not None:
                    barbell_metrics = self.barbell_tracker.update(
                        frame=clean_frame_for_tracking,
                        depth_frame=depth_frame if depth_available else None,
                        depth_intrinsics=depth_intrinsics,
                        initial_bbox=self.barbell_roi
                    )

                    # Important for Clean & Jerk:
                    # Jerk Phase starts only when barbell is clearly above athlete's head.
                    barbell_metrics = self.add_barbell_pose_reference_metrics(
                        barbell_metrics=barbell_metrics,
                        landmarks=landmarks,
                        image_width=w,
                        image_height=h
                    )

                    self.current_phase = self.phase_detector.update(
                        exercise=self.exercise,
                        barbell_metrics=barbell_metrics
                    )

                    trajectory_metrics = self.barbell_tracker.update_trajectory_state(
                        phase=self.current_phase,
                        exercise=self.exercise,
                        barbell_metrics=barbell_metrics
                    )

                    barbell_metrics.update(trajectory_metrics)
                    metrics.update(barbell_metrics)

                    self.barbell_tracker.draw_overlay(
                        display_frame,
                        camera_view=self.camera_view,
                        phase=self.current_phase
                    )

                else:
                    barbell_metrics = self.barbell_tracker.empty_metrics()
                    metrics.update(barbell_metrics)
                    self.current_phase = "Setup"

                    cv2.putText(
                        display_frame,
                        "Auto detecting barbell disk...",
                        (20, 175),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (0, 255, 255),
                        2
                    )

            elif self.camera_view == "Front View":
                barbell_metrics = self.barbell_tracker.empty_metrics()
                metrics.update(barbell_metrics)

                self.current_phase = self.phase_detector.update_front_view(
                    exercise=self.exercise,
                    landmarks=landmarks,
                    pose_landmark_enum=self.mp_pose.PoseLandmark,
                    image_width=w,
                    image_height=h
                )

            else:
                barbell_metrics = self.barbell_tracker.empty_metrics()
                metrics.update(barbell_metrics)
                self.current_phase = "Not Detected"

            metrics["Phase"] = self.current_phase
            metrics["Exercise"] = self.exercise
            metrics["Camera View"] = self.camera_view

            self.draw_weightlifting_overlay(display_frame)

        # ======================================================
        # SPRINTING
        # ======================================================
        elif self.sport == "Sprinting":
            self.current_phase = self.sprinting_phase_detector.update(
                landmarks=landmarks,
                pose_landmark_enum=self.mp_pose.PoseLandmark,
                image_width=w,
                image_height=h
            )

            metrics["Phase"] = self.current_phase
            metrics["Exercise"] = "Sprinting"
            metrics["Camera View"] = self.camera_view

            self.draw_sprinting_overlay(display_frame)

        else:
            metrics["Phase"] = "N/A"

        self.metrics_ready.emit(metrics)

        return display_frame

    # ==========================================================
    # BARBELL VS ATHLETE HEAD REFERENCE
    # ==========================================================
    def add_barbell_pose_reference_metrics(
        self,
        barbell_metrics,
        landmarks,
        image_width,
        image_height,
        min_visibility=0.45
    ):
        """
        Adds strict side-view pose reference information.

        Main use:
        Clean & Jerk Jerk Phase should start only when the barbell disk center
        is clearly above the athlete's head-top level.

        Important:
        Smaller y value means higher position in image coordinates.
        """

        try:
            if not barbell_metrics.get("Barbell Detected", False):
                barbell_metrics["Barbell Above Head"] = False
                return barbell_metrics

            barbell_y = barbell_metrics.get("Barbell Y (px)")

            if barbell_y is None:
                barbell_metrics["Barbell Above Head"] = False
                return barbell_metrics

            LM = self.mp_pose.PoseLandmark

            def visible_y(idx):
                lm = landmarks[idx]

                if hasattr(lm, "visibility") and lm.visibility < min_visibility:
                    return None

                return float(lm.y * image_height)

            def avg_y(ids):
                values = []

                for idx in ids:
                    y = visible_y(idx)

                    if y is not None:
                        values.append(y)

                if not values:
                    return None

                return sum(values) / len(values)

            head_points = []

            for idx in [
                LM.NOSE.value,
                LM.LEFT_EYE.value,
                LM.RIGHT_EYE.value,
                LM.LEFT_EAR.value,
                LM.RIGHT_EAR.value
            ]:
                y = visible_y(idx)

                if y is not None:
                    head_points.append(y)

            # Head top = highest visible head landmark.
            head_top_y = min(head_points) if head_points else None

            shoulder_y = avg_y([
                LM.LEFT_SHOULDER.value,
                LM.RIGHT_SHOULDER.value
            ])

            hip_y = avg_y([
                LM.LEFT_HIP.value,
                LM.RIGHT_HIP.value
            ])

            if head_top_y is None:
                if shoulder_y is not None and hip_y is not None:
                    torso_length = max(1.0, hip_y - shoulder_y)
                    head_top_y = shoulder_y - 0.55 * torso_length

            above_head = False
            head_clearance = None

            if head_top_y is not None:
                # Positive clearance means barbell disk center is above head-top.
                head_clearance = float(head_top_y) - float(barbell_y)

                # Strict overhead rule.
                # If Jerk is still early, increase 30.0 to 35.0 or 40.0.
                above_head = head_clearance >= 30.0

            barbell_metrics["Barbell Above Head"] = above_head
            barbell_metrics["Athlete Head Y (px)"] = round(head_top_y, 2) if head_top_y is not None else None
            barbell_metrics["Barbell Head Clearance (px)"] = (
                round(head_clearance, 2)
                if head_clearance is not None
                else None
            )

            return barbell_metrics

        except Exception:
            barbell_metrics["Barbell Above Head"] = False
            return barbell_metrics

    # ==========================================================
    # OVERLAYS
    # ==========================================================
    def draw_athlete_com(
        self,
        display_frame,
        landmarks,
        depth_frame,
        depth_available,
        image_width,
        image_height
    ):
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
                xs.append(int(lm.x * image_width))
                ys.append(int(lm.y * image_height))

        if not xs or not ys:
            return None

        athlete_x = int(sum(xs) / len(xs))
        athlete_y = int(sum(ys) / len(ys))

        cv2.circle(
            display_frame,
            (athlete_x, athlete_y),
            8,
            (0, 165, 255),
            -1
        )

        cv2.putText(
            display_frame,
            "Athlete COM",
            (athlete_x + 10, athlete_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 165, 255),
            2
        )

        athlete_depth = None

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

        return athlete_depth

    def draw_weightlifting_overlay(self, frame):
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

    def draw_sprinting_overlay(self, frame):
        if self.sport != "Sprinting":
            return

        overlay_lines = [
            "Exercise: Sprinting",
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

    # ==========================================================
    # DEPTH
    # ==========================================================
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

    # ==========================================================
    # EMPTY METRICS
    # ==========================================================
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

            "Barbell Raw Horizontal Displacement (px)": None,
            "Barbell Raw Vertical Displacement (px)": None,
            "Barbell Raw Vertical Velocity (px/s)": None,
            "Barbell Raw Horizontal Velocity (px/s)": None,
            "Barbell Raw Max Height (px)": None,

            "Barbell Horizontal Displacement (px)": None,
            "Barbell Vertical Displacement (px)": None,
            "Barbell Vertical Velocity (px/s)": None,
            "Barbell Horizontal Velocity (px/s)": None,
            "Barbell Max Height (px)": None,

            "Barbell X (m)": None,
            "Barbell Y (m)": None,
            "Barbell Z Depth (m)": None,

            "Barbell Raw Horizontal Displacement (m)": None,
            "Barbell Raw Vertical Displacement (m)": None,
            "Barbell Raw Vertical Velocity (m/s)": None,
            "Barbell Raw Horizontal Velocity (m/s)": None,
            "Barbell Raw Max Height (m)": None,

            "Barbell Horizontal Displacement (m)": None,
            "Barbell Vertical Displacement (m)": None,
            "Barbell Vertical Velocity (m/s)": None,
            "Barbell Horizontal Velocity (m/s)": None,
            "Barbell Max Height (m)": None,

            "Barbell Above Head": False,
            "Athlete Head Y (px)": None,
            "Barbell Head Clearance (px)": None,
        }

    # ==========================================================
    # QIMAGE + STOP
    # ==========================================================
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