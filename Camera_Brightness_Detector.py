import cv2
import time

# Open the default webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Set the resolution to 320x240
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

failure_count = 0  # Counter for consecutive frame failures
max_failures = 10  # Max consecutive failures before exiting

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        failure_count += 1
        print(f"Warning: Can't receive frame ({failure_count}/{max_failures}). Retrying...")
        if failure_count >= max_failures:
            print("Error: Maximum frame read failures reached. Exiting program.")
            break
        time.sleep(0.1)  # Short delay before retrying
        continue

    failure_count = 0  # Reset failure count after a successful read

    # Resize the frame to 320x240 (in case the camera doesn't support setting resolution)
    frame = cv2.resize(frame, (640, 480))

    # Convert the frame to grayscale
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Find the brightest pixel
    _, max_val, _, max_loc = cv2.minMaxLoc(gray_frame)
    brightest_pixel_value = max_val
    brightest_pixel_coords = max_loc

    # Draw a bounding box around the brightest pixel
    box_size = 20  # Size of the bounding box
    x, y = brightest_pixel_coords
    top_left = (max(0, x - box_size // 2), max(0, y - box_size // 2))
    bottom_right = (min(320, x + box_size // 2), min(240, y + box_size // 2))
    cv2.rectangle(frame, top_left, bottom_right, (0, 255, 0), 2)  # Green bounding box

    # Display the brightest pixel value and coordinates
    text = f"Brightest Pixel: {brightest_pixel_value} at {brightest_pixel_coords}"
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Display the frame
    cv2.imshow('Webcam with Brightest Pixel', frame)

    # Press 'q' to exit
    if cv2.waitKey(1) == ord('q'):
        break

# Release the webcam and close the window
cap.release()
cv2.destroyAllWindows()
