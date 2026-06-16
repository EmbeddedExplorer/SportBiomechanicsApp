import time
import importlib
from collections import deque

import cv2
import numpy as np


class BarbellTracker:
    """
    ROI-based barbell / plate tracker.

    Important:
    - This class never opens ROI selection windows.
    - ROI selection is handled from the Weightlifting UI before preview starts.
    - DLib is optional. If unavailable, OpenCV tracker is used.
    """

    def __init__(self, max_history=5000):
        self.history = deque(maxlen=max_history)

        self.initialized = False
        self.tracker = None
        self.tracker_type = None
        self.dlib_module = None

        self.bbox = None

        self.start_center_px = None
        self.last_center_px = None
        self.last_time = None

        self.start_point_m = None
        self.last_point_m = None

        self.max_vertical_displacement_px = 0.0
        self.max_vertical_displacement_m = 0.0

    def reset(self):
        self.history.clear()

        self.initialized = False
        self.tracker = None
        self.tracker_type = None
        self.dlib_module = None

        self.bbox = None

        self.start_center_px = None
        self.last_center_px = None
        self.last_time = None

        self.start_point_m = None
        self.last_point_m = None

        self.max_vertical_displacement_px = 0.0
        self.max_vertical_displacement_m = 0.0

    def create_tracker(self):
        """
        Try DLib first. If DLib is not installed, use OpenCV tracker.
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
        """
        Initialize tracker from pre-selected ROI.

        bbox:
            (x, y, w, h)
        """

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

    def update(self, frame, depth_frame=None, depth_intrinsics=None, initial_bbox=None):
        timestamp = time.time()

        if not self.initialized:
            if initial_bbox is None:
                return self.empty_metrics()

            ok = self.initialize_from_bbox(frame, initial_bbox)

            if not ok:
                return self.empty_metrics()

        success, bbox = self.update_tracker(frame)

        if not success or bbox is None:
            return self.empty_metrics()

        x, y, w, h = bbox

        center_x = int(x + w / 2)
        center_y = int(y + h / 2)

        if self.start_center_px is None:
            self.start_center_px = (center_x, center_y)

        start_x, start_y = self.start_center_px

        horizontal_displacement_px = center_x - start_x
        vertical_displacement_px = start_y - center_y

        self.max_vertical_displacement_px = max(
            self.max_vertical_displacement_px,
            vertical_displacement_px
        )

        vertical_velocity_px_s = 0.0
        horizontal_velocity_px_s = 0.0

        if self.last_center_px is not None and self.last_time is not None:
            dt = timestamp - self.last_time

            if dt > 0:
                last_x, last_y = self.last_center_px
                vertical_velocity_px_s = (last_y - center_y) / dt
                horizontal_velocity_px_s = (center_x - last_x) / dt

        point_m = self.get_3d_point_m(
            depth_frame=depth_frame,
            depth_intrinsics=depth_intrinsics,
            x=center_x,
            y=center_y
        )

        horizontal_displacement_m = None
        vertical_displacement_m = None
        depth_m = None
        vertical_velocity_m_s = None
        horizontal_velocity_m_s = None

        if point_m is not None:
            depth_m = point_m[2]

            if self.start_point_m is None:
                self.start_point_m = point_m

            sx, sy, sz = self.start_point_m
            px, py, pz = point_m

            horizontal_displacement_m = px - sx

            # RealSense Y-axis is downward.
            # Upward movement = negative change in Y.
            vertical_displacement_m = -(py - sy)

            self.max_vertical_displacement_m = max(
                self.max_vertical_displacement_m,
                vertical_displacement_m
            )

            if self.last_point_m is not None and self.last_time is not None:
                dt = timestamp - self.last_time

                if dt > 0:
                    lx, ly, lz = self.last_point_m
                    horizontal_velocity_m_s = (px - lx) / dt
                    vertical_velocity_m_s = -(py - ly) / dt

        self.last_center_px = (center_x, center_y)
        self.last_point_m = point_m
        self.last_time = timestamp
        self.bbox = (int(x), int(y), int(w), int(h))

        self.history.append({
            "time": timestamp,

            "x_px": center_x,
            "y_px": center_y,

            "horizontal_displacement_px": horizontal_displacement_px,
            "vertical_displacement_px": vertical_displacement_px,
            "vertical_velocity_px_s": vertical_velocity_px_s,
            "horizontal_velocity_px_s": horizontal_velocity_px_s,
            "max_vertical_displacement_px": self.max_vertical_displacement_px,

            "x_m": point_m[0] if point_m is not None else None,
            "y_m": point_m[1] if point_m is not None else None,
            "z_m": point_m[2] if point_m is not None else None,

            "horizontal_displacement_m": horizontal_displacement_m,
            "vertical_displacement_m": vertical_displacement_m,
            "vertical_velocity_m_s": vertical_velocity_m_s,
            "horizontal_velocity_m_s": horizontal_velocity_m_s,
            "max_vertical_displacement_m": self.max_vertical_displacement_m,
        })

        return {
            "Barbell Detected": True,

            "Barbell X (px)": center_x,
            "Barbell Y (px)": center_y,

            "Barbell Horizontal Displacement (px)": round(horizontal_displacement_px, 2),
            "Barbell Vertical Displacement (px)": round(vertical_displacement_px, 2),
            "Barbell Vertical Velocity (px/s)": round(vertical_velocity_px_s, 2),
            "Barbell Horizontal Velocity (px/s)": round(horizontal_velocity_px_s, 2),
            "Barbell Max Height (px)": round(self.max_vertical_displacement_px, 2),

            "Barbell X (m)": round(point_m[0], 4) if point_m is not None else None,
            "Barbell Y (m)": round(point_m[1], 4) if point_m is not None else None,
            "Barbell Z Depth (m)": round(depth_m, 4) if depth_m is not None else None,
            "Barbell Horizontal Displacement (m)": round(horizontal_displacement_m, 4) if horizontal_displacement_m is not None else None,
            "Barbell Vertical Displacement (m)": round(vertical_displacement_m, 4) if vertical_displacement_m is not None else None,
            "Barbell Vertical Velocity (m/s)": round(vertical_velocity_m_s, 4) if vertical_velocity_m_s is not None else None,
            "Barbell Horizontal Velocity (m/s)": round(horizontal_velocity_m_s, 4) if horizontal_velocity_m_s is not None else None,
            "Barbell Max Height (m)": round(self.max_vertical_displacement_m, 4) if self.max_vertical_displacement_m is not None else None,
        }

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

    def draw_overlay(self, frame, camera_view="Side View"):
        if not self.history:
            return frame

        points = [
            (int(item["x_px"]), int(item["y_px"]))
            for item in self.history
            if item["x_px"] is not None and item["y_px"] is not None
        ]

        if len(points) >= 2:
            pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], False, (0, 255, 255), 2)

        latest = self.history[-1]

        x = int(latest["x_px"])
        y = int(latest["y_px"])

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
            cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), (0, 0, 255), 2)

        if self.start_center_px is not None:
            start_x, _ = self.start_center_px

            cv2.line(
                frame,
                (start_x, 0),
                (start_x, frame.shape[0]),
                (255, 255, 0),
                1
            )

            label = "Start Reference" if camera_view == "Side View" else "Center Line"

            cv2.putText(
                frame,
                label,
                (start_x + 8, 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 0),
                1
            )

        return frame

    def empty_metrics(self):
        return {
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