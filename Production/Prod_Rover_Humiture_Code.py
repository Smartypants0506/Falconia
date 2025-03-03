import adafruit_dht
import board
import time
from datetime import datetime
import cv2

# Initialize the DHT11 sensor
sensor = adafruit_dht.DHT11(board.D26)
log_file = "sensor_log.txt"

# Initialize video capture
video_capture = cv2.VideoCapture(0)  # 0 is the default camera
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for MP4
video_out = cv2.VideoWriter('output.mp4', fourcc, 15.0, (320, 240))  # Adjust resolution and frame rate as needed

# Font settings for timestamp
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.7
font_color = (255, 255, 255)  # White color
font_thickness = 2

while True:
    try:
        # Capture sensor data
        temperature = sensor.temperature
        humidity = sensor.humidity
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Temperature: {temperature}°C  Humidity: {humidity}\n"

        # Log sensor data
        with open(log_file, "a") as file:
            file.write(log_entry)

        # Capture video frame
        ret, frame = video_capture.read()
        if ret:
            # Overlay timestamp on the frame
            cv2.putText(frame, timestamp, (10, 30), font, font_scale, font_color, font_thickness)

            # Write the frame to the video file
            video_out.write(frame)

    except RuntimeError as e:
        # Log sensor error
        with open(log_file, "a") as file:
            file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Sensor error: {e}\n")

    time.sleep(0.1)

# Release resources
video_capture.release()
video_out.release()
cv2.destroyAllWindows()