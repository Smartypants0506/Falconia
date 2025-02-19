import cv2
import numpy as np
from datetime import datetime

STREAM_URL = "udp://0.0.0.0:12345"
OUTPUT_FILE = "output.mp4"
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(OUTPUT_FILE, fourcc, FPS, (FRAME_WIDTH, FRAME_HEIGHT))


def get_inverted_vibrancy_matrix(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1].astype(float) / 255.0
    value = hsv[:, :, 2].astype(float) / 255.0
    vibrancy = saturation * value
    inverted_vibrancy = 1.0 - vibrancy  # Invert vibrancy
    return inverted_vibrancy


def add_timestamp(frame):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, timestamp, (FRAME_WIDTH - 250, 30), font, 0.7, (0, 255, 0), 2)
    return frame


def capture_stream():
    cap = cv2.VideoCapture(STREAM_URL)

    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        inverted_vibrancy_matrix = get_inverted_vibrancy_matrix(frame)
        vibrancy_display = (inverted_vibrancy_matrix * 255).astype(np.uint8)
        vibrancy_colored = cv2.applyColorMap(vibrancy_display, cv2.COLORMAP_JET)

        vibrancy_colored = add_timestamp(vibrancy_colored)
        out.write(vibrancy_colored)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    capture_stream()
