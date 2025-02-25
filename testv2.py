import cv2

# Open webcam
cap = cv2.VideoCapture(0)

# Set resolution to 640x480
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640*2)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480*2)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Capture a frame
ret, frame = cap.read()
cap.release()

if not ret:
    print("Error: Could not capture an image.")
    exit()

# Get image dimensions
height, width, _ = frame.shape

# Extract corner pixel values
corners = {
    "top_left": frame[0, 0].tolist(),
    "top_right": frame[0, width - 1].tolist(),
    "bottom_left": frame[height - 1, 0].tolist(),
    "bottom_right": frame[height - 1, width - 1].tolist(),
}

# Display the image in full resolution
cv2.imshow("Captured Image", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Print corner pixel values
print("Corner pixel values (BGR format):")
print(corners)
