import time

from modules.phase_definitions import SETUP_PHASE


class PhaseDetector:
    """
    Weightlifting phase detector for BioMotion Studio.

    Final phase labels:

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

    Side View:
        Uses barbell motion.

    Front View:
        Uses pose landmarks, mainly wrist height relative to body.

    Important:
        - Setup is internal.
        - Phase logic is forward-only to reduce toggling.
        - Phase changes require short confirmation.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.phase = SETUP_PHASE

        self.lift_started = False
        self.lift_off_time = None

        self.frame_count = 0

        self.last_displacement = None
        self.last_velocity = 0.0
        self.max_displacement_seen = 0.0

        self.upward_motion_count = 0

        self.pending_phase = None
        self.pending_count = 0
        self.last_phase_change_time = time.time()

        self.catch_seen = False
        self.squat_seen = False
        self.jerk_seen = False

        self.final_stable_count = 0

        # Front-view memory
        self.initial_wrist_y = None
        self.previous_wrist_y = None
        self.front_upward_count = 0

    # ==========================================================
    # SIDE VIEW: BARBELL-BASED UPDATE
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

        self.max_displacement_seen = max(
            self.max_displacement_seen,
            displacement
        )

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

            return self.set_phase_forward_only(
                candidate,
                [
                    "Setup",
                    "Deadlift Phase",
                    "Jump Phase",
                    "Catch Phase",
                    "Overhead Squat Phase"
                ]
            )

        candidate = self.detect_clean_jerk_side_candidate(displacement, velocity)

        return self.set_phase_forward_only(
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
        Lift-off detection from barbell motion.

        It is intentionally relaxed because tracker movement can be noisy.
        """

        displacement_threshold = 4.0
        frame_delta_threshold = 1.0
        velocity_threshold = 10.0
        required_motion_frames = 2

        moved_from_start = displacement > displacement_threshold

        moved_from_previous = False

        if self.last_displacement is not None:
            moved_from_previous = (
                displacement - self.last_displacement
            ) > frame_delta_threshold

        velocity_up = velocity > velocity_threshold

        if moved_from_start or moved_from_previous or velocity_up:
            self.upward_motion_count += 1
        else:
            self.upward_motion_count = max(0, self.upward_motion_count - 1)

        return self.upward_motion_count >= required_motion_frames

    def detect_snatch_side_candidate(self, displacement, velocity):
        """
        Snatch side-view phases:
            Deadlift Phase
            Jump Phase
            Catch Phase
            Overhead Squat Phase
        """

        jump_start_height = 65.0
        catch_height = 115.0

        jump_velocity_threshold = 60.0
        stable_velocity_threshold = 18.0

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

        if displacement >= catch_height and abs(velocity) <= 25.0:
            self.catch_seen = True
            return "Catch Phase"

        if displacement >= catch_height and velocity < -5.0:
            self.catch_seen = True
            return "Catch Phase"

        if displacement >= jump_start_height or velocity >= jump_velocity_threshold:
            return "Jump Phase"

        return "Deadlift Phase"

    def detect_clean_jerk_side_candidate(self, displacement, velocity):
        """
        Clean & Jerk side-view phases:
            Deadlift Phase
            Jump Phase
            Catch Phase
            Squat Phase
            Jerk Phase
        """

        jump_start_height = 65.0
        catch_height = 100.0

        jump_velocity_threshold = 60.0
        stable_velocity_threshold = 22.0

        jerk_velocity_threshold = 50.0
        jerk_extra_height_threshold = 25.0

        now = time.time()

        if self.phase == "Jerk Phase":
            return "Jerk Phase"

        if self.phase == "Squat Phase":
            # After squat phase, a strong upward bar movement indicates jerk.
            if velocity >= jerk_velocity_threshold:
                self.jerk_seen = True
                return "Jerk Phase"

            return "Squat Phase"

        if self.phase == "Catch Phase":
            # After clean catch, short stable period becomes squat/recovery.
            if abs(velocity) <= stable_velocity_threshold:
                self.final_stable_count += 1
            else:
                self.final_stable_count = 0

            if self.final_stable_count >= 8:
                self.squat_seen = True
                return "Squat Phase"

            return "Catch Phase"

        if displacement >= catch_height and abs(velocity) <= 30.0:
            self.catch_seen = True
            return "Catch Phase"

        if displacement >= catch_height and velocity < -5.0:
            self.catch_seen = True
            return "Catch Phase"

        if displacement >= jump_start_height or velocity >= jump_velocity_threshold:
            return "Jump Phase"

        return "Deadlift Phase"

    # ==========================================================
    # FRONT VIEW: POSE-BASED UPDATE
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

        wrist_y = pose_data["wrist_y"]
        shoulder_y = pose_data["shoulder_y"]
        hip_y = pose_data["hip_y"]
        knee_y = pose_data["knee_y"]
        ankle_y = pose_data["ankle_y"]

        body_height = max(1.0, ankle_y - shoulder_y)

        # Larger ratio means wrists are higher in the body frame.
        wrist_height_ratio = (ankle_y - wrist_y) / body_height

        if self.initial_wrist_y is None:
            self.initial_wrist_y = wrist_y

        if not self.lift_started:
            if not self.detect_front_view_lift_start(wrist_y):
                self.previous_wrist_y = wrist_y
                return self.set_phase(SETUP_PHASE, force=True)

            self.lift_started = True
            self.lift_off_time = time.time()

        self.previous_wrist_y = wrist_y

        exercise_name = exercise.lower().strip()

        if "snatch" in exercise_name:
            candidate = self.detect_snatch_front_candidate(
                wrist_height_ratio=wrist_height_ratio,
                wrist_y=wrist_y,
                shoulder_y=shoulder_y,
                hip_y=hip_y,
                knee_y=knee_y
            )

            return self.set_phase_forward_only(
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
            hip_y=hip_y,
            knee_y=knee_y
        )

        return self.set_phase_forward_only(
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
        upward_threshold_px = 2.0
        initial_movement_threshold_px = 5.0
        required_frames = 2

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

    def detect_snatch_front_candidate(
        self,
        wrist_height_ratio,
        wrist_y,
        shoulder_y,
        hip_y,
        knee_y
    ):
        if self.phase == "Overhead Squat Phase":
            return "Overhead Squat Phase"

        if self.phase == "Catch Phase":
            self.final_stable_count += 1

            if self.final_stable_count >= 10:
                return "Overhead Squat Phase"

            return "Catch Phase"

        # Wrists above shoulder level indicates snatch catch.
        if wrist_y <= shoulder_y:
            self.catch_seen = True
            return "Catch Phase"

        if wrist_height_ratio >= 0.50:
            return "Jump Phase"

        return "Deadlift Phase"

    def detect_clean_jerk_front_candidate(
        self,
        wrist_height_ratio,
        wrist_y,
        shoulder_y,
        hip_y,
        knee_y
    ):
        if self.phase == "Jerk Phase":
            return "Jerk Phase"

        # Overhead position indicates jerk.
        if wrist_y <= shoulder_y - 15:
            self.jerk_seen = True
            return "Jerk Phase"

        if self.phase == "Squat Phase":
            return "Squat Phase"

        if self.phase == "Catch Phase":
            self.final_stable_count += 1

            if self.final_stable_count >= 8:
                return "Squat Phase"

            return "Catch Phase"

        # Front rack / shoulder level indicates clean catch.
        shoulder_zone = abs(wrist_y - shoulder_y)

        if shoulder_zone <= 50 or wrist_height_ratio >= 0.62:
            self.catch_seen = True
            return "Catch Phase"

        if wrist_height_ratio >= 0.45:
            return "Jump Phase"

        return "Deadlift Phase"

    def extract_front_view_pose_data(
        self,
        landmarks,
        pose_landmark_enum,
        image_width,
        image_height,
        min_visibility=0.45
    ):
        LM = pose_landmark_enum

        def avg_y(ids):
            values = []

            for idx in ids:
                lm = landmarks[idx]

                if hasattr(lm, "visibility") and lm.visibility < min_visibility:
                    continue

                values.append(float(lm.y * image_height))

            if not values:
                return None

            return sum(values) / len(values)

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

        required = [
            wrist_y,
            shoulder_y,
            hip_y,
            knee_y,
            ankle_y
        ]

        if any(value is None for value in required):
            return None

        return {
            "wrist_y": wrist_y,
            "shoulder_y": shoulder_y,
            "hip_y": hip_y,
            "knee_y": knee_y,
            "ankle_y": ankle_y
        }

    # ==========================================================
    # FORWARD-ONLY PHASE SMOOTHING
    # ==========================================================
    def set_phase_forward_only(self, candidate_phase, phase_order):
        if candidate_phase not in phase_order:
            return self.set_phase(candidate_phase, force=True)

        if self.phase not in phase_order:
            current_index = 0
        else:
            current_index = phase_order.index(self.phase)

        candidate_index = phase_order.index(candidate_phase)

        # Prevent backward phase toggling.
        if candidate_index < current_index:
            return self.phase

        if candidate_index == current_index:
            self.pending_phase = None
            self.pending_count = 0
            return self.phase

        if candidate_phase != self.pending_phase:
            self.pending_phase = candidate_phase
            self.pending_count = 1
        else:
            self.pending_count += 1

        required_confirmation_frames = 2

        if self.pending_count >= required_confirmation_frames:
            return self.set_phase(candidate_phase, force=True)

        return self.phase

    def set_phase(self, new_phase, force=False):
        if force or new_phase != self.phase:
            self.phase = new_phase
            self.last_phase_change_time = time.time()

        return self.phase