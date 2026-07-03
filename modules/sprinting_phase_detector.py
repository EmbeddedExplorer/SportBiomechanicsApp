class SprintingPhaseDetector:
    """
    Side-view sprinting phase detector.

    Final phases:
        Initial Contact
        Support Phase
        Toe-Off
        Flight / Swing

    The detector estimates ground contact using the lowest visible foot point
    from ankle, heel, and foot index landmarks.

    Design goal:
        - Keep phase labels stable.
        - Avoid rapid flickering between contact and flight.
        - Work with normal side-view sprinting videos.
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

        self.contact_frame_count = 0
        self.flight_frame_count = 0

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
            self.previous_foot_y = foot_y
            return self.set_phase("Not Detected")

        contact_threshold = max(18, int(image_height * 0.035))
        release_threshold = max(26, int(image_height * 0.050))

        distance_from_ground = abs(self.ground_y - foot_y)

        # Hysteresis:
        # If previous frame was contact, use a slightly larger release threshold.
        # This prevents rapid flickering caused by landmark jitter.
        if self.previous_contact is True:
            is_contact = distance_from_ground <= release_threshold
        else:
            is_contact = distance_from_ground <= contact_threshold

        vertical_velocity = None

        if self.previous_foot_y is not None:
            vertical_velocity = foot_y - self.previous_foot_y

        if is_contact:
            self.contact_frame_count += 1
            self.flight_frame_count = 0
        else:
            self.flight_frame_count += 1
            self.contact_frame_count = 0

        event_phase = None

        if self.previous_contact is not None:
            # Flight to contact
            if is_contact and not self.previous_contact:
                event_phase = "Initial Contact"
                self.phase_hold_count = 4

            # Contact to flight
            elif self.previous_contact and not is_contact:
                event_phase = "Toe-Off"
                self.phase_hold_count = 4

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
                if landmark_id >= len(landmarks):
                    continue

                lm = landmarks[landmark_id]

                if hasattr(lm, "visibility") and lm.visibility < min_visibility:
                    continue

                if lm.y is None:
                    continue

                y = int(lm.y * image_height)

                if y < 0 or y > image_height * 1.2:
                    continue

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

        In image coordinates:
            Larger y value = lower position in the image.
        """

        if self.ground_y is None:
            self.ground_y = foot_y
            return

        # During early frames, collect the lowest visible foot point.
        if self.frame_count <= 90:
            self.ground_y = max(self.ground_y, foot_y)
            return

        # Later, allow slow adaptation if a lower ground point appears.
        if foot_y > self.ground_y:
            self.ground_y = int(0.92 * self.ground_y + 0.08 * foot_y)

    def set_phase(self, phase):
        self.phase = phase
        return self.phase