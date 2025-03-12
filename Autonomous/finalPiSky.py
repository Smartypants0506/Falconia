import cv2
import numpy as np
from flask import Flask, jsonify, request, Response
import math
import time

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
DOMINANCE_THRESHOLD = 25
PIXEL_TOLERANCE = 20

# Define the array of targets in pixel coordinates as tuples
targets = [(249, 252), (267, 375), (266, 494), (322, 571), (443, 580), (573, 599), (698, 595), (803, 589), (818, 535), (818, 446), (814, 371), (775, 333), (682, 323), (573, 312), (485, 313), (414, 325), (409, 424), (457, 494)]

# Global variables to store previous angle and length
prev_angle = None
prev_length = None
ANGLE_TOLERANCE = 10  # degrees
LENGTH_TOLERANCE = 20  # pixels


def get_absolute_angle(x1, y1, x2, y2):
    """Returns the absolute angle (0 to 360 degrees) of the vector from (x1, y1) to (x2, y2)."""
    dx = x2 - x1
    dy = y2 - y1
    angle = math.atan2(dy, dx)  # Angle in radians (-π to π)
    angle_degrees = math.degrees(angle)  # Convert to degrees

    # Convert negative angles to [0, 360] range
    if angle_degrees < 0:
        angle_degrees += 360

    return angle_degrees


def get_signed_angle_difference(angle1, angle2):
    """Returns the signed difference (angle1 - angle2) in the range [-180, 180]."""
    diff = angle1 - angle2

    return diff


def find_most_dominant_pixel(channel, other_channels, color_name):
    # Calculate a dominance score: how much the target channel exceeds the sum of others
    dominance = channel.astype(float) - (other_channels[0].astype(float) + other_channels[1].astype(float))

    # Find the maximum dominance score
    max_dominance = np.max(dominance)

    # If the maximum dominance is below the threshold, return None
    if max_dominance < DOMINANCE_THRESHOLD:
        return None

    # Find the pixel with the highest dominance score
    y, x = np.unravel_index(np.argmax(dominance), dominance.shape)
    return (x, y)  # Return coordinates (x, y)

def normalize_angle(angle):
    """Normalize angle to [-180, 180] degrees."""
    return (angle + 180) % 360 - 180

def calculate_angle_between_lines(line1_start, line1_end, line2_start, line2_end):
    # Calculate vectors for the two lines
    vector1 = (line1_end[0] - line1_start[0], line1_end[1] - line1_start[1])
    vector2 = (line2_end[0] - line2_start[0], line2_end[1] - line2_start[1])

    # Calculate the dot product and magnitudes of the vectors
    dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]
    magnitude1 = math.sqrt(vector1[0] ** 2 + vector1[1] ** 2)
    magnitude2 = math.sqrt(vector2[0] ** 2 + vector2[1] ** 2)

    # Calculate the angle in radians and convert to degrees
    angle_rad = math.acos(dot_product / (magnitude1 * magnitude2))
    angle_deg = math.degrees(angle_rad)
    #print(angle_deg)

    return angle_deg

def calculate_angle_and_length(point1, point2):
    # Calculate the length of the line using Euclidean distance
    length = math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)

    # Calculate the angle in radians, then convert to degrees
    angle_rad = math.atan2(point2[1] - point1[1], point2[0] - point1[0])
    angle_deg = math.degrees(angle_rad)

    return length, angle_deg

