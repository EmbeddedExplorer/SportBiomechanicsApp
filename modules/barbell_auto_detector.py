import cv2
import numpy as np


class BarbellAutoDetector:
    """
    Automatic barbell disk detector for side-view weightlifting.

    Detection logic:
    - Detect circular / plate-like candidates.
    - Prefer candidates near the athlete lower body / foot region.
    - Avoid selecting background plates far from the athlete.
    - Used only for side-view.
    """

    def __init__(self):
        self.last_bbox = None
        self.detection_count = 0

    def reset(self):
        self.last_bbox = None
        self.detection_count = 0

    def detect(
        self,
        frame,
        landmarks=None,
        pose_landmark_enum=None,
        min_visibility=0.45
    ):
        if frame is None:
            return None

        h, w = frame.shape[:2]

        pose_ref = self.extract_pose_reference(
            landmarks=landmarks,
            pose_landmark_enum=pose_landmark_enum,
            image_width=w,
            image_height=h,
            min_visibility=min_visibility
        )

        candidates = []

        candidates.extend(self.detect_by_contours(frame))
        candidates.extend(self.detect_by_hough(frame))

        candidates = self.merge_similar_candidates(candidates)

        if not candidates:
            return None

        best_candidate = None
        best_score = float("inf")

        for bbox in candidates:
            score = self.score_candidate(
                bbox=bbox,
                frame_width=w,
                frame_height=h,
                pose_ref=pose_ref
            )

            if score < best_score:
                best_score = score
                best_candidate = bbox

        if best_candidate is None:
            return None

        # Reject weak candidates.
        if best_score > 1000:
            return None

        self.last_bbox = best_candidate
        self.detection_count += 1

        return best_candidate

    def detect_by_contours(self, frame):
        h, w = frame.shape[:2]

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        masks = []

        # Green plates
        masks.append(cv2.inRange(
            hsv,
            np.array([35, 35, 35]),
            np.array([95, 255, 255])
        ))

        # Blue plates / bluish plates
        masks.append(cv2.inRange(
            hsv,
            np.array([90, 35, 35]),
            np.array([130, 255, 255])
        ))

        # Red plates
        mask_red1 = cv2.inRange(
            hsv,
            np.array([0, 40, 40]),
            np.array([10, 255, 255])
        )

        mask_red2 = cv2.inRange(
            hsv,
            np.array([170, 40, 40]),
            np.array([180, 255, 255])
        )

        masks.append(cv2.bitwise_or(mask_red1, mask_red2))

        # Dark plates / black plates
        masks.append(cv2.inRange(
            hsv,
            np.array([0, 0, 0]),
            np.array([180, 90, 90])
        ))

        combined = np.zeros((h, w), dtype=np.uint8)

        for mask in masks:
            combined = cv2.bitwise_or(combined, mask)

        kernel = np.ones((5, 5), np.uint8)

        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(
            combined,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        candidates = []

        min_area = max(250, int(w * h * 0.0008))
        max_area = int(w * h * 0.08)

        for contour in contours:
            area = cv2.contourArea(contour)

            if area < min_area or area > max_area:
                continue

            perimeter = cv2.arcLength(contour, True)

            if perimeter <= 0:
                continue

            circularity = 4 * np.pi * area / (perimeter * perimeter)

            if circularity < 0.35:
                continue

            x, y, bw, bh = cv2.boundingRect(contour)

            aspect = bw / float(bh + 1e-6)

            if aspect < 0.45 or aspect > 2.2:
                continue

            if bw < 15 or bh < 15:
                continue

            candidates.append((x, y, bw, bh))

        return candidates

    def detect_by_hough(self, frame):
        h, w = frame.shape[:2]

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (9, 9), 2)

        min_radius = max(10, int(min(w, h) * 0.025))
        max_radius = max(30, int(min(w, h) * 0.18))

        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=35,
            param1=80,
            param2=25,
            minRadius=min_radius,
            maxRadius=max_radius
        )

        candidates = []

        if circles is None:
            return candidates

        circles = np.round(circles[0, :]).astype("int")

        for cx, cy, r in circles:
            x = int(cx - r)
            y = int(cy - r)
            bw = int(2 * r)
            bh = int(2 * r)

            if x < 0 or y < 0:
                continue

            if x + bw >= w or y + bh >= h:
                continue

            candidates.append((x, y, bw, bh))

        return candidates

    def merge_similar_candidates(self, candidates):
        if not candidates:
            return []

        merged = []

        for bbox in candidates:
            x, y, w, h = bbox
            cx = x + w / 2
            cy = y + h / 2

            duplicate = False

            for existing in merged:
                ex, ey, ew, eh = existing
                ecx = ex + ew / 2
                ecy = ey + eh / 2

                distance = ((cx - ecx) ** 2 + (cy - ecy) ** 2) ** 0.5

                if distance < max(w, h, ew, eh) * 0.4:
                    duplicate = True
                    break

            if not duplicate:
                merged.append(bbox)

        return merged

    def score_candidate(
        self,
        bbox,
        frame_width,
        frame_height,
        pose_ref=None
    ):
        x, y, w, h = bbox

        cx = x + w / 2
        cy = y + h / 2

        score = 0.0

        # Prefer lower half of image for setup barbell.
        lower_half_bonus = 0 if cy > frame_height * 0.45 else 250
        score += lower_half_bonus

        # Penalize extremely large or small boxes.
        area = w * h
        ideal_area = frame_width * frame_height * 0.015
        score += abs(area - ideal_area) / max(1, ideal_area) * 80

        # Prefer circular / square-ish candidate.
        aspect = w / float(h + 1e-6)
        score += abs(aspect - 1.0) * 80

        if pose_ref is not None:
            athlete_center_x = pose_ref.get("athlete_center_x")
            foot_y = pose_ref.get("foot_y")
            left_x = pose_ref.get("athlete_left_x")
            right_x = pose_ref.get("athlete_right_x")

            if athlete_center_x is not None:
                score += abs(cx - athlete_center_x) * 0.8

            if foot_y is not None:
                score += abs(cy - foot_y) * 0.7

            if left_x is not None and right_x is not None:
                margin = frame_width * 0.25

                if cx < left_x - margin or cx > right_x + margin:
                    score += 350

        else:
            # Without pose landmarks, prefer lower central candidates.
            score += abs(cx - frame_width / 2) * 0.4
            score += abs(cy - frame_height * 0.75) * 0.7

        return score

    def extract_pose_reference(
        self,
        landmarks,
        pose_landmark_enum,
        image_width,
        image_height,
        min_visibility=0.45
    ):
        if landmarks is None or pose_landmark_enum is None:
            return None

        LM = pose_landmark_enum

        body_ids = [
            LM.LEFT_SHOULDER.value,
            LM.RIGHT_SHOULDER.value,
            LM.LEFT_HIP.value,
            LM.RIGHT_HIP.value,
            LM.LEFT_KNEE.value,
            LM.RIGHT_KNEE.value,
            LM.LEFT_ANKLE.value,
            LM.RIGHT_ANKLE.value
        ]

        foot_ids = [
            LM.LEFT_ANKLE.value,
            LM.RIGHT_ANKLE.value,
            LM.LEFT_HEEL.value,
            LM.RIGHT_HEEL.value,
            LM.LEFT_FOOT_INDEX.value,
            LM.RIGHT_FOOT_INDEX.value
        ]

        xs = []
        foot_ys = []

        for idx in body_ids:
            lm = landmarks[idx]

            if hasattr(lm, "visibility") and lm.visibility < min_visibility:
                continue

            xs.append(float(lm.x * image_width))

        for idx in foot_ids:
            lm = landmarks[idx]

            if hasattr(lm, "visibility") and lm.visibility < min_visibility:
                continue

            foot_ys.append(float(lm.y * image_height))

        if not xs:
            return None

        athlete_left_x = min(xs)
        athlete_right_x = max(xs)
        athlete_center_x = sum(xs) / len(xs)

        foot_y = max(foot_ys) if foot_ys else None

        return {
            "athlete_left_x": athlete_left_x,
            "athlete_right_x": athlete_right_x,
            "athlete_center_x": athlete_center_x,
            "foot_y": foot_y
        }