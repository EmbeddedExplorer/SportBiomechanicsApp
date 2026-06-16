import time


class PhaseDetector:
    """
    Rule-based phase detector for V9.

    This is an initial practical detector using estimated barbell movement.
    It will improve later when OpenCV/DLib barbell tracking and validated thresholds are added.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.phase = "Not Detected"

        self.lift_started = False
        self.clean_catch_seen = False
        self.jerk_drive_seen = False
        self.jerk_catch_seen = False

        self.phase_start_time = time.time()
        self.clean_catch_time = None
        self.last_phase_change_time = time.time()

    def update(self, exercise, barbell_metrics):
        if not barbell_metrics.get("Barbell Detected", False):
            self.phase = "Not Detected"
            return self.phase

        displacement = barbell_metrics.get("Barbell Vertical Displacement (px)")
        velocity = barbell_metrics.get("Barbell Vertical Velocity (px/s)")
        max_height = barbell_metrics.get("Barbell Max Height (px)")

        if displacement is None or velocity is None:
            self.phase = "Not Detected"
            return self.phase

        if exercise == "Snatch":
            return self.detect_snatch_phase(
                displacement=displacement,
                velocity=velocity,
                max_height=max_height
            )

        return self.detect_clean_jerk_phase(
            displacement=displacement,
            velocity=velocity,
            max_height=max_height
        )

    def set_phase(self, new_phase):
        if new_phase != self.phase:
            self.phase = new_phase
            self.last_phase_change_time = time.time()

        return self.phase

    def detect_snatch_phase(self, displacement, velocity, max_height):
        abs_velocity = abs(velocity)

        if not self.lift_started:
            if displacement < 15 and abs_velocity < 60:
                return self.set_phase("Setup")

            if displacement >= 15 or velocity > 60:
                self.lift_started = True
                return self.set_phase("First Pull")

        if displacement < 80:
            return self.set_phase("First Pull")

        if 80 <= displacement < 130:
            return self.set_phase("Transition")

        if displacement >= 130 and velocity > 100:
            return self.set_phase("Second Pull")

        if max_height is not None and max_height > 140:
            if velocity <= 60 and velocity > -80:
                return self.set_phase("Turnover")

            if velocity <= -80:
                return self.set_phase("Catch")

        if self.phase == "Catch" and abs_velocity < 45:
            return self.set_phase("Recovery")

        return self.phase

    def detect_clean_jerk_phase(self, displacement, velocity, max_height):
        abs_velocity = abs(velocity)
        now = time.time()

        if not self.lift_started:
            if displacement < 15 and abs_velocity < 60:
                return self.set_phase("Setup")

            if displacement >= 15 or velocity > 60:
                self.lift_started = True
                return self.set_phase("First Pull")

        if not self.clean_catch_seen:
            if displacement < 80:
                return self.set_phase("First Pull")

            if 80 <= displacement < 130:
                return self.set_phase("Transition")

            if displacement >= 130 and velocity > 100:
                return self.set_phase("Second Pull")

            if displacement >= 120 and velocity <= 50:
                self.clean_catch_seen = True
                self.clean_catch_time = now
                return self.set_phase("Clean Catch")

            return self.phase

        if self.clean_catch_seen and not self.jerk_drive_seen:
            elapsed_after_clean = now - self.clean_catch_time if self.clean_catch_time else 0

            if elapsed_after_clean < 1.5:
                return self.set_phase("Front Squat Recovery")

            if velocity < -45:
                return self.set_phase("Jerk Dip")

            if velocity > 80:
                self.jerk_drive_seen = True
                return self.set_phase("Jerk Drive")

            return self.phase

        if self.jerk_drive_seen and not self.jerk_catch_seen:
            if velocity <= 40:
                self.jerk_catch_seen = True
                return self.set_phase("Jerk Catch / Split")

            return self.set_phase("Jerk Drive")

        if self.jerk_catch_seen:
            if abs_velocity < 45:
                return self.set_phase("Recovery")

        return self.phase