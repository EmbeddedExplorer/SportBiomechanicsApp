import cv2
import numpy as np


def select_roi_from_frame(frame, window_title="Select Barbell ROI"):
    """
    Opens an OpenCV ROI selector before the preview thread starts.
    This avoids opening cv2.selectROI inside a PyQt QThread.

    Returns:
        (x, y, w, h) or None
    """

    if frame is None:
        return None

    display = frame.copy()

    cv2.putText(
        display,
        "Select barbell plate/weight ROI, then press ENTER or SPACE",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 255),
        2
    )

    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_title, 900, 650)

    roi = cv2.selectROI(
        window_title,
        display,
        fromCenter=False,
        showCrosshair=True
    )

    cv2.destroyWindow(window_title)
    cv2.waitKey(1)

    x, y, w, h = roi

    if w <= 5 or h <= 5:
        return None

    return int(x), int(y), int(w), int(h)


def get_first_frame_from_bag(file_path):
    """
    Extract first usable color frame from a RealSense .bag file.
    Used only for manual ROI selection before preview starts.
    """

    pipeline = None
    started = False

    try:
        import pyrealsense2 as rs

        pipeline = rs.pipeline()
        config = rs.config()

        rs.config.enable_device_from_file(
            config,
            file_path,
            repeat_playback=False
        )

        config.enable_all_streams()

        profile = pipeline.start(config)
        started = True

        try:
            playback = profile.get_device().as_playback()
            playback.set_real_time(False)
        except Exception:
            pass

        align = rs.align(rs.stream.color)

        frame = None

        for _ in range(80):
            try:
                frames = pipeline.wait_for_frames(timeout_ms=1000)
            except Exception:
                break

            try:
                frames = align.process(frames)
            except Exception:
                pass

            color_frame = frames.get_color_frame()

            if color_frame:
                frame = np.asanyarray(color_frame.get_data())

                # Some .bag color streams come as RGB.
                try:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                except Exception:
                    pass

                break

        return frame

    except Exception as e:
        print(f"Could not extract first frame from .bag: {e}")
        return None

    finally:
        if pipeline is not None and started:
            try:
                pipeline.stop()
            except Exception:
                pass

        try:
            del pipeline
        except Exception:
            pass

        try:
            cv2.destroyAllWindows()
            cv2.waitKey(1)
        except Exception:
            pass


def get_first_frame_from_realsense_live():
    """
    Extract first frame from live RealSense camera.
    Used only for manual ROI selection before preview starts.
    """

    pipeline = None
    started = False

    try:
        import pyrealsense2 as rs

        pipeline = rs.pipeline()
        config = rs.config()

        config.enable_stream(
            rs.stream.color,
            640,
            480,
            rs.format.bgr8,
            30
        )

        profile = pipeline.start(config)
        started = True

        frame = None

        for _ in range(80):
            try:
                frames = pipeline.wait_for_frames(timeout_ms=1000)
            except Exception:
                break

            color_frame = frames.get_color_frame()

            if color_frame:
                frame = np.asanyarray(color_frame.get_data())
                break

        return frame

    except Exception as e:
        print(f"Could not extract first live RealSense frame: {e}")
        return None

    finally:
        if pipeline is not None and started:
            try:
                pipeline.stop()
            except Exception:
                pass

        try:
            del pipeline
        except Exception:
            pass

        try:
            cv2.destroyAllWindows()
            cv2.waitKey(1)
        except Exception:
            pass