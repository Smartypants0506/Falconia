import cv2
import numpy as np
from flask import Flask, Response, render_template, jsonify

app = Flask(__name__)

LIGHT_POSITION = None

def generate_frames():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        light_position = None
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            light_position = (x + w // 2, y + h // 2)
            cv2.circle(frame, light_position, 5, (0, 255, 0), -1)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        if light_position:
            # print(f"Light position: {light_position}")

            global LIGHT_POSITION
            LIGHT_POSITION = light_position

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/light_position')
def light_position():
    # This is a placeholder; you'll need to modify generate_frames() or
    # the tracking logic to store and return the last detected light position.
    # return jsonify({"position": "(x, y)"})
    return jsonify({"position": LIGHT_POSITION})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)