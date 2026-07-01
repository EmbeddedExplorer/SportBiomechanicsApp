import time
import math

from modules.phase_definitions import SETUP_PHASE


class PhaseDetector:
    """
    Weightlifting phase detector.

    Snatch:
        Setup
        Deadlift Phase
        Jump Phase
        Catch Phase
        Overhead Squat Phase

    Clean & Jerk:
        Setup
        Deadlift Phase
        Jump Phase
        Catch Phase
        Squat Phase
        Jerk Phase

    Important:
        - Snatch logic is kept stable.
        - Clean & Jerk side view uses barbell above-head logic.
        - Clean & Jerk front view uses wrist/head-top overhead logic.
        - Setup remains Setup until true vertical lift-off is detected.
        - Horizontal barbell adjustment during Setup does not start Deadlift.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.phase = SETUP_PHASE

        self.lift_started = False
        self.lift_off_time = None

        self.frame_count = 0
        self.frames_in_phase = 0

        self.last_displacement = None
        self.last_velocity = 0.0
        self.max_displacement_seen = 0.0

        self.upward_motion_count = 0

        # Setup / lift-off stabilization
        self.setup_reference_displacement = None
        self.setup_min_displacement = None
        self.setup_max_displacement = None
        self.true_lift_confirm_count = 0

        self.pending_phase = None
        self.pending_count = 0
        self.last_phase_change_time = time.time()

        self.catch_seen = False
        self.squat_seen = False
        self.jerk_seen = False

        self.final_stable_count = 0

        # Clean & Jerk side-view memory
        self.clean_catch_displacement = None
        self.squat_start_displacement = None
        self.squat_lowest_displacement = None
        self.side_overhead_count = 0

        # Front-view memory
        self.initial_wrist_y = None
        self.initial_hip_y = None
        self.previous_wrist_y = None
        self.front_wrist_smooth_y = None
        self.front_previous_smooth_wrist_y = None
        self.front_upward_count = 0

        self.squat_start_wrist_y = None
        self.front_squat_lowest_wrist_y = None
        self.front_overhead_count = 0

        self.initial_knee_angle = None
        self.last_knee_angle = None

    # ==========================================================
    # SIDE VIEW UPDATE
    # ==========================================================
    def update(self, exercise, barbell_metrics):
        self.frame_count += 1

        if not barbell_metrics.get("Barbell Detected", False):
            return self.set_phase("Not Detected", force=True)

        displacement = (
            barbell_metrics.get("Barbell Raw Vertical Displacement (px)")
            if barbell_metrics.get("Barbell Raw Vertical Displacement (px)") is not None
            else barbell_metrics.get("Barbell Vertical Displacement (px)")
        )

        velocity = (
            barbell_metrics.get("Barbell Raw Vertical Velocity (px/s)")
            if barbell_metrics.get("Barbell Raw Vertical Velocity (px/s)") is not None
            else barbell_metrics.get("Barbell Vertical Velocity (px/s)")
        )

        if displacement is None:
            return self.set_phase("Not Detected", force=True)

        try:
            displacement = float(displacement)
        except Exception:
            return self.set_phase("Not Detected", force=True)

        try:
            velocity = float(velocity) if velocity is not None else 0.0
        except Exception:
            velocity = 0.0

        self.max_displacement_seen = max(self.max_displacement_seen, displacement)

        if not self.lift_started:
            if not self.detect_lift_off(displacement, velocity):
                self.last_displacement = displacement
                self.last_velocity = velocity
                return self.set_phase(SETUP_PHASE, force=True)

            self.lift_started = True
            self.lift_off_time = time.time()

        self.last_displacement = displacement
        self.last_velocity = velocity

        exercise_name = exercise.lower().strip()

        if "snatch" in exercise_name:
            candidate = self.detect_snatch_side_candidate(displacement, velocity)

            return self.apply_forward_order(
                candidate,
                [
                    "Setup",
                    "Deadlift Phase",
                    "Jump Phase",
                    "Catch Phase",
                    "Overhead Squat Phase"
                ]
            )

        candidate = self.detect_clean_jerk_side_candidate(
            displacement=displacement,
            velocity=velocity,
            barbell_metrics=barbell_metrics
        )

        return self.apply_forward_order(
            candidate,
            [
                "Setup",
                "Deadlift Phase",
                "Jump Phase",
                "Catch Phase",
                "Squat Phase",
                "Jerk Phase"
            ]
        )

    def detect_lift_off(self, displacement, velocity):
        """
        Detect true lift-off from Setup.

        Updated logic:
        - Horizontal barbell adjustment during Setup should not start Deadlift.
        - Small vertical jitter should not start Deadlift.
        - Deadlift starts only after clear upward vertical displacement.
        - Reference line will be drawn from the true lift-start point because
          trajectory starts only when phase leaves Setup.
        """

        vertical_lift_threshold_px = 12.0
        frame_delta_threshold_px = 1.5
        velocity_threshold_px_s = 8.0
        required_confirm_frames = 3

        if self.setup_reference_displacement is None:
            self.setup_reference_displacement = displacement
            self.setup_min_displacement = displacement
            self.setup_max_displacement = displacement
            self.last_displacement = displacement
            self.true_lift_confirm_count = 0
            return False

        self.setup_min_displacement = min(
            self.setup_min_displacement,
            displacement
        )

        self.setup_max_displacement = max(
            self.setup_max_displacement,
            displacement
        )

        vertical_gain_from_setup = displacement - self.setup_min_displacement

        moved_up_from_previous = False

        if self.last_displacement is not None:
            moved_up_from_previous = (
                displacement - self.last_displacement
            ) >= frame_delta_threshold_px

        velocity_up = velocity >= velocity_threshold_px_s

        clear_vertical_lift = vertical_gain_from_setup >= vertical_lift_threshold_px

        if clear_vertical_lift and (moved_up_from_previous or velocity_up):
            self.true_lift_confirm_count += 1
        else:
            self.true_lift_confirm_count = max(
                0,
                self.true_lift_confirm_count - 1
            )

        return self.true_lift_confirm_count >= required_confirm_frames

    # ==========================================================
    # SNATCH SIDE VIEW
    # ==========================================================
    def detect_snatch_side_candidate(self, displacement, velocity):
        jump_start_height = 65.0
        catch_height = 115.0

        jump_velocity_threshold = 60.0
        stable_velocity_threshold = 18.0

        if self.phase == SETUP_PHASE:
            return "Deadlift Phase"

        if self.phase == "Deadlift Phase":
            if self.frames_in_phase < 4:
                return "Deadlift Phase"

            if displacement >= jump_start_height or velocity >= jump_velocity_threshold:
                return "Jump Phase"

            return "Deadlift Phase"

        if self.phase == "Jump Phase":
            if self.frames_in_phase < 4:
                return "Jump Phase"

            if displacement >= catch_height and abs(velocity) <= 25.0:
                return "Catch Phase"

            if displacement >= catch_height and velocity < -5.0:
                return "Catch Phase"

            return "Jump Phase"

        if self.phase == "Catch Phase":
            if abs(velocity) <= stable_velocity_threshold:
                self.final_stable_count += 1
            else:
                self.final_stable_count = 0

            if self.final_stable_count >= 10:
                return "Overhead Squat Phase"

            return "Catch Phase"

        if self.phase == "Overhead Squat Phase":
            return "Overhead Squat Phase"

        return "Deadlift Phase"

    # ==========================================================
    # CLEAN & JERK SIDE VIEW
    # ==========================================================
    def detect_clean_jerk_side_candidate(self, displacement, velocity, barbell_metrics):
        """
        Clean & Jerk side view.

        Corrected rule:
        Jerk Phase starts only when the barbell disk center is clearly above
        the athlete's head-top level.

        Therefore:
        - Catch Phase = clean catch/front rack briefly.
        - Squat Phase = recovery, dip, and early drive.
        - Jerk Phase = barbell clearly overhead.
        """

        jump_start_height = 65.0
        catch_height = 100.0

        jump_velocity_threshold = 60.0
        catch_velocity_threshold = 32.0

        barbell_above_head = bool(barbell_metrics.get("Barbell Above Head", False))

        if self.phase == SETUP_PHASE:
            return "Deadlift Phase"

        if self.phase == "Deadlift Phase":
            if self.frames_in_phase < 4:
                return "Deadlift Phase"

            if displacement >= jump_start_height or velocity >= jump_velocity_threshold:
                return "Jump Phase"

            return "Deadlift Phase"

        if self.phase == "Jump Phase":
            if self.frames_in_phase < 4:
                return "Jump Phase"

            if displacement >= catch_height and abs(velocity) <= catch_velocity_threshold:
                self.catch_seen = True
                return "Catch Phase"

            if displacement >= catch_height and velocity < -5.0:
                self.catch_seen = True
                return "Catch Phase"

            return "Jump Phase"

        if self.phase == "Catch Phase":
            if self.clean_catch_displacement is None:
                self.clean_catch_displacement = displacement

            if self.frames_in_phase >= 10:
                self.squat_seen = True
                return "Squat Phase"

            return "Catch Phase"

        if self.phase == "Squat Phase":
            if self.squat_start_displacement is None:
                self.squat_start_displacement = displacement

            if self.squat_lowest_displacement is None:
                self.squat_lowest_displacement = displacement

            self.squat_lowest_displacement = min(
                self.squat_lowest_displacement,
                displacement
            )

            if self.frames_in_phase >= 12:
                if barbell_above_head:
                    self.side_overhead_count += 1
                else:
                    self.side_overhead_count = max(0, self.side_overhead_count - 1)

                if self.side_overhead_count >= 5:
                    self.jerk_seen = True
                    return "Jerk Phase"

            return "Squat Phase"

        if self.phase == "Jerk Phase":
            return "Jerk Phase"

        return "Deadlift Phase"

    # ==========================================================
    # FRONT VIEW UPDATE
    # ==========================================================
    def update_front_view(
        self,
        exercise,
        landmarks,
        pose_landmark_enum,
        image_width,
        image_height
    ):
        self.frame_count += 1

        pose_data = self.extract_front_view_pose_data(
            landmarks=landmarks,
            pose_landmark_enum=pose_landmark_enum,
            image_width=image_width,
            image_height=image_height
        )

        if pose_data is None:
            return self.set_phase("Not Detected", force=True)

        raw_wrist_y = pose_data["wrist_y"]
        shoulder_y = pose_data["shoulder_y"]
        hip_y = pose_data["hip_y"]
        ankle_y = pose_data["ankle_y"]
        head_y = pose_data["head_y"]
        knee_angle = pose_data["knee_angle"]

        body_height = max(1.0, ankle_y - shoulder_y)

        if self.front_wrist_smooth_y is None:
            self.front_wrist_smooth_y = raw_wrist_y
        else:
            alpha = 0.72
            self.front_wrist_smooth_y = (
                alpha * self.front_wrist_smooth_y
                + (1.0 - alpha) * raw_wrist_y
            )

        wrist_y = self.front_wrist_smooth_y
        wrist_height_ratio = (ankle_y - wrist_y) / body_height

        if self.initial_wrist_y is None:
            self.initial_wrist_y = wrist_y

        if self.initial_hip_y is None:
            self.initial_hip_y = hip_y

        if self.initial_knee_angle is None and knee_angle is not None:
            self.initial_knee_angle = knee_angle

        if not self.lift_started:
            if not self.detect_front_view_lift_start(wrist_y):
                self.previous_wrist_y = wrist_y
                self.front_previous_smooth_wrist_y = wrist_y
                return self.set_phase(SETUP_PHASE, force=True)

            self.lift_started = True
            self.lift_off_time = time.time()

        wrist_velocity_up = 0.0

        if self.front_previous_smooth_wrist_y is not None:
            wrist_velocity_up = self.front_previous_smooth_wrist_y - wrist_y

        self.previous_wrist_y = wrist_y
        self.front_previous_smooth_wrist_y = wrist_y
        self.last_knee_angle = knee_angle

        exercise_name = exercise.lower().strip()

        if "snatch" in exercise_name:
            candidate = self.detect_snatch_front_candidate(
                wrist_height_ratio=wrist_height_ratio,
                wrist_y=wrist_y,
                shoulder_y=shoulder_y
            )

            return self.apply_forward_order(
                candidate,
                [
                    "Setup",
                    "Deadlift Phase",
                    "Jump Phase",
                    "Catch Phase",
                    "Overhead Squat Phase"
                ]
            )

        candidate = self.detect_clean_jerk_front_candidate(
            wrist_height_ratio=wrist_height_ratio,
            wrist_y=wrist_y,
            shoulder_y=shoulder_y,
            head_y=head_y,
            hip_y=hip_y,
            body_height=body_height,
            knee_angle=knee_angle,
            wrist_velocity_up=wrist_velocity_up
        )

        return self.apply_forward_order(
            candidate,
            [
                "Setup",
                "Deadlift Phase",
                "Jump Phase",
                "Catch Phase",
                "Squat Phase",
                "Jerk Phase"
            ]
        )

    def detect_front_view_lift_start(self, wrist_y):
        upward_threshold_px = 1.8
        initial_movement_threshold_px = 5.0
        required_frames = 3

        moved_from_initial = False

        if self.initial_wrist_y is not None:
            moved_from_initial = (
                self.initial_wrist_y - wrist_y
            ) > initial_movement_threshold_px

        moved_from_previous = False

        if self.previous_wrist_y is not None:
            moved_from_previous = (
                self.previous_wrist_y - wrist_y
            ) > upward_threshold_px

        if moved_from_initial or moved_from_previous:
            self.front_upward_count += 1
        else:
            self.front_upward_count = max(0, self.front_upward_count - 1)

        return self.front_upward_count >= required_frames

    # ==========================================================
    # SNATCH FRONT VIEW
    # ==========================================================
    def detect_snatch_front_candidate(
        self,
        wrist_height_ratio,
        wrist_y,
        shoulder_y
    ):
        min_deadlift_frames = 12
        min_jump_frames = 10
        min_catch_frames = 18

        if self.phase == SETUP_PHASE:
            return "Deadlift Phase"

        if self.phase == "Deadlift Phase":
            if self.frames_in_phase < min_deadlift_frames:
                return "Deadlift Phase"

            if wrist_height_ratio >= 0.45:
                return "Jump Phase"

            return "Deadlift Phase"

        if self.phase == "Jump Phase":
            if self.frames_in_phase < min_jump_frames:
                return "Jump Phase"

            if wrist_y <= shoulder_y:
                self.catch_seen = True
                return "Catch Phase"

            if wrist_height_ratio >= 0.72:
                self.catch_seen = True
                return "Catch Phase"

            return "Jump Phase"

        if self.phase == "Catch Phase":
            if self.frames_in_phase < min_catch_frames:
                return "Catch Phase"

            return "Overhead Squat Phase"

        if self.phase == "Overhead Squat Phase":
            return "Overhead Squat Phase"

        return "Deadlift Phase"

    # ==========================================================
    # CLEAN & JERK FRONT VIEW
    # ==========================================================
    def detect_clean_jerk_front_candidate(
        self,
        wrist_height_ratio,
        wrist_y,
        shoulder_y,
        head_y,
        hip_y,
        body_height,
        knee_angle,
        wrist_velocity_up
    ):
        """
        Front-view Clean & Jerk.

        Updated rule:
        Jerk Phase starts only when the wrists/bar region is clearly above
        the athlete's head-top level.

        Therefore:
        - Catch Phase = clean catch/front rack.
        - Squat Phase = recovery, dip, and early upward drive.
        - Jerk Phase = overhead position only.
        """

        min_deadlift_frames = 20
        min_jump_frames = 14
        min_catch_frames = 20
        min_squat_frames = 28

        shoulder_zone = abs(wrist_y - shoulder_y)

        hip_drop_ratio = 0.0
        if self.initial_hip_y is not None:
            hip_drop_ratio = (hip_y - self.initial_hip_y) / body_height

        knee_is_bent = False
        if knee_angle is not None:
            knee_is_bent = knee_angle <= 145.0

        if self.phase == SETUP_PHASE:
            return "Deadlift Phase"

        if self.phase == "Deadlift Phase":
            if self.frames_in_phase < min_deadlift_frames:
                return "Deadlift Phase"

            if wrist_height_ratio >= 0.36 or wrist_velocity_up >= 2.5:
                return "Jump Phase"

            return "Deadlift Phase"

        if self.phase == "Jump Phase":
            if self.frames_in_phase < min_jump_frames:
                return "Jump Phase"

            if shoulder_zone <= 60:
                self.catch_seen = True
                return "Catch Phase"

            if wrist_height_ratio >= 0.58:
                self.catch_seen = True
                return "Catch Phase"

            return "Jump Phase"

        if self.phase == "Catch Phase":
            if self.frames_in_phase < min_catch_frames:
                return "Catch Phase"

            if knee_is_bent or hip_drop_ratio >= 0.04:
                self.squat_seen = True
                return "Squat Phase"

            if self.frames_in_phase >= min_catch_frames + 12:
                self.squat_seen = True
                return "Squat Phase"

            return "Catch Phase"

        if self.phase == "Squat Phase":
            if self.squat_start_wrist_y is None:
                self.squat_start_wrist_y = wrist_y

            if self.front_squat_lowest_wrist_y is None:
                self.front_squat_lowest_wrist_y = wrist_y

            self.front_squat_lowest_wrist_y = max(
                self.front_squat_lowest_wrist_y,
                wrist_y
            )

            wrist_up_after_dip = self.front_squat_lowest_wrist_y - wrist_y

            head_clearance = head_y - wrist_y
            wrist_above_head = head_clearance >= 30.0

            if self.frames_in_phase < min_squat_frames:
                return "Squat Phase"

            if wrist_above_head:
                self.front_overhead_count += 1
            else:
                self.front_overhead_count = max(0, self.front_overhead_count - 1)

            if self.front_overhead_count >= 5 and wrist_up_after_dip >= 12.0:
                self.jerk_seen = True
                return "Jerk Phase"

            return "Squat Phase"

        if self.phase == "Jerk Phase":
            return "Jerk Phase"

        return "Deadlift Phase"

    # ==========================================================
    # LANDMARK EXTRACTION
    # ==========================================================
    def extract_front_view_pose_data(
        self,
        landmarks,
        pose_landmark_enum,
        image_width,
        image_height,
        min_visibility=0.45
    ):
        LM = pose_landmark_enum

        def visible_xy(idx):
            lm = landmarks[idx]

            if hasattr(lm, "visibility") and lm.visibility < min_visibility:
                return None

            return (
                float(lm.x * image_width),
                float(lm.y * image_height)
            )

        def avg_y(ids):
            values = []

            for idx in ids:
                point = visible_xy(idx)

                if point is None:
                    continue

                _, y = point
                values.append(y)

            if not values:
                return None

            return sum(values) / len(values)

        def angle_2d(a, b, c):
            if a is None or b is None or c is None:
                return None

            ax, ay = a
            bx, by = b
            cx, cy = c

            v1 = (ax - bx, ay - by)
            v2 = (cx - bx, cy - by)

            dot = v1[0] * v2[0] + v1[1] * v2[1]
            mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
            mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

            if mag1 == 0 or mag2 == 0:
                return None

            cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
            return math.degrees(math.acos(cos_angle))

        wrist_y = avg_y([
            LM.LEFT_WRIST.value,
            LM.RIGHT_WRIST.value
        ])

        shoulder_y = avg_y([
            LM.LEFT_SHOULDER.value,
            LM.RIGHT_SHOULDER.value
        ])

        hip_y = avg_y([
            LM.LEFT_HIP.value,
            LM.RIGHT_HIP.value
        ])

        knee_y = avg_y([
            LM.LEFT_KNEE.value,
            LM.RIGHT_KNEE.value
        ])

        ankle_y = avg_y([
            LM.LEFT_ANKLE.value,
            LM.RIGHT_ANKLE.value
        ])

        head_points = []

        for idx in [
            LM.NOSE.value,
            LM.LEFT_EYE.value,
            LM.RIGHT_EYE.value,
            LM.LEFT_EAR.value,
            LM.RIGHT_EAR.value
        ]:
            point = visible_xy(idx)

            if point is not None:
                _, y = point
                head_points.append(y)

        head_y = min(head_points) if head_points else None

        left_knee_angle = angle_2d(
            visible_xy(LM.LEFT_HIP.value),
            visible_xy(LM.LEFT_KNEE.value),
            visible_xy(LM.LEFT_ANKLE.value)
        )

        right_knee_angle = angle_2d(
            visible_xy(LM.RIGHT_HIP.value),
            visible_xy(LM.RIGHT_KNEE.value),
            visible_xy(LM.RIGHT_ANKLE.value)
        )

        knee_angles = [
            angle for angle in [left_knee_angle, right_knee_angle]
            if angle is not None
        ]

        knee_angle = None
        if knee_angles:
            knee_angle = sum(knee_angles) / len(knee_angles)

        required = [
            wrist_y,
            shoulder_y,
            hip_y,
            knee_y,
            ankle_y
        ]

        if any(value is None for value in required):
            return None

        if head_y is None:
            torso_length = max(1.0, hip_y - shoulder_y)
            head_y = shoulder_y - 0.45 * torso_length

        return {
            "wrist_y": wrist_y,
            "shoulder_y": shoulder_y,
            "hip_y": hip_y,
            "knee_y": knee_y,
            "ankle_y": ankle_y,
            "head_y": head_y,
            "knee_angle": knee_angle
        }

    # ==========================================================
    # ORDER CONTROL
    # ==========================================================
    def apply_forward_order(self, candidate_phase, phase_order):
        if candidate_phase not in phase_order:
            return self.set_phase(candidate_phase, force=True)

        if self.phase not in phase_order:
            current_index = 0
        else:
            current_index = phase_order.index(self.phase)

        candidate_index = phase_order.index(candidate_phase)

        if candidate_index < current_index:
            return self.set_phase(self.phase)

        if candidate_index == current_index:
            self.pending_phase = None
            self.pending_count = 0
            return self.set_phase(self.phase)

        if candidate_index > current_index + 1:
            candidate_phase = phase_order[current_index + 1]

        if self.phase == SETUP_PHASE:
            required_confirmation_frames = 1
        else:
            required_confirmation_frames = 4

        if candidate_phase != self.pending_phase:
            self.pending_phase = candidate_phase
            self.pending_count = 1
        else:
            self.pending_count += 1

        if self.pending_count >= required_confirmation_frames:
            return self.set_phase(candidate_phase, force=True)

        return self.set_phase(self.phase)

    def set_phase(self, new_phase, force=False):
        if force or new_phase != self.phase:
            previous_phase = self.phase
            self.phase = new_phase
            self.frames_in_phase = 0
            self.last_phase_change_time = time.time()

            if new_phase == "Catch Phase":
                self.catch_seen = True
                self.final_stable_count = 0

            if new_phase == "Squat Phase":
                self.squat_seen = True

                self.squat_start_displacement = self.last_displacement
                self.squat_lowest_displacement = self.last_displacement
                self.side_overhead_count = 0

                self.squat_start_wrist_y = self.previous_wrist_y
                self.front_squat_lowest_wrist_y = self.previous_wrist_y
                self.front_overhead_count = 0

            if new_phase == "Jerk Phase":
                self.jerk_seen = True

            if previous_phase != new_phase:
                self.pending_phase = None
                self.pending_count = 0

        else:
            self.frames_in_phase += 1

        return self.phase