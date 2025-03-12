import cv2
import numpy as np
from flask import Flask, jsonify, request, Response
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
PIXEL_TOLERANCE = 20

# Define the array of targets in pixel coordinates as tuples
targets = [(249, 252), (267, 375), (266, 494), (322, 571), (443, 580), (573, 599), (698, 595), (803, 589), (818, 535), (818, 446), (814, 371), (775, 333), (682, 323), (573, 312), (485, 313), (414, 325), (409, 424), (457, 494)]

# Define angle and position tolerances
ANGLE_TOLERANCE = 10  # degrees
POSITION_TOLERANCE = 20  # pixels

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

def process_frame():
    """Process the frame and return smoothed marker positions."""
    global smoothed_red, smoothed_blue
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        return None, None, None
    frame = cv2.flip(frame, 1)

    # Detect white rectangle
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 30, 255])
    mask_white = cv2.inRange(hsv, lower_white, upper_white)
    contours, _ = cv2.findContours(mask_white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    white_rect = None
    max_area = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 1000:  # Filter small areas
            continue
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) == 4:
            if area > max_area:
                max_area = area
                white_rect = approx

    red_center = None
    blue_center = None

    if white_rect is not None:
        x, y, w, h = cv2.boundingRect(white_rect)
        roi = frame[y:y+h, x:x+w]
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Detect red rectangle
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        mask_red = cv2.inRange(hsv_roi, lower_red1, upper_red1) | cv2.inRange(hsv_roi, lower_red2, upper_red2)
        red_contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if red_contours:
            largest_red = max(red_contours, key=cv2.contourArea)
            epsilon = 0.02 * cv2.arcLength(largest_red, True)
            approx_red = cv2.approxPolyDP(largest_red, epsilon, True)
            if len(approx_red) == 4:
                xr, yr, wr, hr = cv2.boundingRect(approx_red)
                red_center = (x + xr + wr//2, y + yr + hr//2)

        # Detect blue rectangle
        lower_blue = np.array([90, 100, 100])
        upper_blue = np.array([120, 255, 255])
        mask_blue = cv2.inRange(hsv_roi, lower_blue, upper_blue)
        blue_contours, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if blue_contours:
            largest_blue = max(blue_contours, key=cv2.contourArea)
            epsilon = 0.02 * cv2.arcLength(largest_blue, True)
            approx_blue = cv2.approxPolyDP(largest_blue, epsilon, True)
            if len(approx_blue) == 4:
                xb, yb, wb, hb = cv2.boundingRect(approx_blue)
                blue_center = (x + xb + wb//2, y + yb + hb//2)

    # Apply smoothing
    if red_center is not None:
        if smoothed_red is None:
            smoothed_red = red_center
        else:
            smoothed_red = (
                int(smoothed_red[0] * SMOOTHING_FACTOR + red_center[0] * (1 - SMOOTHING_FACTOR)),
                int(smoothed_red[1] * SMOOTHING_FACTOR + red_center[1] * (1 - SMOOTHING_FACTOR))
            )
    else:
        smoothed_red = None

    if blue_center is not None:
        if smoothed_blue is None:
            smoothed_blue = blue_center
        else:
            smoothed_blue = (
                int(smoothed_blue[0] * SMOOTHING_FACTOR + blue_center[0] * (1 - SMOOTHING_FACTOR)),
                int(smoothed_blue[1] * SMOOTHING_FACTOR + blue_center[1] * (1 - SMOOTHING_FACTOR))
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
        center = calculate_center(smoothed_red, smoothed_blue)
        cv2.circle(frame, center, 10, (0, 255, 255), -1)  # Yellow circle

        if len(targets) > 0:
            target_point = targets[0]
            cv2.line(frame, center, target_point, (255, 0, 255), 2)
            distance = math.sqrt((center[0] - target_point[0]) ** 2 + (center[1] - target_point[1]) ** 2)
            if distance <= PIXEL_TOLERANCE:
                targets.pop(0)
            angle = calculate_angle_between_lines(smoothed_red, smoothed_blue, center, target_point)
            cv2.putText(frame, f"Distance: {distance:.2f} px", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f"Angle: {angle:.2f} deg", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        for point in targets:
            cv2.circle(frame, point, 5, (255, 255, 0), -1)

        length, angle = calculate_angle_and_length(smoothed_red, smoothed_blue)
        cv2.putText(frame, f"Length: {length:.2f} px", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Line Angle: {angle:.2f} deg", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    else:
        cv2.putText(frame, "Error: Colors not detected!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    return frame

@app.route('/markers', methods=['GET'])
def get_markers():
    """Return marker coordinates for the rover without local display."""
    target_index = request.args.get('target_index', type=int)
    frame, smoothed_red, smoothed_blue = process_frame()
    if frame is None:
        return jsonify({'error': 'Failed to capture frame'}), 500
    frame = draw_visuals(frame, smoothed_red, smoothed_blue, target_index)
    return jsonify({
        'red': {'x': smoothed_red[0], 'y': smoothed_red[1]} if smoothed_red else None,
        'blue': {'x': smoothed_blue[0], 'y': smoothed_blue[1]} if smoothed_blue else None
    })

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
    angle = calculate_angle_between_lines(smoothed_red, smoothed_blue, center, target_point)

    if distance <= POSITION_TOLERANCE:
        action = 'forward'
    elif angle > ANGLE_TOLERANCE:
        action = 'right'
    elif angle < -ANGLE_TOLERANCE:
        action = 'left'
    else:
        action = 'forward'

    return jsonify({'action': action, 'distance': distance, 'angle': angle})

def generate_frames(target_index):
    while True:
        frame, smoothed_red, smoothed_blue = process_frame()
        if frame is None:
            continue
        frame = draw_visuals(frame, smoothed_red, smoothed_blue, target_index)
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

@app.route('/display')
def display():
    target_index = request.args.get('target_index', type=int)
    return Response(generate_frames(target_index), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12345)