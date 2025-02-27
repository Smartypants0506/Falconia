import cv2

# Load the image
image = cv2.imread('/Users/omkar/Downloads/Screenshot.jpg')  # Replace with your image path
if image is None:
    print("Error: Could not load image.")
    exit()

# Desired dimensions
TARGET_WIDTH = 702
TARGET_HEIGHT = 448

# Calculate aspect ratio of the original image
original_height, original_width = image.shape[:2]
aspect_ratio = original_width / original_height

# Calculate new dimensions while retaining aspect ratio
if aspect_ratio > (TARGET_WIDTH / TARGET_HEIGHT):
    # Image is wider than target, scale based on height
    new_height = TARGET_HEIGHT
    new_width = int(new_height * aspect_ratio)
else:
    # Image is taller than target, scale based on width
    new_width = TARGET_WIDTH
    new_height = int(new_width / aspect_ratio)

# Resize the image while retaining aspect ratio
resized = cv2.resize(image, (new_width, new_height))

# Calculate crop coordinates
start_x = (new_width - TARGET_WIDTH) // 2
start_y = (new_height - TARGET_HEIGHT) // 2

# Crop the center of the image
cropped = resized[start_y:start_y + TARGET_HEIGHT, start_x:start_x + TARGET_WIDTH]

# Calculate inches per pixel ratios
INCHES_WIDTH = 142
INCHES_HEIGHT = 92
scale_x = INCHES_WIDTH / cropped.shape[1]  # 702 pixels wide
scale_y = INCHES_HEIGHT / cropped.shape[0]  # 448 pixels tall

# Mouse callback function
def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        # Calculate inches from top-left corner
        x_inch = x * scale_x
        y_inch = y * scale_y
        # Update window title with coordinates
        cv2.setWindowTitle('Map',
            f"X: {x_inch:.2f}\" Y: {y_inch:.2f}\"  |  Press ESC to exit")

# Create window and set callback
cv2.namedWindow('Map')
cv2.setMouseCallback('Map', on_mouse)

# Show image with initial title
cv2.imshow('Map', cropped)
cv2.setWindowTitle('Map', "Move mouse over map | Press ESC to exit")

# Wait until ESC key is pressed
while True:
    if cv2.waitKey(1) & 0xFF == 27:  # ESC key
        break

cv2.destroyAllWindows()