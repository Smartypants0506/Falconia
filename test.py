from flask import Flask, render_template_string
import cv2
import numpy as np
import threading

app = Flask(__name__)

# Global variables to store the coordinates
x_coord = 0
y_coord = 0

# Function to process the video stream and detect the brightest pixel
def process_video_stream():
    global x_coord, y_coord

    # Initialize video capture (replace 0 with your video source if needed)
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Find the brightest pixel
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(gray)
        x_coord, y_coord = max_loc  # Coordinates of the brightest pixel

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

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
                // Refresh the page every second to update the coordinates
                setTimeout(function() {
                    window.location.reload();
                }, 1000);
            </script>
        </body>
        </html>
    ''', x=x_coord, y=y_coord)

# Run the Flask server
def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    # Start the video processing in a separate thread
    video_thread = threading.Thread(target=process_video_stream)
    video_thread.daemon = True
    video_thread.start()

    # Start the Flask server
    run_flask()