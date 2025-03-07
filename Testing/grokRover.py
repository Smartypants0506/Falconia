import time
import math
from adafruit_motorkit import MotorKit
import requests
import json

# Initialize motor kit
kit = MotorKit()

# Control parameters
ANGLE_TOLERANCE = 15.0  # degrees
POSITION_TOLERANCE = 10.0  # pixels
SPEED = 0.75  # Motor speed (-1.0 to 1.0)
KP_STEERING = 0.02  # Proportional gain for steering
STEP_TIME = 0.1  # Time per movement step (seconds)

# Target list in pixel coordinates
targets = [
    (100, 100), (200, 100), (300, 100), (400, 100),
    (500, 100), (600, 100), (700, 100)
]

# Camera server URL (replace with camera Pi's IP)
CAMERA_URL = 'http://<camera_pi_ip>:5000'

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

def calculate_midpoint(red_pixel, blue_pixel):
    """Calculate midpoint between red and blue markers in pixels."""
    return ((red_pixel[0] + blue_pixel[0]) // 2, (red_pixel[1] + blue_pixel[1]) // 2)

def calculate_direction(red_pixel, blue_pixel):
    """Calculate direction vector from red (rear) to blue (front)."""
    return (blue_pixel[0] - red_pixel[0], blue_pixel[1] - red_pixel[1])

def calculate_angle(vector):
    """Calculate angle of a vector in degrees."""
    return math.degrees(math.atan2(vector[1], vector[0]))

def normalize_angle(angle):
    """Normalize angle to [-180, 180] degrees."""
    return (angle + 180) % 360 - 180

def turn_to_angle(target_angle, target_index):
    """Turn rover until its orientation matches the target angle."""
    while True:
        red_pixel, blue_pixel = get_markers(target_index)
        direction_vector = calculate_direction(red_pixel, blue_pixel)
        current_angle = calculate_angle(direction_vector)
        angle_error = normalize_angle(target_angle - current_angle)

        if abs(angle_error) <= ANGLE_TOLERANCE:
            kit.motor1.throttle = 0
            kit.motor2.throttle = 0
            break

        # Turn in place
        if angle_error > 0:
            kit.motor1.throttle = SPEED   # Right wheel forward
            kit.motor2.throttle = -SPEED  # Left wheel backward
        else:
            kit.motor1.throttle = -SPEED  # Right wheel backward
            kit.motor2.throttle = SPEED   # Left wheel forward
        time.sleep(STEP_TIME)

def main():
    """Main control loop for autonomous navigation."""
    # Send targets to camera server
    targets_list = [{'x': int(t[0]), 'y': int(t[1])} for t in targets]
    requests.post(f'{CAMERA_URL}/set_targets', json={'targets': targets_list})

    for i, target in enumerate(targets):
        print(f"Navigating to target {i}: {target}")

        # Turn to align with target
        while True:
            red_pixel, blue_pixel = get_markers(i)
            midpoint = calculate_midpoint(red_pixel, blue_pixel)
            direction_vector = calculate_direction(red_pixel, blue_pixel)
            current_angle = calculate_angle(direction_vector)
            target_vector = (target[0] - midpoint[0], target[1] - midpoint[1])
            target_angle = calculate_angle(target_vector)
            angle_error = normalize_angle(target_angle - current_angle)
            if abs(angle_error) > ANGLE_TOLERANCE:
                turn_to_angle(target_angle, i)
            else:
                break

        # Move toward target with steering adjustment
        while True:
            red_pixel, blue_pixel = get_markers(i)
            midpoint = calculate_midpoint(red_pixel, blue_pixel)
            direction_vector = calculate_direction(red_pixel, blue_pixel)
            current_angle = calculate_angle(direction_vector)
            target_vector = (target[0] - midpoint[0], target[1] - midpoint[1])
            target_angle = calculate_angle(target_vector)
            distance = math.hypot(target_vector[0], target_vector[1])
            if distance <= POSITION_TOLERANCE:
                print(f"Reached target {i}: {target}")
                break
            angle_error = normalize_angle(target_angle - current_angle)
            steering = KP_STEERING * angle_error
            steering = max(-1.0, min(1.0, steering))
            kit.motor1.throttle = SPEED + steering
            kit.motor2.throttle = SPEED - steering
            time.sleep(STEP_TIME)
            kit.motor1.throttle = 0
            kit.motor2.throttle = 0

    # Stop rover after all targets are reached
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0
    print("All targets reached!")

if __name__ == "__main__":
    main()