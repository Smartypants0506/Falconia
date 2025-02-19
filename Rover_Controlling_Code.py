import keyboard
import time
from adafruit_motorkit import MotorKit

# Initialize the motor hat
#kit = MotorKit()

# Configuration
MAX_SPEED = 1.0  # Maximum throttle (range: 0 to 1)
ACCELERATION_STEP = 0.01  # How fast it speeds up
DECELERATION_STEP = 0.05  # How fast it slows down
UPDATE_RATE = 0.01  # Update interval (lower = smoother, higher = more responsive)

# Current speed levels
motor1_speed = 0.0
motor2_speed = 0.0

print("Use arrow keys to control motors smoothly. Press 'esc' to exit.")

while True:
    # Determine target speed for Motor 1 (Up/Down arrows)
    if keyboard.is_pressed("up"):
        target_speed_m1 = MAX_SPEED
    elif keyboard.is_pressed("down"):
        target_speed_m1 = -MAX_SPEED
    else:
        target_speed_m1 = 0

    # Determine target speed for Motor 2 (Left/Right arrows)
    if keyboard.is_pressed("left"):
        target_speed_m2 = MAX_SPEED
    elif keyboard.is_pressed("right"):
        target_speed_m2 = -MAX_SPEED
    else:
        target_speed_m2 = 0

    # Gradually adjust Motor 1 speed
    if motor1_speed < target_speed_m1:
        motor1_speed = min(motor1_speed + ACCELERATION_STEP, target_speed_m1)
    elif motor1_speed > target_speed_m1:
        motor1_speed = max(motor1_speed - DECELERATION_STEP, target_speed_m1)

    # Gradually adjust Motor 2 speed
    if motor2_speed < target_speed_m2:
        motor2_speed = min(motor2_speed + ACCELERATION_STEP, target_speed_m2)
    elif motor2_speed > target_speed_m2:
        motor2_speed = max(motor2_speed - DECELERATION_STEP, target_speed_m2)

    motor1_speed = round(motor1_speed, 3)
    motor2_speed = round(motor2_speed, 3)

    # Apply the speeds to the motors
    kit.motor1.throttle = motor1_speed
    kit.motor2.throttle = motor2_speed

    # Exit on 'esc' key
    if keyboard.is_pressed("esc"):
        break

    time.sleep(UPDATE_RATE)  # Adjusts update rate for smoother response

# Ensure motors fully stop when exiting
kit.motor1.throttle = 0
kit.motor2.throttle = 0
