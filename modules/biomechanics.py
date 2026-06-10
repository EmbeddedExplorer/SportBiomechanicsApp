import math


def calculate_angle(point_a, point_b, point_c):
    """
    Calculate the angle at point_b formed by points A-B-C.
    Returns angle in degrees.
    """

    if point_a is None or point_b is None or point_c is None:
        return None

    ax, ay = point_a
    bx, by = point_b
    cx, cy = point_c

    vector_ba = (ax - bx, ay - by)
    vector_bc = (cx - bx, cy - by)

    dot_product = (
        vector_ba[0] * vector_bc[0] +
        vector_ba[1] * vector_bc[1]
    )

    magnitude_ba = math.sqrt(vector_ba[0] ** 2 + vector_ba[1] ** 2)
    magnitude_bc = math.sqrt(vector_bc[0] ** 2 + vector_bc[1] ** 2)

    if magnitude_ba == 0 or magnitude_bc == 0:
        return None

    cos_angle = dot_product / (magnitude_ba * magnitude_bc)
    cos_angle = max(-1.0, min(1.0, cos_angle))

    angle_rad = math.acos(cos_angle)
    angle_deg = math.degrees(angle_rad)

    return round(angle_deg, 2)


def get_landmark_point(landmarks, landmark_id, image_width, image_height, min_visibility=0.5):
    """
    Convert normalized MediaPipe landmark into image pixel coordinate.
    """

    landmark = landmarks[landmark_id]

    if hasattr(landmark, "visibility"):
        if landmark.visibility < min_visibility:
            return None

    x = int(landmark.x * image_width)
    y = int(landmark.y * image_height)

    return x, y


def average_points(points):
    """
    Average valid points.
    """

    valid_points = [p for p in points if p is not None]

    if not valid_points:
        return None

    x = sum(p[0] for p in valid_points) / len(valid_points)
    y = sum(p[1] for p in valid_points) / len(valid_points)

    return x, y


def calculate_trunk_lean(mid_shoulder, mid_hip):
    """
    Calculate trunk lean angle relative to vertical direction.
    0 degrees means upright vertical posture.
    """

    if mid_shoulder is None or mid_hip is None:
        return None

    sx, sy = mid_shoulder
    hx, hy = mid_hip

    trunk_vector = (sx - hx, sy - hy)
    vertical_vector = (0, -1)

    trunk_mag = math.sqrt(trunk_vector[0] ** 2 + trunk_vector[1] ** 2)

    if trunk_mag == 0:
        return None

    dot_product = (
        trunk_vector[0] * vertical_vector[0] +
        trunk_vector[1] * vertical_vector[1]
    )

    cos_angle = dot_product / trunk_mag
    cos_angle = max(-1.0, min(1.0, cos_angle))

    angle = math.degrees(math.acos(cos_angle))

    return round(angle, 2)


def compute_pose_metrics(
    landmarks,
    pose_landmark_enum,
    image_width,
    image_height,
    athlete_depth=None,
    center_depth=None
):
    """
    Compute main biomechanics angles from MediaPipe landmarks.
    """

    LM = pose_landmark_enum

    # Left side landmarks
    left_shoulder = get_landmark_point(
        landmarks, LM.LEFT_SHOULDER.value, image_width, image_height
    )
    left_elbow = get_landmark_point(
        landmarks, LM.LEFT_ELBOW.value, image_width, image_height
    )
    left_wrist = get_landmark_point(
        landmarks, LM.LEFT_WRIST.value, image_width, image_height
    )
    left_hip = get_landmark_point(
        landmarks, LM.LEFT_HIP.value, image_width, image_height
    )
    left_knee = get_landmark_point(
        landmarks, LM.LEFT_KNEE.value, image_width, image_height
    )
    left_ankle = get_landmark_point(
        landmarks, LM.LEFT_ANKLE.value, image_width, image_height
    )
    left_foot = get_landmark_point(
        landmarks, LM.LEFT_FOOT_INDEX.value, image_width, image_height
    )

    # Right side landmarks
    right_shoulder = get_landmark_point(
        landmarks, LM.RIGHT_SHOULDER.value, image_width, image_height
    )
    right_elbow = get_landmark_point(
        landmarks, LM.RIGHT_ELBOW.value, image_width, image_height
    )
    right_wrist = get_landmark_point(
        landmarks, LM.RIGHT_WRIST.value, image_width, image_height
    )
    right_hip = get_landmark_point(
        landmarks, LM.RIGHT_HIP.value, image_width, image_height
    )
    right_knee = get_landmark_point(
        landmarks, LM.RIGHT_KNEE.value, image_width, image_height
    )
    right_ankle = get_landmark_point(
        landmarks, LM.RIGHT_ANKLE.value, image_width, image_height
    )
    right_foot = get_landmark_point(
        landmarks, LM.RIGHT_FOOT_INDEX.value, image_width, image_height
    )

    mid_shoulder = average_points([left_shoulder, right_shoulder])
    mid_hip = average_points([left_hip, right_hip])

    metrics = {
        "Pose": "Detected",

        "Left Hip Angle": calculate_angle(left_shoulder, left_hip, left_knee),
        "Right Hip Angle": calculate_angle(right_shoulder, right_hip, right_knee),

        "Left Knee Angle": calculate_angle(left_hip, left_knee, left_ankle),
        "Right Knee Angle": calculate_angle(right_hip, right_knee, right_ankle),

        "Left Ankle Angle": calculate_angle(left_knee, left_ankle, left_foot),
        "Right Ankle Angle": calculate_angle(right_knee, right_ankle, right_foot),

        "Left Shoulder Angle": calculate_angle(left_elbow, left_shoulder, left_hip),
        "Right Shoulder Angle": calculate_angle(right_elbow, right_shoulder, right_hip),

        "Left Elbow Angle": calculate_angle(left_shoulder, left_elbow, left_wrist),
        "Right Elbow Angle": calculate_angle(right_shoulder, right_elbow, right_wrist),

        "Trunk Lean Angle": calculate_trunk_lean(mid_shoulder, mid_hip),

        "Athlete Depth (m)": athlete_depth,
        "Center Depth (m)": center_depth
    }

    return metrics