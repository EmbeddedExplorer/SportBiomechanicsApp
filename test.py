'''import pyrealsense2 as rs

ctx = rs.context()
devices = ctx.query_devices()

print("Number of RealSense devices:", len(devices))

for dev in devices:
    print("Name:", dev.get_info(rs.camera_info.name))
    print("Serial:", dev.get_info(rs.camera_info.serial_number))
    print("Firmware:", dev.get_info(rs.camera_info.firmware_version))
    print("USB:", dev.get_info(rs.camera_info.usb_type_descriptor))

import cv2
import numpy as np

pipeline = rs.pipeline()
config = rs.config()

config.enable_stream(
    rs.stream.color,
    640,
    480,
    rs.format.bgr8,
    30
)

pipeline.start(config)

try:
    while True:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()

        if not color_frame:
            continue

        image = np.asanyarray(color_frame.get_data())

        cv2.imshow("RGB", image)

        if cv2.waitKey(1) == 27:
            break

finally:
    pipeline.stop()
    cv2.destroyAllWindows()'''

import mediapipe as mp

print(mp)
print(mp.__file__)
print(dir(mp))