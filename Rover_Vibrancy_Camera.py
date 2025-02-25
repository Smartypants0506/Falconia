import cv2
import numpy as np
import socket
import struct
import datetime

# UDP Stream Configuration
UDP_IP = "0.0.0.0"  # Listen on all interfaces
UDP_PORT = 5000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# Frame specifications (match sender settings)
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
CHANNELS = 3  # Assuming an RGB stream
FRAME_SIZE = FRAME_WIDTH * FRAME_HEIGHT * CHANNELS

# Buffer to store frame data
buffer = bytearray()


def extract_vibrant_regions(frame):
    """Extracts and highlights the most vibrant regions in the frame."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s_channel = hsv[:, :, 1]
    _, mask = cv2.threshold(s_channel, 150, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    output = frame.copy()
    cv2.drawContours(output, contours, -1, (0, 255, 0), 2)
    return output


def add_timestamp(frame):
    """Adds a timestamp to the top-right corner of the frame."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, timestamp, (FRAME_WIDTH - 220, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)
    return frame


while True:
    try:
        data, _ = sock.recvfrom(4096)  # Receive a packet (UDP max size is 65507, but typical is <4096)
        buffer.extend(data)  # Append incoming data to buffer

        # Process frame when buffer contains enough data
        if len(buffer) >= FRAME_SIZE:
            frame_data = buffer[:FRAME_SIZE]  # Extract a full frame
            buffer = buffer[FRAME_SIZE:]  # Remove processed data from buffer

            # Convert to NumPy array and reshape
            frame = np.frombuffer(frame_data, dtype=np.uint8).reshape((FRAME_HEIGHT, FRAME_WIDTH, CHANNELS))

            # Process frame
            processed_frame = extract_vibrant_regions(frame)
            processed_frame = add_timestamp(processed_frame)

            # Display
            cv2.imshow("Vibrant Object Detection", processed_frame)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    except Exception as e:
        print(f"Error: {e}")

# Cleanup
sock.close()
cv2.destroyAllWindows()
