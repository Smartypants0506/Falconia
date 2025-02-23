import time
import math
from adafruit_motorkit import MotorKit

# Motor setup
kit = MotorKit()

# Constants
TIME_PER_360 = 4.0  # Time (s) for 360-degree turn TODO CALCULATE TS
DEGREES_PER_SECOND = 360.0 / TIME_PER_360
ANGLE_TOLERANCE = 5.0  # Degrees
POSITION_TOLERANCE = 1.0  # Inches
KP_STEERING = 0.5  # Steering proportional gain
TIME_PER_FOOT = 2.0  # Time (s) to move 1 foot (12 inches) TODO CALCULATE TS
SPEED = 0.5  # Base motor speed (0 to 1)

# Target waypoints (x, y) in inches
targets = [(50, 50), (30, 80), (90, 120)] #TODO MAKE TS UP
current_pos = (0, 0)  # Initial position (top-left corner) #TODO ESTIMATE TS

# Constants for map and image dimensions TODO CHECK TS
MAP_WIDTH_INCHES = 94  # Map width in inches
MAP_HEIGHT_INCHES = 143  # Map height in inches
IMAGE_WIDTH_PIXELS = 300  # Image width in pixels
IMAGE_HEIGHT_PIXELS = 500  # Image height in pixels

# Known corners of the map in pixels (from the website) TODO AQUIRE TS
TOP_LEFT_PIXEL = (243, 359)  # Pixel corresponding to (0, 0) on the map
TOP_RIGHT_PIXEL = (543, 359)  # Pixel corresponding to (94, 0) on the map
BOTTOM_LEFT_PIXEL = (243, 859)  # Pixel corresponding to (0, 143) on the map
BOTTOM_RIGHT_PIXEL = (543, 859)  # Pixel corresponding to (94, 143) on the map

def get_current_pixel(): # TODO HIT UP ESTEP
    # Replace with actual code to fetch the current pixel from the website
    # For now, return a simulated pixel (e.g., the middle of the map)
    return (393, 609)  # Example pixel

def update_position():
    global current_pos

    # Get the current pixel from the website
    current_pixel = get_current_pixel()
    pixel_x, pixel_y = current_pixel

    # Calculate scaling factors (inches per pixel)
    scale_x = MAP_WIDTH_INCHES / (TOP_RIGHT_PIXEL[0] - TOP_LEFT_PIXEL[0])
    scale_y = MAP_HEIGHT_INCHES / (BOTTOM_LEFT_PIXEL[1] - TOP_LEFT_PIXEL[1])

    # Calculate the position in inches from the top-left corner of the map
    x_inches = (pixel_x - TOP_LEFT_PIXEL[0]) * scale_x
    y_inches = (pixel_y - TOP_LEFT_PIXEL[1]) * scale_y

    # Update the rover's current position
    current_pos = (x_inches, y_inches)

# Helper function to calculate angle between two points
def calculate_angle(x1, y1, x2, y2):
    return math.atan2(y2 - y1, x2 - x1) * 180 / math.pi

# Helper function to move forward a specific distance
def move_forward(distance_inches):
    time_to_move = (distance_inches / 12.0) * TIME_PER_FOOT
    kit.motor1.throttle = SPEED
    kit.motor2.throttle = SPEED
    time.sleep(time_to_move)
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0
    update_position()  # Update position after moving

# Helper function to turn a specific angle (in degrees)
def turn_angle(angle_degrees):
    turn_time = abs(angle_degrees) / DEGREES_PER_SECOND
    if angle_degrees > 0:
        kit.motor1.throttle = SPEED
        kit.motor2.throttle = -SPEED
    else:
        kit.motor1.throttle = -SPEED
        kit.motor2.throttle = SPEED
    time.sleep(turn_time)
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0

# Turn handling with feedback loop
def adjust_heading(target_angle):
    global current_pos
    while True:
        # Get current direction by moving forward slightly
        start_pos = current_pos
        move_forward(3)  # Move 6 inches to establish direction
        current_angle = calculate_angle(start_pos[0], start_pos[1], current_pos[0], current_pos[1])
        angle_error = target_angle - current_angle

        # Normalize angle error
        if angle_error > 180:
            angle_error -= 360
        elif angle_error < -180:
            angle_error += 360

        if abs(angle_error) <= ANGLE_TOLERANCE:
            break

        # Turn to correct angle
        turn_angle(angle_error)

# PID-controlled movement to target
def move_to_target(target):
    global current_pos
    while True:
        update_position()
        dx = target[0] - current_pos[0]
        dy = target[1] - current_pos[1]
        distance = math.hypot(dx, dy)

        if distance <= POSITION_TOLERANCE:
            break

        desired_angle = calculate_angle(current_pos[0], current_pos[1], target[0], target[1])

        # Get current movement angle
        prev_pos = current_pos
        move_forward(2)  # Move 6 inches to establish direction
        current_angle = calculate_angle(prev_pos[0], prev_pos[1], current_pos[0], current_pos[1])

        # Calculate steering adjustment
        angle_error = desired_angle - current_angle
        if angle_error > 180:
            angle_error -= 360
        elif angle_error < -180:
            angle_error += 360

        steering = KP_STEERING * angle_error
        steering = max(-1, min(1, steering))  # Constrain steering to [-1, 1]

        # Apply steering
        kit.motor1.throttle = SPEED + steering
        kit.motor2.throttle = SPEED - steering
        time.sleep(0.1)

    kit.motor1.throttle = 0
    kit.motor2.throttle = 0

# Main navigation loop
def main():
    global current_pos
    update_position()  # Get initial position

    # Establish initial direction
    #initial_pos = current_pos
    # move_forward(3)  # Move 2 feet to establish initial direction
    # initial_angle = calculate_angle(initial_pos[0], initial_pos[1], current_pos[0], current_pos[1])

    # Navigate through targets
    for target in targets:
        target_angle = calculate_angle(current_pos[0], current_pos[1], target[0], target[1])
        adjust_heading(target_angle)
        move_to_target(target)

if __name__ == "__main__":
    main()