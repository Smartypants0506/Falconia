from flask import Flask, render_template_string
import cv2
import numpy as np
import threading
import time

app = Flask(__name__)

# Global variables to store the coordinates
x_coord = 0
y_coord = 0

# Function to process the video stream and detect the brightest pixel
def process_video_stream():
    global x_coord, y_coord

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640 * 2)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480 * 2)
    failure_count = 0  # Counter for consecutive frame failures
    max_failures = 10  # Max consecutive failures before exiting

    while True:
        ret, frame = cap.read()
        if not ret:
            failure_count += 1
            print(f"Warning: Unable to read frame ({failure_count}/{max_failures})")
            if failure_count >= max_failures:
                print("Error: Maximum frame read failures reached. Exiting video thread.")
                break
            time.sleep(0.1)  # Short delay before retrying
            continue
        failure_count = 0  # Reset failure count after a successful read

        # Convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Find the brightest pixel
        _, _, _, max_loc = cv2.minMaxLoc(gray)
        x_coord, y_coord = max_loc  # Coordinates of the brightest pixel

    cap.release()
    cv2.destroyAllWindows()

# Flask route to serve the web page
@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Brightest Pixel Coordinates</title>
        </head>
        <body>
            <p>{{ x }}, {{ y }}</p>
            <script>
                setTimeout(function() {
                    window.location.reload();
                }, 3000);
            </script>
        </body>
        </html>
    ''', x=x_coord, y=y_coord)

# Run the Flask server
def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    video_thread = threading.Thread(target=process_video_stream, daemon=True)
    video_thread.start()
    run_flask()
