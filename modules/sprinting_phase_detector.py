class SprintingPhaseDetector:
    """
    Simple side-view sprinting phase detector.

    Final phases:
        Initial Contact
        Support Phase
        Toe-Off
        Flight / Swing

    It uses foot / ankle / heel landmarks to estimate ground contact.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.phase = "Not Detected"

        self.frame_count = 0
        self.ground_y = None

        self.previous_contact = None
        self.previous_foot_y = None

        self.phase_hold_count = 0

    def update(self, landmarks, pose_landmark_enum, image_width, image_height):
        self.frame_count += 1

        foot_data = self.get_lowest_visible_foot(
            landmarks=landmarks,
            pose_landmark_enum=pose_landmark_enum,
            image_width=image_width,
            image_height=image_height
        )

        if foot_data is None:
            return self.set_phase("Not Detected")

        foot_y = foot_data["foot_y"]

        self.update_ground_level(foot_y)

        if self.ground_y is None:
            return self.set_phase("Not Detected")

        ground_threshold = max(18, int(image_height * 0.035))

        is_contact = abs(self.ground_y - foot_y) <= ground_threshold

        vertical_velocity = None

        if self.previous_foot_y is not None:
            vertical_velocity = foot_y - self.previous_foot_y

        event_phase = None

        if self.previous_contact is not None:
            if is_contact and not self.previous_contact:
                event_phase = "Initial Contact"
                self.phase_hold_count = 4

            elif self.previous_contact and not is_contact:
                event_phase = "Toe-Off"
                self.phase_hold_count = 4

            elif is_contact and vertical_velocity is not None and vertical_velocity < -6:
                event_phase = "Toe-Off"
                self.phase_hold_count = 3

        if event_phase is not None:
            phase = event_phase

        elif self.phase_hold_count > 0:
            phase = self.phase
            self.phase_hold_count -= 1

        elif is_contact:
            phase = "Support Phase"

        else:
            phase = "Flight / Swing"

        self.previous_contact = is_contact
        self.previous_foot_y = foot_y

        return self.set_phase(phase)

    def get_lowest_visible_foot(
        self,
        landmarks,
        pose_landmark_enum,
        image_width,
        image_height,
        min_visibility=0.45
    ):
        LM = pose_landmark_enum

        foot_landmark_groups = [
            [
                LM.LEFT_ANKLE.value,
                LM.LEFT_HEEL.value,
                LM.LEFT_FOOT_INDEX.value
            ],
            [
                LM.RIGHT_ANKLE.value,
                LM.RIGHT_HEEL.value,
                LM.RIGHT_FOOT_INDEX.value
            ]
        ]

        candidate_feet = []

        for group in foot_landmark_groups:
            y_values = []

            for landmark_id in group:
                lm = landmarks[landmark_id]

                if hasattr(lm, "visibility") and lm.visibility < min_visibility:
                    continue

                y = int(lm.y * image_height)
                y_values.append(y)

            if y_values:
                candidate_feet.append(max(y_values))

        if not candidate_feet:
            return None

        lowest_foot_y = max(candidate_feet)

        return {
            "foot_y": lowest_foot_y
        }

    def update_ground_level(self, foot_y):
        """
        Estimate ground level from the lowest visible foot point.
        """

        if self.ground_y is None:
            self.ground_y = foot_y
            return

        if self.frame_count <= 60:
            self.ground_y = max(self.ground_y, foot_y)
            return

        if foot_y > self.ground_y:
            self.ground_y = int(0.9 * self.ground_y + 0.1 * foot_y)

    def set_phase(self, phase):
        self.phase = phase
        return self.phase