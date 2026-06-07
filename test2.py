import cv2
import numpy as np
import pyrealsense2 as rs
import mediapipe as mp


def main():
    pipeline = rs.pipeline()
    config = rs.config()

    config.enable_stream(
        rs.stream.color,
        640,
        480,
        rs.format.bgr8,
        30
    )

    config.enable_stream(
        rs.stream.depth,
        640,
        480,
        rs.format.z16,
        30
    )

    pipeline.start(config)

    align = rs.align(rs.stream.color)

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    print("RealSense + MediaPipe Pose test started.")
    print("Press ESC to exit.")

    try:
        while True:
            try:
                frames = pipeline.wait_for_frames(timeout_ms=5000)
            except RuntimeError:
                print("Frame timeout...")
                continue

            aligned_frames = align.process(frames)

            color_frame = aligned_frames.get_color_frame()
            depth_frame = aligned_frames.get_depth_frame()

            if not color_frame or not depth_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())

            rgb_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_image)

            h, w, _ = color_image.shape

            center_x = w // 2
            center_y = h // 2

            center_depth = depth_frame.get_distance(center_x, center_y)

            athlete_depth = None

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    color_image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )

                landmarks = results.pose_landmarks.landmark

                torso_ids = [
                    mp_pose.PoseLandmark.LEFT_SHOULDER.value,
                    mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
                    mp_pose.PoseLandmark.LEFT_HIP.value,
                    mp_pose.PoseLandmark.RIGHT_HIP.value
                ]

                xs = []
                ys = []

                for idx in torso_ids:
                    lm = landmarks[idx]

                    if lm.visibility > 0.5:
                        xs.append(int(lm.x * w))
                        ys.append(int(lm.y * h))

                if xs and ys:
                    athlete_x = int(sum(xs) / len(xs))
                    athlete_y = int(sum(ys) / len(ys))

                    athlete_depth = depth_frame.get_distance(
                        athlete_x,
                        athlete_y
                    )

                    cv2.circle(
                        color_image,
                        (athlete_x, athlete_y),
                        8,
                        (0, 165, 255),
                        -1
                    )

                    cv2.putText(
                        color_image,
                        "Athlete Center",
                        (athlete_x + 10, athlete_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 165, 255),
                        2
                    )

            cv2.circle(
                color_image,
                (center_x, center_y),
                8,
                (0, 255, 255),
                -1
            )

            cv2.putText(
                color_image,
                f"Center Depth: {center_depth:.2f} m",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            if athlete_depth is not None and athlete_depth > 0:
                cv2.putText(
                    color_image,
                    f"Athlete Depth: {athlete_depth:.2f} m",
                    (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 165, 255),
                    2
                )

            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.08),
                cv2.COLORMAP_JET
            )

            combined = np.hstack(
                (color_image, depth_colormap)
            )

            cv2.imshow(
                "D435 RGB + Depth + MediaPipe Pose",
                combined
            )

            key = cv2.waitKey(1)

            if key == 27:
                break

            
    finally:
        pose.close()
        pipeline.stop()
        cv2.destroyAllWindows()
        print("Test stopped.")


if __name__ == "__main__":
    main()