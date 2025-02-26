import cv2
import numpy as np

# Define the points for resizing
TOP_LEFT_PIXEL = (58, 23)  # (x, y)
BOTTOM_RIGHT_PIXEL = (760, 469)  # (x, y)

# Define the real-world dimensions of the map (in inches)
MAP_WIDTH_INCHES = 140
MAP_HEIGHT_INCHES = 90

# Load the image from a PNG file
image_path = "C:/Users/banta/Downloads/Screensho(1).png"  # Replace with the path to your PNG file
frame = cv2.imread(image_path)

# Check if the image was loaded successfully
if frame is None:
    print("Error: Could not load image.")
    exit()

# Calculate the width and height based on the points
width = BOTTOM_RIGHT_PIXEL[0] - TOP_LEFT_PIXEL[0]
height = BOTTOM_RIGHT_PIXEL[1] - TOP_LEFT_PIXEL[1]

# Ensure width and height are positive
if width <= 0 or height <= 0:
    print("Error: Invalid coordinates. Width or height is zero or negative.")
    exit()

# Resize the image to the specified dimensions
frame = cv2.resize(frame, (width, height))

# Calculate the conversion factors (pixels to inches)
pixels_to_inches_x = MAP_WIDTH_INCHES / width
pixels_to_inches_y = MAP_HEIGHT_INCHES / height


# Function to display pixel coordinates and real-world measurements on mouse hover
def show_pixel_info(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        # Create a copy of the frame to draw the info on
        frame_copy = frame.copy()

        # Calculate the real-world measurements in inches
        inches_x = x * pixels_to_inches_x
        inches_y = y * pixels_to_inches_y

        # Display the pixel coordinates and real-world measurements
        text_pixel = f"Pixel: ({x}, {y})"
        text_inches = f"Inches: ({inches_x:.2f}, {inches_y:.2f})"
        cv2.putText(frame_copy, text_pixel, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame_copy, text_inches, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Show the frame with the info
        cv2.imshow("Map Image", frame_copy)


# Set the mouse callback function
cv2.imshow("Map Image", frame)
cv2.setMouseCallback("Map Image", show_pixel_info)

# Wait for a key press and close the window
cv2.waitKey(0)
cv2.destroyAllWindows()