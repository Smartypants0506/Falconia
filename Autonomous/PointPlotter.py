import cv2
import numpy as np

# Global variables to store the clicked points
points = []
frame = None


def mouse_callback(event, x, y, flags, param):
    """Handle mouse events"""
    if event == cv2.EVENT_LBUTTONDOWN:  # Left mouse button clicked
        points.append((x, y))
        # Draw a circle at the clicked point
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        print(f"Point added: ({x}, {y})")
        cv2.imshow("Image - Click to select points, press Enter to finish", frame)


def get_points_from_image(image_path):
    """Capture points from a still image"""
    global points, frame

    # Reset points list
    points = []
    # Load the image
    frame = cv2.imread(image_path)

    if frame is None:
        print("Error: Could not load image.")
        return []

    # Set up the window and mouse callback
    cv2.namedWindow("Image - Click to select points, press Enter to finish")
    cv2.setMouseCallback("Image - Click to select points, press Enter to finish", mouse_callback)

    print("Click on the image to select points. Press Enter when done.")

    while True:
        # Show the image with marked points
        cv2.imshow("Image - Click to select points, press Enter to finish", frame)

        # Wait for key press
        key = cv2.waitKey(1) & 0xFF

        # If Enter is pressed (ASCII 13), break the loop
        if key == 13:
            break
        # If ESC is pressed (ASCII 27), break and return empty list
        elif key == 27:
            points = []
            break

    # Clean up
    cv2.destroyAllWindows()

    return points


# Example usage
if __name__ == "__main__":
    image_path = "/Users/omkar/Downloads/one.png"  # Change this to the path of your image
    selected_points = get_points_from_image(image_path)
    print("\nFinal list of points:", selected_points)
