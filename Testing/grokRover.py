import time
from adafruit_motorkit import MotorKit
import requests

# Initialize motor kit
kit = MotorKit()

# Rover-specific constants
SPEED = 0.75  # Default motor speed (-1.0 to 1.0)
STEP_TIME = 0.1  # Time per movement step (seconds)

# Camera server URL (replace with your camera Pi's IP)
CAMERA_URL = 'http://192.168.0.103:12345'

# Motor control functions
def forward(speed=SPEED):
    """Move the rover forward at the specified speed."""
    kit.motor1.throttle = -speed   # Right wheel forward
    kit.motor2.throttle = -speed   # Left wheel forward

def backward(speed=SPEED):
    """Move the rover backward at the specified speed."""
    kit.motor1.throttle = speed  # Right wheel backward
    kit.motor2.throttle = speed  # Left wheel backward

def left(speed=SPEED):
    """Turn the rover left in place at the specified speed."""
    kit.motor1.throttle = 1   # Right wheel forward
    kit.motor2.throttle = -1  # Left wheel backward

def right(speed=SPEED):
    """Turn the rover right in place at the specified speed."""
    kit.motor1.throttle = -1 # Right wheel backward
    kit.motor2.throttle = 1  # Left wheel forward

def stop():
    """Stop all rover movement."""
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0

def get_action():
    """Fetch the action from the camera server."""
    while True:
        try:
            response = requests.get(f'{CAMERA_URL}/action', timeout=1)
            if response.status_code != 200:
                print(f"HTTP {response.status_code}. Retrying...")
                time.sleep(0.1)
                continue
            data = response.json()
            return data.get('action'), data.get('distance'), data.get('angle')
        except (requests.RequestException, KeyError) as e:
            print(f"Error fetching action: {e}. Retrying...")
            time.sleep(0.1)

def main():
    """Main control loop for autonomous navigation."""
    while True:
        # Get the action from the camera server
        action, distance, angle = get_action()

        # Log the action, distance, and angle for debugging
        print(f"Action: {action}, Distance: {distance}, Angle: {angle}")

        # Perform the action
        if action == 'forward':
            forward()
        elif action == 'left':
            left()
        elif action == 'right':
            right()
        elif action == 'stop':
            stop()
            print("All targets reached!")
            break
        else:
            print(f"Unknown action: {action}")
            stop()

        # Wait for the next step
        time.sleep(STEP_TIME)

if __name__ == "__main__":
    main()