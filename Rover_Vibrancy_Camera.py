import cv2
import numpy as np
import matplotlib.pyplot as plt

STREAM_URL = "udp://0.0.0.0:12345"

def get_inverted_vibrancy_matrix(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1].astype(float) / 255.0
    value = hsv[:, :, 2].astype(float) / 255.0
    vibrancy = saturation * value
    inverted_vibrancy = 1.0 - vibrancy  # Invert vibrancy
    return inverted_vibrancy

def show_image(img, title="Image"):
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title(title)
    plt.axis("off")
    plt.show()

def capture_stream():
    cap = cv2.VideoCapture(STREAM_URL)  # Read from UDP stream

    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        inverted_vibrancy_matrix = get_inverted_vibrancy_matrix(frame)
        vibrancy_display = (inverted_vibrancy_matrix * 255).astype(np.uint8)
        vibrancy_colored = cv2.applyColorMap(vibrancy_display, cv2.COLORMAP_JET)

        cv2.imshow("Original Frame", frame)
        cv2.imshow("Inverted Vibrancy Map", vibrancy_colored)

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_stream()