def calculate_center(point1, point2):
    return ((point1[0] + point2[0]) // 2, (point1[1] + point2[1]) // 2)

def is_reading_valid(new_length, new_angle):
    """Check if the new reading is within tolerance of the previous reading."""
    global prev_length, prev_angle
    if prev_length is None or prev_angle is None:
        return True
    length_diff = abs(new_length - prev_length)
    angle_diff = abs(normalize_angle(new_angle - prev_angle))
    return length_diff <= LENGTH_TOLERANCE and angle_diff <= ANGLE_TOLERANCE

def process_frame():
    """Process the frame and return smoothed marker positions."""
    global smoothed_red, smoothed_blue
    ret, frame = cap.read()
    cv2.flip(frame, 1)

    # If frame is not captured, break the loop
    if not ret:
        print("Error: Failed to capture frame.")
        return None, None, None

    # Convert BGR (OpenCV default) to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Split the frame into R, G, B channels
    red_channel = frame_rgb[:, :, 0]
    green_channel = frame_rgb[:, :, 1]
    blue_channel = frame_rgb[:, :, 2]

    # Find the pixel with the most dominant red and blue values
    red_pixel = find_most_dominant_pixel(red_channel, (green_channel, blue_channel), "red")
    blue_pixel = find_most_dominant_pixel(blue_channel, (red_channel, green_channel), "blue")

    # Apply smoothing to red position if a valid red pixel is found
    if red_pixel is not None:
        if smoothed_red is None:
            smoothed_red = red_pixel
        else:
            smoothed_red = (
                int(smoothed_red[0] * SMOOTHING_FACTOR + red_pixel[0] * (1 - SMOOTHING_FACTOR)),
                int(smoothed_red[1] * SMOOTHING_FACTOR + red_pixel[1] * (1 - SMOOTHING_FACTOR))
            )
    else:
        smoothed_red = None  # Reset if no valid red pixel is found

    # Apply smoothing to blue position if a valid blue pixel is found
    if blue_pixel is not None:
        if smoothed_blue is None:
            smoothed_blue = blue_pixel
        else:
            smoothed_blue = (
                int(smoothed_blue[0] * SMOOTHING_FACTOR + blue_pixel[0] * (1 - SMOOTHING_FACTOR)),
                int(smoothed_blue[1] * SMOOTHING_FACTOR + blue_pixel[1] * (1 - SMOOTHING_FACTOR))
            )
    else:
        smoothed_blue = None

    return frame, smoothed_red, smoothed_blue

def draw_visuals(frame, smoothed_red, smoothed_blue, target_index):
    """Draw markers, direction vectors, targets, and detailed metrics on the frame."""
    if smoothed_red:
        cv2.circle(frame, smoothed_red, 20, (0, 0, 255), 2)  # Red circle
    if smoothed_blue:
        cv2.circle(frame, smoothed_blue, 20, (255, 0, 0), 2)  # Blue circle

    # Draw orientation line, midpoint, and metrics if both markers are detected
    if smoothed_red is not None and smoothed_blue is not None:
        cv2.line(frame, smoothed_red, smoothed_blue, (0, 255, 0), 2)

        # Calculate the center of the line
        center = calculate_center(smoothed_red, smoothed_blue)

        # Draw a circle at the center of the line
        cv2.circle(frame, center, 10, (0, 255, 255), -1)  # Yellow circle at the center

        # Check if there are points in the list
        if len(targets) > 0:
            target_point = targets[0]

            # Draw a line from the yellow circle to the target point
            cv2.line(frame, center, target_point, (255, 0, 255), 2)  # Magenta line

            # Calculate the distance between the yellow circle and the target point
            distance = math.sqrt((center[0] - target_point[0]) ** 2 + (center[1] - target_point[1]) ** 2)

            # If the yellow circle is within the pixel tolerance of the target point, remove the point
            if distance <= PIXEL_TOLERANCE:
                targets.pop(0)  # Remove the first point
                if len(targets) > 0:
                    print(f"Reached waypoint! Moving to next waypoint: {targets[0]}")
                else:
                    print("All waypoints reached!")

            # Calculate the angle between the red-blue line and the yellow-to-target line
            angle1 = get_absolute_angle(center[0], center[1], target_point[0], target_point[1])
            angle2 = get_absolute_angle(100, 100, 200, 100)
            angle3 = get_absolute_angle(smoothed_red[0], smoothed_red[1], smoothed_blue[0], smoothed_blue[1])
            anglex = get_signed_angle_difference(angle1, angle2)
            angley = get_signed_angle_difference(angle3, angle2)
            angle = -(anglex - angley)

            # Display the distance and angle on the frame
            text_distance = f"Distance: {distance:.2f} px"
            text_angle = f"Angle: {angle:.2f} deg"
            cv2.putText(frame, text_distance, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, text_angle, (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Display the points
        for point in targets:
            cv2.circle(frame, point, 5, (255, 255, 0), -1)  # Cyan circles for points

        # Calculate the length and angle of the line between red and blue points
        length, angle = calculate_angle_and_length(smoothed_red, smoothed_blue)

        # Display the length and angle on the frame
        text_length = f"Length: {length:.2f} px"
        text_angle = f"Line Angle: {angle:.2f} deg"
        cv2.putText(frame, text_length, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, text_angle, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    else:
        # Display an error message if one or both colors are not detected
        cv2.putText(frame, "Error: Colors not detected!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    return frame

def generate_frames(target_index):
    """Generator for MJPEG streaming of annotated frames."""
    while True:
        frame, smoothed_red, smoothed_blue = process_frame()
        if frame is None:
            continue

        # Draw all visuals on the frame
        frame = draw_visuals(frame, smoothed_red, smoothed_blue, target_index)

        # Encode the frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        # Yield the frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(1/6)

@app.route('/markers', methods=['GET'])
def get_markers():
    """Return marker coordinates for the rover without local display."""
    target_index = request.args.get('target_index', type=int)
    frame, smoothed_red, smoothed_blue = process_frame()
    if frame is None:
        return jsonify({'error': 'Failed to capture frame'}), 500

    # Draw visuals but don't display locally
    frame = draw_visuals(frame, smoothed_red, smoothed_blue, target_index)

    # Return marker coordinates
    return jsonify({
        'red': {'x': smoothed_red[0], 'y': smoothed_red[1]} if smoothed_red else None,
        'blue': {'x': smoothed_blue[0], 'y': smoothed_blue[1]} if smoothed_blue else None,
        'center': {'x': (smoothed_red[0] + smoothed_red[1])/2, 'y': (smoothed_blue[0] + smoothed_blue[1])/2}
    })

@app.route('/display', methods=['GET'])
def display():
    """Stream the annotated video feed with all details as MJPEG."""
    target_index = request.args.get('target_index', type=int)
    return Response(generate_frames(target_index),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/action', methods=['GET'])
def get_action():
    """Return an action based on the angle and distance to the target."""
    frame, smoothed_red, smoothed_blue = process_frame()
    if frame is None:
        return jsonify({'error': 'Failed to capture frame'}), 500
    if smoothed_red is None or smoothed_blue is None:
        return jsonify({'error': 'Markers not detected'}), 400
    if len(targets) == 0:
        return jsonify({'action': 'stop', 'message': 'No more targets'})

    center = calculate_center(smoothed_red, smoothed_blue)
    target_point = targets[0]
    distance = math.sqrt((center[0] - target_point[0]) ** 2 + (center[1] - target_point[1]) ** 2)
    angle1 = get_absolute_angle(center[0], center[1], target_point[0], target_point[1])
    angle2 = get_absolute_angle(100, 100, 200, 100)
    angle3 = get_absolute_angle(smoothed_red[0], smoothed_red[1], smoothed_blue[0], smoothed_blue[1])
    anglex = get_signed_angle_difference(angle1, angle2)
    angley = get_signed_angle_difference(angle3, angle2)
    angle = -(anglex - angley)


    if distance <= PIXEL_TOLERANCE:
        action = 'forward'
    elif angle > ANGLE_TOLERANCE:
        action = 'left'
    elif angle < -ANGLE_TOLERANCE:
        action = 'right'
    else:
        action = 'forward'

    return jsonify({'action': action, 'distance': distance, 'angle': angle})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12345)