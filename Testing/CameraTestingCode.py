import cv2
import numpy as np
import math

# Initialize the webcam (0 is usually the default camera)
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
#cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Turn off auto exposure
#cap.set(cv2.CAP_PROP_EXPOSURE, -6)

# Check if the webcam opened successfully
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Initialize smoothed positions
smoothed_red = None
smoothed_blue = None

# Smoothing factor (0.1 keeps 10% of previous position, 90% of new position)
SMOOTHING_FACTOR = 0.1

# Dominance threshold (minimum difference to consider a pixel dominant)
DOMINANCE_THRESHOLD = 30  # Adjusted threshold

# Array of points to display and connect
points = [(233, 84), (390, 86), (617, 92), (563, 290), (438, 392), (239, 414), (70, 394), (56, 313)]  # Example points

# Pixel tolerance for reaching a waypoint
PIXEL_TOLERANCE = 20  # Adjust this value as needed


# Function to find the pixel with the most dominant red or blue value
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


# Function to calculate the angle between two lines
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


# Function to calculate the length and angle of a line
def calculate_angle_and_length(point1, point2):
    # Calculate the length of the line using Euclidean distance
    length = math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)

    # Calculate the angle in radians, then convert to degrees
    angle_rad = math.atan2(point2[1] - point1[1], point2[0] - point1[0])
    angle_deg = math.degrees(angle_rad)

    return length, angle_deg


# Function to calculate the center point between two points
def calculate_center(point1, point2):
    return ((point1[0] + point2[0]) // 2, (point1[1] + point2[1]) // 2)


# Main loop to process webcam feed
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # If frame is not captured, break the loop
    if not ret:
        print("Error: Failed to capture frame.")
        break

    # Flip the frame horizontally (mirror effect)
    frame = cv2.flip(frame, 1)

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
        smoothed_blue = None  # Reset if no valid blue pixel is found

    # Draw on the original frame
    result_frame = frame.copy()

    # Draw circles with smoothed positions if valid
    if smoothed_red is not None:
        cv2.circle(result_frame, smoothed_red, 20, (0, 0, 255), 2)  # Red circle in BGR
    if smoothed_blue is not None:
        cv2.circle(result_frame, smoothed_blue, 20, (255, 0, 0), 2)  # Blue circle in BGR

    # Draw green line between circles if both are valid
    if smoothed_red is not None and smoothed_blue is not None:
        cv2.line(result_frame, smoothed_red, smoothed_blue, (0, 255, 0), 2)

        # Calculate the center of the line
        center = calculate_center(smoothed_red, smoothed_blue)

        # Draw a circle at the center of the line
        cv2.circle(result_frame, center, 10, (0, 255, 255), -1)  # Yellow circle at the center

        # Check if there are points in the list
        if len(points) > 0:
            target_point = points[0]

            # Draw a line from the yellow circle to the target point
            cv2.line(result_frame, center, target_point, (255, 0, 255), 2)  # Magenta line

            # Calculate the distance between the yellow circle and the target point
            distance = math.sqrt((center[0] - target_point[0]) ** 2 + (center[1] - target_point[1]) ** 2)

            # If the yellow circle is within the pixel tolerance of the target point, remove the point
            if distance <= PIXEL_TOLERANCE:
                points.pop(0)  # Remove the first point
                if len(points) > 0:
                    print(f"Reached waypoint! Moving to next waypoint: {points[0]}")
                else:
                    print("All waypoints reached!")

            # Calculate the angle between the red-blue line and the yellow-to-target line
            angle = calculate_angle_between_lines(smoothed_red, smoothed_blue, center, target_point)

            # Display the distance and angle on the frame
            text_distance = f"Distance: {distance:.2f} px"
            text_angle = f"Angle: {angle:.2f} deg"
            cv2.putText(result_frame, text_distance, (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            cv2.putText(result_frame, text_angle, (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Display the points
        for point in points:
            cv2.circle(result_frame, point, 5, (255, 255, 0), -1)  # Cyan circles for points

        # Calculate the length and angle of the line between red and blue points
        length, angle = calculate_angle_and_length(smoothed_red, smoothed_blue)

        # Display the length and angle on the frame
        text_length = f"Length: {length:.2f} px"
        text_angle = f"Line Angle: {angle:.2f} deg"
        cv2.putText(result_frame, text_length, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.putText(result_frame, text_angle, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    else:
        # Display an error message if one or both colors are not detected
        cv2.putText(result_frame, "Error: Colors not detected!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Display the result in a window
    cv2.imshow('Webcam Feed', result_frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close all windows
cap.release()
cv2.destroyAllWindows()