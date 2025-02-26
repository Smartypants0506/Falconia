import time
import math
import numpy as np
import cv2
import requests
import re
from adafruit_motorkit import MotorKit

# Initialize motor controller
kit = MotorKit()

# Constants
TIME_PER_360 = 1.6  # Time for a full 360-degree turn (seconds)
DEGREES_PER_SECOND = 360.0 / TIME_PER_360
ANGLE_TOLERANCE = 15.0  # Tolerance for angle alignment (degrees)
POSITION_TOLERANCE = 3.0  # Tolerance for position alignment (inches)
KP_STEERING = 1.0  # Proportional gain for steering
TIME_PER_FOOT = 0.54  # Time to travel 1 foot (seconds)
SPEED = 0.75  # Motor speed (0 to 1)

# Map dimensions (inches)
MAP_WIDTH_INCHES = 142
MAP_HEIGHT_INCHES = 92

targets = [(14.5, 16), (16.5, 16), (19.5, 16), (22.5, 16), (34, 16), (38, 10.5), (46, 7.8), (53, 12), (59, 13.5), (60.5, 18.5)]
current_pos = (9.7, 12.5)


current_direction = (0.0, 1.0)  # Initial direction vector (facing positive Y-axis)

# Camera pixel coordinates of map corners
TOP_LEFT_PIXEL = (58, 469)
TOP_RIGHT_PIXEL = (58, 23)
BOTTOM_LEFT_PIXEL = (760, 469)
BOTTOM_RIGHT_PIXEL = (760, 23)

# Perspective transform setup
real_corners = np.array([
    [0, 0],  # Top-left
    [MAP_WIDTH_INCHES, 0],  # Top-right
    [0, MAP_HEIGHT_INCHES],  # Bottom-left
    [MAP_WIDTH_INCHES, MAP_HEIGHT_INCHES]  # Bottom-right
], dtype=np.float32)

pixel_corners = np.array([
    TOP_LEFT_PIXEL,
    TOP_RIGHT_PIXEL,
    BOTTOM_LEFT_PIXEL,
    BOTTOM_RIGHT_PIXEL
], dtype=np.float32)

# Calculate perspective transform matrix
M = cv2.getPerspectiveTransform(pixel_corners, real_corners)


# PID Controller Class
class PIDController:
    def __init__(self, Kp, Ki, Kd, sample_time, output_limits=(-1, 1)):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.sample_time = sample_time
        self.output_limits = output_limits
        self.reset()

    def reset(self):
        self.integral = 0
        self.previous_error = None
        self.last_time = time.monotonic()

    def compute(self, error):
        now = time.monotonic()
        dt = now - self.last_time

        if dt < self.sample_time:
            return None

        # Proportional
        P = self.Kp * error

        # Integral
        self.integral += error * dt
        I = self.Ki * self.integral

        # Derivative
        if self.previous_error is not None:
            D = self.Kd * (error - self.previous_error) / dt
        else:
            D = 0

        # Store values
        self.previous_error = error
        self.last_time = now

        # Calculate output
        output = P + I + D

        # Clamp output
        output = max(self.output_limits[0], min(output, self.output_limits[1]))

        return output


# Initialize PID for steering TODO TUNE
pid_steering = PIDController(
    Kp=1.0,
    Ki=0.1,
    Kd=0.05,
    sample_time=0.1,
    output_limits=(-1, 1)
)


# Helper Functions
def pixel_to_inches(pixel_point):
    px = np.array([[pixel_point]], dtype=np.float32)
    transformed = cv2.perspectiveTransform(px, M)
    return (transformed[0][0][0], transformed[0][0][1])


def get_heading_from_displacement(old_pos, new_pos):
    dx = new_pos[0] - old_pos[0]
    dy = new_pos[1] - old_pos[1]
    if dx == 0 and dy == 0:
        return None  # No movement
    return math.atan2(dy, dx)  # Returns heading in radians


def update_direction_using_displacement(old_pos, new_pos):
    global current_direction
    heading = get_heading_from_displacement(old_pos, new_pos)
    if heading is not None:
        # Update direction vector
        current_direction = (math.cos(heading), math.sin(heading))


def get_current_pixel():
    session = requests.Session()
    while True:
        try:
            response = session.get('http://192.168.0.100:8080/', timeout=1)
            if response.status_code == 200:
                # Use regex for faster parsing
                match = re.search(r'(\d+\.?\d*)\D*(\d+\.?\d*)', response.text)
                if match:
                    return (float(match.group(1)), float(match.group(2)))
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(0.05)


def update_position():
    global current_pos
    current_pixel = get_current_pixel()
    current_pos = pixel_to_inches(current_pixel)


def turn_to_angle(target_heading_deg):
    global current_direction

    pid_steering.reset()

    while True:
        current_pos = get_current_pixel()
        current_heading = math.degrees(math.atan2(current_direction[1], current_direction[0]))

        # Calculate angle error (normalized to ±180)
        error = (target_heading_deg - current_heading) % 360
        if error > 180:
            error -= 360

        if abs(error) < ANGLE_TOLERANCE:
            break

        # Get PID output
        pid_output = pid_steering.compute(error)

        # Convert PID output to motor commands
        turn_duration = abs(pid_output) * 0.1  # Adjust scaling factor
        if pid_output > 0:
            # Turn clockwise
            kit.motor1.throttle = SPEED
            kit.motor2.throttle = -SPEED
        else:
            # Turn counter-clockwise
            kit.motor1.throttle = -SPEED
            kit.motor2.throttle = SPEED

        time.sleep(turn_duration)

        # Stop motors briefly
        kit.motor1.throttle = 0
        kit.motor2.throttle = 0

        # Update direction using camera feedback
        new_pos = get_current_pixel()
        update_direction_using_displacement(current_pos, new_pos)


def move_to_target(target_pos):
    global current_pos

    while True:
        update_position()
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]
        distance = math.hypot(dx, dy)

        if distance < POSITION_TOLERANCE:
            break

        # Calculate target heading
        target_heading = math.degrees(math.atan2(dy, dx))
        turn_to_angle(target_heading)

        # Move forward
        kit.motor1.throttle = SPEED
        kit.motor2.throttle = SPEED
        time.sleep(distance * TIME_PER_FOOT / 12)  # Convert inches to feet

        # Stop motors
        kit.motor1.throttle = 0
        kit.motor2.throttle = 0


# Main Loop
def main():
    for target in targets:
        print(f"Moving to target: {target}")
        move_to_target(target)
        time.sleep(1)  # Pause at each target


if __name__ == "__main__":
    main()