import cv2
import numpy as np
import math
import requests


# Function to calculate the center point between two points
def calculate_center(point1, point2):
    return ((point1[0] + point2[0]) // 2, (point1[1] + point2[1]) // 2)


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


# Main loop to process webcam feed
while True:
    # Fetch coordinates from the Flask server
    response = requests.get("http://localhost:5000/coordinates")
    if response.status_code == 200:
        data = response.json()
        red_pixel = data["red_pixel"]
        blue_pixel = data["blue_pixel"]

        # Check if both red and blue pixels are detected
        if red_pixel != "Not detected" and blue_pixel != "Not detected":
            # Create a blank frame for visualization
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # Draw red and blue circles
            cv2.circle(frame, red_pixel, 20, (0, 0, 255), 2)  # Red circle
            cv2.circle(frame, blue_pixel, 20, (255, 0, 0), 2)  # Blue circle

            # Draw green line between red and blue circles
            cv2.line(frame, red_pixel, blue_pixel, (0, 255, 0), 2)

            # Calculate the center of the line
            center = calculate_center(red_pixel, blue_pixel)

            # Draw a yellow circle at the center
            cv2.circle(frame, center, 10, (0, 255, 255), -1)  # Yellow circle

            # Example target point
            target_point = (320, 240)  # Replace with your logic for target points

            # Draw a magenta line from the yellow circle to the target point
            cv2.line(frame, center, target_point, (255, 0, 255), 2)

            # Calculate the angle between the red-blue line and the yellow-to-target line
            angle = calculate_angle_between_lines(red_pixel, blue_pixel, center, target_point)

            # Display the angle on the frame
            text_angle = f"Angle: {angle:.2f} deg"
            cv2.putText(frame, text_angle, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # Display the frame
            cv2.imshow('Client Visualization', frame)
        else:
            print("Red or blue pixel not detected.")
    else:
        print("Failed to fetch coordinates from the server.")

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cv2.destroyAllWindows()