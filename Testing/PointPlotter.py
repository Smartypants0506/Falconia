import cv2
import numpy as np

# Global variables to store the clicked points
points = []


def mouse_callback(event, x, y, flags, param):
    """Handle mouse events"""
    if event == cv2.EVENT_LBUTTONDOWN:  # Left mouse button clicked
        points.append((x, y))
        # Draw a circle at the clicked point
        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
        print(f"Point added: ({x}, {y})")


def get_points_from_camera():
    """Capture points from camera feed"""
    global points, frame

    # Reset points list
    points = []

    # Open the default camera (usually camera 0)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return []

    # Set up the window and mouse callback
    cv2.namedWindow("Camera - Click to select points, press Enter to finish")
    cv2.setMouseCallback("Camera - Click to select points, press Enter to finish",
                         mouse_callback)

    print("Click on the camera feed to select points. Press Enter when done.")

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        if not ret:
            print("Error: Could not read frame.")
            break

        # Display instructions on the frame
        cv2.putText(frame,
                    "Click to select points, press Enter to finish",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2)

        # Show the frame with marked points
        cv2.imshow("Camera - Click to select points, press Enter to finish", frame)

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
    cap.release()
    cv2.destroyAllWindows()

    return points


# Example usage
if __name__ == "__main__":
    selected_points = get_points_from_camera()
    print("\nFinal list of points:", selected_points)

    # You can now use these points in other functions
    # For example:
    # some_function(selected_points)