import cv2
import numpy as np
from flask import Flask, Response, render_template, jsonify, render_template_string

app = Flask(__name__)

# Initialize with default values
LIGHT_POSITION = (0, 0)


def generate_frames():
    global LIGHT_POSITION  # Move this up here to ensure proper scope
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

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
            center_x, center_y = x + w // 2, y + h // 2
            cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)

            # Update position - place outside the yield
            LIGHT_POSITION = (center_x, center_y)
            print(f"Light position updated: {LIGHT_POSITION}")

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Brightest Pixel Coordinates</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
                .coordinates { font-size: 24px; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>Light Tracking</h1>
            <div class="coordinates">Position: <span id="coords">{{ x }}, {{ y }}</span></div>

            <script>
                function updateCoordinates() {
                    fetch('/light_position')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('coords').textContent = data.x + ', ' + data.y;
                        });
                }

                // Update coordinates every second instead of page reload
                setInterval(updateCoordinates, 500);
            </script>
        </body>
        </html>
    ''', x=LIGHT_POSITION[0], y=LIGHT_POSITION[1])


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/light_position')
def light_position():
    global LIGHT_POSITION
    return jsonify({
        "position": f"({LIGHT_POSITION[0]}, {LIGHT_POSITION[1]})",
        "x": LIGHT_POSITION[0],
        "y": LIGHT_POSITION[1]
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)