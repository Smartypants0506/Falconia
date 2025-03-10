import cv2
import numpy as np
from flask import Flask, Response, render_template, jsonify

app = Flask(__name__)

LIGHT_POSITION = None  # Stores the detected bright spot coordinates

def find_brightest_spot(frame):
    """Detects the brightest spot in the frame and updates LIGHT_POSITION."""
    global LIGHT_POSITION

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (15, 15), 0)

    # Find the brightest spot
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(blurred)
    LIGHT_POSITION = maxLoc  # Store coordinates of the brightest spot

    print(f"✅ Brightest Spot Found at: {LIGHT_POSITION}")  # Debugging output


def generate_frames():
    """Captures camera frames, finds the brightest spot, and streams video."""
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # Try CAP_MSMF if needed

    # Ensure camera opens successfully
    if not cap.isOpened():
        print("❌ Error: Could not open camera.")
        return

    # Reduce camera exposure to improve bright spot detection
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Turn off auto exposure
        cap.set(cv2.CAP_PROP_EXPOSURE, -6)  # Adjust exposure manually

    print("✅ Camera opened in Flask app.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error: Could not read frame.")
                break  # Exit loop if no frame

            # Find the brightest spot in the frame
            find_brightest_spot(frame)

            # Encode frame for streaming
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    finally:
        cap.release()
        print("✅ Camera released in Flask app.")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/light_position')
def light_position():
    """Returns the last detected bright spot position."""
    global LIGHT_POSITION
    if LIGHT_POSITION is None:
        return jsonify({"error": "No light detected yet"}), 400
    return jsonify({"position": LIGHT_POSITION})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)