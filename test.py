from flask import Flask, Response, render_template_string, jsonify
import cv2
import numpy as np

app = Flask(__name__)

# Global variable to store the light position
LIGHT_POSITION = (0, 0)


def generate_frames():
    """Generator function that processes video frames and yields them for streaming"""
    global LIGHT_POSITION

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        yield b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + b'Camera Error' + b'\r\n'
        return

    try:
        while True:
            # Read a frame from the camera
            ret, frame = cap.read()
            if not ret:
                break

            # Process the frame to find bright spots
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Find the largest contour (brightest area)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)

                # Draw rectangle and center point
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                center_x, center_y = x + w // 2, y + h // 2
                cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)

                # Update the global position
                LIGHT_POSITION = (center_x, center_y)
                print(f"Light position: {LIGHT_POSITION}")

            # Convert the frame to JPEG format for streaming
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            # Yield the frame in the format expected by Flask's Response
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    finally:
        # Make sure we release the camera
        cap.release()


@app.route('/')
def index():
    """Main page with video feed and coordinates"""
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Light Position Tracker</title>
            <style>
                body { font-family: Arial; margin: 20px; text-align: center; }
                #coords { font-size: 24px; margin: 20px 0; }
                #video { margin-top: 20px; border: 1px solid #ccc; }
            </style>
        </head>
        <body>
            <h1>Light Position Tracker</h1>
            <div id="coords">Position: waiting for data...</div>
            <div><img id="video" src="{{ url_for('video_feed') }}"></div>

            <script>
                // Update the coordinates every 500ms
                setInterval(function() {
                    fetch('/light_position')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('coords').textContent = 
                                'Position: ' + data.x + ', ' + data.y;
                        });
                }, 500);
            </script>
        </body>
        </html>
    ''')


@app.route('/video_feed')
def video_feed():
    """Route for the video feed"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/light_position')
def light_position():
    """Route for getting the current light position"""
    global LIGHT_POSITION
    return jsonify({
        "x": LIGHT_POSITION[0],
        "y": LIGHT_POSITION[1]
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)