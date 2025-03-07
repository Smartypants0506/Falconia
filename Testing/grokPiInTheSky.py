import cv2
import numpy as np
from flask import Flask, jsonify, request
import math

app = Flask(__name__)

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Smoothing variables for marker detection
smoothed_red = None
smoothed_blue = None
SMOOTHING_FACTOR = 0.1
DOMINANCE_THRESHOLD = 30

# Global list to store targets
targets = []

def find_most_dominant_pixel(channel, other_channels, color_name):
    """Find the most dominant pixel for a given color channel."""
    dominance = channel.astype(float) - (other_channels[0].astype(float) + other_channels[1].astype(float))
    max_dominance = np.max(dominance)
    if max_dominance < DOMINANCE_THRESHOLD:
        return None
    y, x = np.unravel_index(np.argmax(dominance), dominance.shape)
    return (x, y)

def normalize_angle(angle):
    """Normalize angle to [-180, 180] degrees."""
    return (angle + 180) % 360 - 180

@app.route('/set_targets', methods=['POST'])
def set_targets():
    """Receive and store the list of targets from the rover."""
    global targets
    data = request.json
    targets = data.get('targets', [])
    return jsonify({'status': 'success'})

@app.route('/markers', methods=['GET'])
def get_markers():
    """Process frame, detect markers, draw visuals, and return marker coordinates."""
    global smoothed_red, smoothed_blue
    target_index = request.args.get('target_index', type=int)

    ret, frame = cap.read()
    if not ret:
        return jsonify({'error': 'Failed to capture frame'}), 500

    # Convert to RGB for color detection
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    red_channel = frame_rgb[:, :, 0]
    green_channel = frame_rgb[:, :, 1]
    blue_channel = frame_rgb[:, :, 2]

    # Detect red and blue markers
    red_pixel = find_most_dominant_pixel(red_channel, (green_channel, blue_channel), "red")
    blue_pixel = find_most_dominant_pixel(blue_channel, (red_channel, green_channel), "blue")

    # Smooth marker positions
    if red_pixel:
        if smoothed_red is None:
            smoothed_red = red_pixel
        else:
            smoothed_red = (
                int(smoothed_red[0] * SMOOTHING_FACTOR + red_pixel[0] * (1 - SMOOTHING_FACTOR)),
                int(smoothed_red[1] * SMOOTHING_FACTOR + red_pixel[1] * (1 - SMOOTHING_FACTOR))
            )
    else:
        smoothed_red = None

    if blue_pixel:
        if smoothed_blue is None:
            smoothed_blue = blue_pixel
        else:
            smoothed_blue = (
                int(smoothed_blue[0] * SMOOTHING_FACTOR + blue_pixel[0] * (1 - SMOOTHING_FACTOR)),
                int(smoothed_blue[1] * SMOOTHING_FACTOR + blue_pixel[1] * (1 - SMOOTHING_FACTOR))
            )
    else:
        smoothed_blue = None

    # Draw markers if detected
    if smoothed_red:
        cv2.circle(frame, smoothed_red, 10, (0, 0, 255), 2)  # Red circle
    if smoothed_blue:
        cv2.circle(frame, smoothed_blue, 10, (255, 0, 0), 2)  # Blue circle

    # Draw orientation line, midpoint, and metrics if both markers are detected
    if smoothed_red and smoothed_blue:
        midpoint = ((smoothed_red[0] + smoothed_blue[0]) // 2, (smoothed_red[1] + smoothed_blue[1]) // 2)
        cv2.line(frame, smoothed_red, smoothed_blue, (0, 255, 0), 2)  # Green orientation line
        cv2.circle(frame, midpoint, 5, (0, 255, 255), -1)  # Yellow midpoint

        # Calculate rover orientation angle
        orientation_vector = (smoothed_blue[0] - smoothed_red[0], smoothed_blue[1] - smoothed_red[1])
        orientation_angle = math.degrees(math.atan2(orientation_vector[1], orientation_vector[0]))

        # Draw current target and metrics if valid
        if target_index is not None and 0 <= target_index < len(targets):
            target = targets[target_index]
            target_point = (target['x'], target['y'])
            target_vector = (target_point[0] - midpoint[0], target_point[1] - midpoint[1])
            target_angle = math.degrees(math.atan2(target_vector[1], target_vector[0]))
            angle_diff = normalize_angle(target_angle - orientation_angle)
            distance = math.hypot(target_vector[0], target_vector[1])

            # Draw line to current target
            cv2.line(frame, midpoint, target_point, (255, 0, 255), 2)  # Magenta line

            # Display metrics
            cv2.putText(frame, f"Distance: {distance:.2f} px", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f"Rover Angle: {orientation_angle:.2f} deg", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f"Target Angle: {target_angle:.2f} deg", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f"Angle Diff: {angle_diff:.2f} deg", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Draw all targets
    for t in targets:
        cv2.circle(frame, (t['x'], t['y']), 5, (255, 255, 0), -1)  # Cyan circles

    # Display the annotated frame
    cv2.imshow('Rover Navigation', frame)
    cv2.waitKey(1)  # Required to update the window

    # Return marker coordinates
    return jsonify({
        'red': {'x': smoothed_red[0], 'y': smoothed_red[1]} if smoothed_red else None,
        'blue': {'x': smoothed_blue[0], 'y': smoothed_blue[1]} if smoothed_blue else None
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)