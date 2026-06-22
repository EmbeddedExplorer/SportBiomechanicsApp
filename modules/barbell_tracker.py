import time
import importlib
from collections import deque

import cv2
import numpy as np

from modules.phase_definitions import (
    EXCLUDED_PLOT_PHASES,
    TRAJECTORY_END_PHASES
)


class BarbellTracker:
    """
    ROI-based barbell / plate tracker.

    Main logic:
    - Raw tracking starts immediately after ROI / automatic disk selection.
    - Setup movement is tracked internally but NOT drawn as final trajectory.
    - Final trajectory starts only when the phase leaves Setup.
    - Reference line is fixed at the first lifting-phase barbell center.
    - Trajectory stops extending after the final phase becomes stable.
    """

    def __init__(self, max_history=5000):
        self.max_history = max_history

        self.initialized = False
        self.tracker = None
        self.tracker_type = None
        self.dlib_module = None

        self.bbox = None

        # Raw tracking reference. This starts immediately after tracker initialization.
        self.raw_start_center_px = None
        self.raw_start_point_m = None

        self.current_center_px = None
        self.current_point_m = None

        self.last_center_px = None
        self.last_point_m = None
        self.last_time = None

        self.raw_max_vertical_displacement_px = 0.0
        self.raw_max_vertical_displacement_m = 0.0

        # Final trajectory reference. This starts only after Setup.
        self.trajectory_started = False
        self.trajectory_finished = False
        self.trajectory_reference_center_px = None
        self.trajectory_reference_point_m = None
        self.trajectory_history = deque(maxlen=max_history)

        self.final_stable_count = 0

        self.latest_raw_metrics = self.empty_metrics()
        self.last_trajectory_metrics = self.empty_trajectory_metrics()

    def reset(self):
        self.initialized = False
        self.tracker = None
        self.tracker_type = None
        self.dlib_module = None

        self.bbox = None

        self.raw_start_center_px = None
        self.raw_start_point_m = None

        self.current_center_px = None
        self.current_point_m = None

        self.last_center_px = None
        self.last_point_m = None
        self.last_time = None

        self.raw_max_vertical_displacement_px = 0.0
        self.raw_max_vertical_displacement_m = 0.0

        self.trajectory_started = False
        self.trajectory_finished = False
        self.trajectory_reference_center_px = None
        self.trajectory_reference_point_m = None
        self.trajectory_history.clear()

        self.final_stable_count = 0

        self.latest_raw_metrics = self.empty_metrics()
        self.last_trajectory_metrics = self.empty_trajectory_metrics()

    # ==========================================================
    # TRACKER CREATION
    # ==========================================================
    def create_tracker(self):
        """
        Try DLib first. If DLib is unavailable, use OpenCV trackers.
        """

        try:
            dlib = importlib.import_module("dlib")
            tracker = dlib.correlation_tracker()
            return tracker, "dlib", dlib
        except Exception:
            pass

        tracker_creators = []

        if hasattr(cv2, "legacy"):
            tracker_creators.extend([
                ("opencv_csrt", getattr(cv2.legacy, "TrackerCSRT_create", None)),
                ("opencv_kcf", getattr(cv2.legacy, "TrackerKCF_create", None)),
                ("opencv_mil", getattr(cv2.legacy, "TrackerMIL_create", None)),
                ("opencv_mosse", getattr(cv2.legacy, "TrackerMOSSE_create", None)),
            ])

        tracker_creators.extend([
            ("opencv_csrt", getattr(cv2, "TrackerCSRT_create", None)),
            ("opencv_kcf", getattr(cv2, "TrackerKCF_create", None)),
            ("opencv_mil", getattr(cv2, "TrackerMIL_create", None)),
        ])

        for tracker_name, creator in tracker_creators:
            if creator is not None:
                try:
                    return creator(), tracker_name, None
                except Exception:
                    continue

        return None, None, None

    def initialize_from_bbox(self, frame, bbox):
        if frame is None or bbox is None:
            return False

        x, y, w, h = bbox

        if w <= 5 or h <= 5:
            return False

        tracker, tracker_type, dlib_module = self.create_tracker()

        if tracker is None:
            print("No DLib/OpenCV tracker available.")
            return False

        self.tracker = tracker
        self.tracker_type = tracker_type
        self.dlib_module = dlib_module
        self.bbox = (int(x), int(y), int(w), int(h))

        if tracker_type == "dlib":
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            rect = self.dlib_module.rectangle(
                int(x),
                int(y),
                int(x + w),
                int(y + h)
            )

            self.tracker.start_track(rgb_frame, rect)

        else:
            self.tracker.init(frame, self.bbox)

        self.initialized = True
        return True

    # ==========================================================
    # RAW TRACKING UPDATE
    # ==========================================================
    def update(self, frame, depth_frame=None, depth_intrinsics=None, initial_bbox=None):
        timestamp = time.time()

        if not self.initialized:
            if initial_bbox is None:
                self.latest_raw_metrics = self.empty_metrics()
                return self.latest_raw_metrics

            ok = self.initialize_from_bbox(frame, initial_bbox)

            if not ok:
                self.latest_raw_metrics = self.empty_metrics()
                return self.latest_raw_metrics

        success, bbox = self.update_tracker(frame)

        if not success or bbox is None:
            self.latest_raw_metrics = self.empty_metrics()
            return self.latest_raw_metrics

        x, y, w, h = bbox

        center_x = int(x + w / 2)
        center_y = int(y + h / 2)

        self.current_center_px = (center_x, center_y)
        self.bbox = (int(x), int(y), int(w), int(h))

        if self.raw_start_center_px is None:
            self.raw_start_center_px = (center_x, center_y)

        raw_start_x, raw_start_y = self.raw_start_center_px

        raw_horizontal_displacement_px = center_x - raw_start_x
        raw_vertical_displacement_px = raw_start_y - center_y

        self.raw_max_vertical_displacement_px = max(
            self.raw_max_vertical_displacement_px,
            raw_vertical_displacement_px
        )

        raw_vertical_velocity_px_s = 0.0
        raw_horizontal_velocity_px_s = 0.0

        if self.last_center_px is not None and self.last_time is not None:
            dt = timestamp - self.last_time

            if dt > 0:
                last_x, last_y = self.last_center_px
                raw_vertical_velocity_px_s = (last_y - center_y) / dt
                raw_horizontal_velocity_px_s = (center_x - last_x) / dt

        point_m = self.get_3d_point_m(
            depth_frame=depth_frame,
            depth_intrinsics=depth_intrinsics,
            x=center_x,
            y=center_y
        )

        self.current_point_m = point_m

        raw_horizontal_displacement_m = None
        raw_vertical_displacement_m = None
        raw_depth_m = None
        raw_vertical_velocity_m_s = None
        raw_horizontal_velocity_m_s = None

        if point_m is not None:
            raw_depth_m = point_m[2]

            if self.raw_start_point_m is None:
                self.raw_start_point_m = point_m

            sx, sy, _ = self.raw_start_point_m
            px, py, _ = point_m

            raw_horizontal_displacement_m = px - sx
            raw_vertical_displacement_m = -(py - sy)

            self.raw_max_vertical_displacement_m = max(
                self.raw_max_vertical_displacement_m,
                raw_vertical_displacement_m
            )

            if self.last_point_m is not None and self.last_time is not None:
                dt = timestamp - self.last_time

                if dt > 0:
                    lx, ly, _ = self.last_point_m
                    raw_horizontal_velocity_m_s = (px - lx) / dt
                    raw_vertical_velocity_m_s = -(py - ly) / dt

        self.last_center_px = (center_x, center_y)
        self.last_point_m = point_m
        self.last_time = timestamp

        self.latest_raw_metrics = {
            "Barbell Detected": True,

            "Barbell X (px)": center_x,
            "Barbell Y (px)": center_y,

            "Barbell Raw Horizontal Displacement (px)": round(raw_horizontal_displacement_px, 2),
            "Barbell Raw Vertical Displacement (px)": round(raw_vertical_displacement_px, 2),
            "Barbell Raw Vertical Velocity (px/s)": round(raw_vertical_velocity_px_s, 2),
            "Barbell Raw Horizontal Velocity (px/s)": round(raw_horizontal_velocity_px_s, 2),
            "Barbell Raw Max Height (px)": round(self.raw_max_vertical_displacement_px, 2),

            "Barbell X (m)": round(point_m[0], 4) if point_m is not None else None,
            "Barbell Y (m)": round(point_m[1], 4) if point_m is not None else None,
            "Barbell Z Depth (m)": round(raw_depth_m, 4) if raw_depth_m is not None else None,

            "Barbell Raw Horizontal Displacement (m)": round(raw_horizontal_displacement_m, 4) if raw_horizontal_displacement_m is not None else None,
            "Barbell Raw Vertical Displacement (m)": round(raw_vertical_displacement_m, 4) if raw_vertical_displacement_m is not None else None,
            "Barbell Raw Vertical Velocity (m/s)": round(raw_vertical_velocity_m_s, 4) if raw_vertical_velocity_m_s is not None else None,
            "Barbell Raw Horizontal Velocity (m/s)": round(raw_horizontal_velocity_m_s, 4) if raw_horizontal_velocity_m_s is not None else None,
            "Barbell Raw Max Height (m)": round(self.raw_max_vertical_displacement_m, 4),

            # Final plotted trajectory values remain None during Setup.
            "Barbell Horizontal Displacement (px)": None,
            "Barbell Vertical Displacement (px)": None,
            "Barbell Vertical Velocity (px/s)": None,
            "Barbell Horizontal Velocity (px/s)": None,
            "Barbell Max Height (px)": None,

            "Barbell Horizontal Displacement (m)": None,
            "Barbell Vertical Displacement (m)": None,
            "Barbell Vertical Velocity (m/s)": None,
            "Barbell Horizontal Velocity (m/s)": None,
            "Barbell Max Height (m)": None,
        }

        return self.latest_raw_metrics

    # ==========================================================
    # FINAL TRAJECTORY UPDATE
    # ==========================================================
    def update_trajectory_state(self, phase, exercise=""):
        """
        Start trajectory only after Setup.
        This prevents setup adjustment movement from appearing in the final bar path.
        """

        if self.current_center_px is None:
            return self.empty_trajectory_metrics()

        if phase in EXCLUDED_PLOT_PHASES:
            return self.empty_trajectory_metrics()

        # Once locked, keep returning last values but do not extend path.
        if self.trajectory_finished:
            return self.last_trajectory_metrics

        if not self.trajectory_started:
            self.trajectory_started = True
            self.trajectory_reference_center_px = self.current_center_px
            self.trajectory_reference_point_m = self.current_point_m

        center_x, center_y = self.current_center_px
        ref_x, ref_y = self.trajectory_reference_center_px

        horizontal_displacement_px = center_x - ref_x
        vertical_displacement_px = ref_y - center_y

        vertical_velocity_px_s = self.latest_raw_metrics.get("Barbell Raw Vertical Velocity (px/s)")
        horizontal_velocity_px_s = self.latest_raw_metrics.get("Barbell Raw Horizontal Velocity (px/s)")

        max_height_px = 0.0

        if self.trajectory_history:
            max_height_px = max(
                item.get("vertical_displacement_px", 0.0)
                for item in self.trajectory_history
            )

        max_height_px = max(max_height_px, vertical_displacement_px)

        horizontal_displacement_m = None
        vertical_displacement_m = None
        vertical_velocity_m_s = None
        horizontal_velocity_m_s = None
        max_height_m = None

        if self.current_point_m is not None and self.trajectory_reference_point_m is not None:
            px, py, _ = self.current_point_m
            rx, ry, _ = self.trajectory_reference_point_m

            horizontal_displacement_m = px - rx
            vertical_displacement_m = -(py - ry)

            vertical_velocity_m_s = self.latest_raw_metrics.get("Barbell Raw Vertical Velocity (m/s)")
            horizontal_velocity_m_s = self.latest_raw_metrics.get("Barbell Raw Horizontal Velocity (m/s)")

            previous_m_values = [
                item.get("vertical_displacement_m")
                for item in self.trajectory_history
                if item.get("vertical_displacement_m") is not None
            ]

            if previous_m_values:
                max_height_m = max(previous_m_values)

            if max_height_m is None:
                max_height_m = vertical_displacement_m
            else:
                max_height_m = max(max_height_m, vertical_displacement_m)

        trajectory_record = {
            "phase": phase,
            "x_px": center_x,
            "y_px": center_y,
            "horizontal_displacement_px": horizontal_displacement_px,
            "vertical_displacement_px": vertical_displacement_px,
            "vertical_velocity_px_s": vertical_velocity_px_s,
            "horizontal_velocity_px_s": horizontal_velocity_px_s,
            "max_height_px": max_height_px,
            "horizontal_displacement_m": horizontal_displacement_m,
            "vertical_displacement_m": vertical_displacement_m,
            "vertical_velocity_m_s": vertical_velocity_m_s,
            "horizontal_velocity_m_s": horizontal_velocity_m_s,
            "max_height_m": max_height_m
        }

        self.trajectory_history.append(trajectory_record)

        self.last_trajectory_metrics = {
            "Barbell Horizontal Displacement (px)": round(horizontal_displacement_px, 2),
            "Barbell Vertical Displacement (px)": round(vertical_displacement_px, 2),
            "Barbell Vertical Velocity (px/s)": round(vertical_velocity_px_s, 2) if vertical_velocity_px_s is not None else None,
            "Barbell Horizontal Velocity (px/s)": round(horizontal_velocity_px_s, 2) if horizontal_velocity_px_s is not None else None,
            "Barbell Max Height (px)": round(max_height_px, 2),

            "Barbell Horizontal Displacement (m)": round(horizontal_displacement_m, 4) if horizontal_displacement_m is not None else None,
            "Barbell Vertical Displacement (m)": round(vertical_displacement_m, 4) if vertical_displacement_m is not None else None,
            "Barbell Vertical Velocity (m/s)": round(vertical_velocity_m_s, 4) if vertical_velocity_m_s is not None else None,
            "Barbell Horizontal Velocity (m/s)": round(horizontal_velocity_m_s, 4) if horizontal_velocity_m_s is not None else None,
            "Barbell Max Height (m)": round(max_height_m, 4) if max_height_m is not None else None,
        }

        self.check_trajectory_finish(phase, vertical_velocity_px_s)

        return self.last_trajectory_metrics

    def check_trajectory_finish(self, phase, vertical_velocity_px_s):
        """
        Stop extending trajectory after final phase becomes stable.

        Uses final app phase names:
        - Snatch final: Overhead Squat Phase
        - Clean & Jerk final: Jerk Phase
        """

        if phase not in TRAJECTORY_END_PHASES:
            self.final_stable_count = 0
            return

        try:
            velocity = abs(float(vertical_velocity_px_s))
        except Exception:
            velocity = 999.0

        if velocity <= 10.0:
            self.final_stable_count += 1
        else:
            self.final_stable_count = 0

        if self.final_stable_count >= 12:
            self.trajectory_finished = True

    def empty_trajectory_metrics(self):
        return {
            "Barbell Horizontal Displacement (px)": None,
            "Barbell Vertical Displacement (px)": None,
            "Barbell Vertical Velocity (px/s)": None,
            "Barbell Horizontal Velocity (px/s)": None,
            "Barbell Max Height (px)": None,

            "Barbell Horizontal Displacement (m)": None,
            "Barbell Vertical Displacement (m)": None,
            "Barbell Vertical Velocity (m/s)": None,
            "Barbell Horizontal Velocity (m/s)": None,
            "Barbell Max Height (m)": None,
        }

    # ==========================================================
    # TRACKER UPDATE
    # ==========================================================
    def update_tracker(self, frame):
        try:
            if self.tracker_type == "dlib":
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                self.tracker.update(rgb_frame)
                position = self.tracker.get_position()

                x = int(position.left())
                y = int(position.top())
                w = int(position.right() - position.left())
                h = int(position.bottom() - position.top())

                if w <= 0 or h <= 0:
                    return False, None

                return True, (x, y, w, h)

            success, bbox = self.tracker.update(frame)

            if not success:
                return False, None

            x, y, w, h = bbox
            return True, (int(x), int(y), int(w), int(h))

        except Exception:
            return False, None

    # ==========================================================
    # DEPTH / 3D HELPERS
    # ==========================================================
    def get_depth_value_near_pixel(self, depth_frame, x, y, window_size=5):
        if depth_frame is None:
            return None

        try:
            width = depth_frame.get_width()
            height = depth_frame.get_height()

            x = int(max(0, min(x, width - 1)))
            y = int(max(0, min(y, height - 1)))

            half = window_size // 2
            values = []

            for dy in range(-half, half + 1):
                for dx in range(-half, half + 1):
                    px = max(0, min(x + dx, width - 1))
                    py = max(0, min(y + dy, height - 1))

                    depth = depth_frame.get_distance(px, py)

                    if depth is not None and depth > 0:
                        values.append(depth)

            if not values:
                return None

            return float(np.median(values))

        except Exception:
            return None

    def get_3d_point_m(self, depth_frame, depth_intrinsics, x, y):
        if depth_frame is None or depth_intrinsics is None:
            return None

        depth_value = self.get_depth_value_near_pixel(depth_frame, x, y)

        if depth_value is None:
            return None

        try:
            import pyrealsense2 as rs

            point = rs.rs2_deproject_pixel_to_point(
                depth_intrinsics,
                [float(x), float(y)],
                float(depth_value)
            )

            return tuple(point)

        except Exception:
            return None

    # ==========================================================
    # OVERLAY
    # ==========================================================
    def draw_overlay(self, frame, camera_view="Side View", phase=""):
        if self.current_center_px is not None:
            x, y = self.current_center_px

            cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)

            cv2.putText(
                frame,
                "Barbell",
                (x + 10, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 0, 255),
                2
            )

        if self.bbox is not None:
            bx, by, bw, bh = self.bbox

            cv2.rectangle(
                frame,
                (bx, by),
                (bx + bw, by + bh),
                (0, 0, 255),
                2
            )

        points = [
            (int(item["x_px"]), int(item["y_px"]))
            for item in self.trajectory_history
            if item.get("x_px") is not None and item.get("y_px") is not None
        ]

        if len(points) >= 2:
            pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))

            cv2.polylines(
                frame,
                [pts],
                False,
                (0, 255, 255),
                2
            )

        if self.trajectory_reference_center_px is not None:
            ref_x, _ = self.trajectory_reference_center_px

            cv2.line(
                frame,
                (ref_x, 0),
                (ref_x, frame.shape[0]),
                (255, 255, 0),
                1
            )

            cv2.putText(
                frame,
                "Lift Start Reference",
                (ref_x + 8, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 0),
                1
            )

        if self.trajectory_finished:
            cv2.putText(
                frame,
                "Trajectory Locked",
                (20, frame.shape[0] - 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

        return frame

    # ==========================================================
    # EMPTY METRICS
    # ==========================================================
    def empty_metrics(self):
        return {
            "Barbell Detected": False,

            "Barbell X (px)": None,
            "Barbell Y (px)": None,

            "Barbell Raw Horizontal Displacement (px)": None,
            "Barbell Raw Vertical Displacement (px)": None,
            "Barbell Raw Vertical Velocity (px/s)": None,
            "Barbell Raw Horizontal Velocity (px/s)": None,
            "Barbell Raw Max Height (px)": None,

            "Barbell X (m)": None,
            "Barbell Y (m)": None,
            "Barbell Z Depth (m)": None,

            "Barbell Raw Horizontal Displacement (m)": None,
            "Barbell Raw Vertical Displacement (m)": None,
            "Barbell Raw Vertical Velocity (m/s)": None,
            "Barbell Raw Horizontal Velocity (m/s)": None,
            "Barbell Raw Max Height (m)": None,

            "Barbell Horizontal Displacement (px)": None,
            "Barbell Vertical Displacement (px)": None,
            "Barbell Vertical Velocity (px/s)": None,
            "Barbell Horizontal Velocity (px/s)": None,
            "Barbell Max Height (px)": None,

            "Barbell Horizontal Displacement (m)": None,
            "Barbell Vertical Displacement (m)": None,
            "Barbell Vertical Velocity (m/s)": None,
            "Barbell Horizontal Velocity (m/s)": None,
            "Barbell Max Height (m)": None,
        }