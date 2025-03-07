import time
import math
from adafruit_motorkit import MotorKit
import requests
import json

# Initialize motor kit
kit = MotorKit()

# Rover-specific constants (independent from camera)
ANGLE_TOLERANCE = 10.0  # degrees
POSITION_TOLERANCE = 20.0  # pixels (matches camera's PIXEL_TOLERANCE)
SPEED = 0.75  # Default motor speed (-1.0 to 1.0)
KP_STEERING = 0.02  # Proportional gain for steering
STEP_TIME = 0.1  # Time per movement step (seconds)

# Rover’s independent target list
targets = [(233, 84), (390, 86), (617, 92), (563, 290), (438, 392), (239, 414), (70, 394), (56, 313)]

# Camera server URL (replace with your camera Pi's IP)
CAMERA_URL = 'http://<camera_pi_ip>:5000'

# Motor control functions
def forward(speed=SPEED):
    """Move the rover forward at the specified speed."""
    kit.motor1.throttle = speed   # Right wheel forward
    kit.motor2.throttle = speed   # Left wheel forward

def backward(speed=SPEED):
    """Move the rover backward at the specified speed."""
    kit.motor1.throttle = -speed  # Right wheel backward
    kit.motor2.throttle = -speed  # Left wheel backward

def left(speed=SPEED):
    """Turn the rover left in place at the specified speed."""
    kit.motor1.throttle = speed   # Right wheel forward
    kit.motor2.throttle = -speed  # Left wheel backward

def right(speed=SPEED):
    """Turn the rover right in place at the specified speed."""
    kit.motor1.throttle = -speed  # Right wheel backward
    kit.motor2.throttle = speed   # Left wheel forward

def stop():
    """Stop all rover movement."""
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0

def get_markers(target_index):
    """Fetch red and blue pixel coordinates from the camera server."""
    while True:
        try:
            response = requests.get(f'{CAMERA_URL}/markers?target_index={target_index}', timeout=5)
            if response.status_code != 200:
                print(f"HTTP {response.status_code}. Retrying...")
                time.sleep(0.5)
                continue
            data = response.json()
            red = data.get('red')
            blue = data.get('blue')
            if red is None or blue is None:
                print("Markers not detected. Retrying...")
                time.sleep(0.1)
                continue
            return (red['x'], red['y']), (blue['x'], blue['y'])
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"Error fetching markers: {e}. Retrying...")
            time.sleep(1)

def calculate_center(point1, point2):
    """Calculate the center point between two points (matches camera's draw_visuals)."""
    return ((point1[0] + point2[0]) // 2, (point1[1] + point2[1]) // 2)

def calculate_angle_and_length(point1, point2):
    """Calculate the length and angle of a line (matches camera's draw_visuals)."""
    length = math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)
    angle_rad = math.atan2(point2[1] - point1[1], point2[0] - point1[0])
    angle_deg = math.degrees(angle_rad)
    return length, angle_deg

def calculate_angle_between_lines(line1_start, line1_end, line2_start, line2_end):
    """Calculate the angle between two lines in degrees (matches camera's draw_visuals)."""
    vector1 = (line1_end[0] - line1_start[0], line1_end[1] - line1_start[1])
    vector2 = (line2_end[0] - line2_start[0], line2_end[1] - line2_start[1])
    dot_product = vector1[0] * vector2[0] + vector1[1] * vector2[1]
    magnitude1 = math.sqrt(vector1[0] ** 2 + vector1[1] ** 2)
    magnitude2 = math.sqrt(vector2[0] ** 2 + vector2[1] ** 2)
    angle_rad = math.acos(dot_product / (magnitude1 * magnitude2))
    return math.degrees(angle_rad)

def normalize_angle(angle):
    """Normalize angle to [-180, 180] degrees (matches camera's draw_visuals)."""
    return (angle + 180) % 360 - 180

def turn_to_angle(target_angle, target_index):
    """Turn rover until its orientation matches the target angle."""
    while True:
        red_pixel, blue_pixel = get_markers(target_index)
        center = calculate_center(red_pixel, blue_pixel)
        _, current_angle = calculate_angle_and_length(red_pixel, blue_pixel)
        angle_error = normalize_angle(target_angle - current_angle)

        if abs(angle_error) <= ANGLE_TOLERANCE:
            stop()
            break

        if angle_error > 0:
            left(SPEED)  # Turn left (counterclockwise)
        else:
            right(SPEED)  # Turn right (clockwise)
        time.sleep(STEP_TIME)

def main():
    """Main control loop for autonomous navigation."""
    for i, target in enumerate(targets):
        print(f"Navigating to target {i}: {target}")

        while True:
            red_pixel, blue_pixel = get_markers(i)
            center = calculate_center(red_pixel, blue_pixel)
            orientation_length, current_angle = calculate_angle_and_length(red_pixel, blue_pixel)

            target_vector = (target[0] - center[0], target[1] - center[1])
            distance = math.hypot(target_vector[0], target_vector[1])

            if distance <= POSITION_TOLERANCE:
                print(f"Reached target {i}: {target}")
                break

            target_angle = math.degrees(math.atan2(target_vector[1], target_vector[0]))
            angle_error = normalize_angle(target_angle - current_angle)

            angle_between = calculate_angle_between_lines(red_pixel, blue_pixel, center, target)
            print(f"Angle between orientation and target: {angle_between:.2f} deg")  # For debugging

            if abs(angle_error) > ANGLE_TOLERANCE:
                turn_to_angle(target_angle, i)
                continue

            # Move forward with steering adjustment
            steering = KP_STEERING * angle_error
            steering = max(-1.0, min(1.0, steering))
            right_speed = SPEED - steering
            left_speed = SPEED + steering
            kit.motor1.throttle = right_speed  # Right wheel
            kit.motor2.throttle = left_speed   # Left wheel
            time.sleep(STEP_TIME)
            stop()

    stop()
    print("All targets reached!")

if __name__ == "__main__":
    main()