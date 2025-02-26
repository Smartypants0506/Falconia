import time
import math
#from adafruit_motorkit import MotorKit
import requests
from bs4 import BeautifulSoup
import json

#kit = MotorKit()

TIME_PER_360 = 1.6
DEGREES_PER_SECOND = 360.0 / TIME_PER_360
ANGLE_TOLERANCE = 15.0
POSITION_TOLERANCE = 3.0
KP_STEERING = 0.5
TIME_PER_FOOT = 0.54
SPEED = 0.75

MAP_WIDTH_INCHES = 142
MAP_HEIGHT_INCHES = 92

targets = [(14.5, 16), (16.5, 16), (19.5, 16), (22.5, 16), (34, 16), (38, 10.5), (46, 7.8), (53, 12), (59, 13.5), (60.5, 18.5)]
current_pos = (9.7, 12.5)

TOP_LEFT_PIXEL = (58, 23) # (58, 469)
TOP_RIGHT_PIXEL = (760, 23) # (58, 23)
BOTTOM_LEFT_PIXEL = (58, 469) # (760, 469)
BOTTOM_RIGHT_PIXEL = (760, 469) # (760, 23)

current_direction = (0.0, 1.0)

def create_vector(angle_degrees, magnitude):
    angle_radians = math.radians(angle_degrees)
    print(f"x: {magnitude * math.cos(angle_radians)}, y: {magnitude * math.sin(angle_radians)}")
    return (magnitude * math.cos(angle_radians), magnitude * math.sin(angle_radians))

def get_angle_and_magnitude(vector):
    x, y = vector
    magnitude = math.hypot(x, y)
    angle_degrees = math.atan2(y, x) * 180 / math.pi
    print(f"angle_degrees: {angle_degrees}, magnitude: {magnitude}")
    return angle_degrees, magnitude

def add_vectors(v1, v2):
    print(f"v1: {v1[0] + v2[0]}, v2: {v1[1] + v2[1]}")
    return (v1[0] + v2[0], v1[1] + v2[1])


def subtract_vectors(v1, v2):
    print(f"v1: {v1[0] + v2[0]}, v2: {v1[1] + v2[1]}")
    return (v1[0] - v2[0], v1[1] - v2[1])

def scale_vector(vector, scalar):
    print(f"Scaled vectorX: {vector[0] * scalar}, Scaled vectorY: {vector[1] * scalar}")
    return (vector[0] * scalar, vector[1] * scalar)

def get_current_pixel():
    global current_pos

    while True:
        try:
            # Fetch the JSON content from the root directory of the website
            response = requests.get('http://10.144.109.36:5000/light_position', timeout=5)
            if response.status_code != 200:
                print(f"Failed to fetch coordinates: HTTP {response.status_code}. Retrying...")
                time.sleep(0.5)
                continue

            # Parse the JSON content
            data = response.json()
            print(data)

            # Extract the coordinates from the JSON
            x = data.get('x')
            y = data.get('y')

            if x is None or y is None:
                print("Coordinates not found in the JSON. Retrying...")
                time.sleep(0.1)
                continue

            print(f"Updated position: ({x}, {y})")
            return (x, y)

            # Brief pause before the next update
            time.sleep(0.1)

        except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
            print(f"Error fetching coordinates: {e}. Retrying...")
            time.sleep(1)

def update_position():
    global current_pos

    current_pixel = get_current_pixel()
    print(f"Current pixel: {current_pixel}")
    pixel_x, pixel_y = current_pixel
    print(f"Current pixel: {pixel_x}, {pixel_y}")

    scale_x = MAP_WIDTH_INCHES / (TOP_RIGHT_PIXEL[0] - TOP_LEFT_PIXEL[0])
    scale_y = MAP_HEIGHT_INCHES / (BOTTOM_LEFT_PIXEL[1] - TOP_LEFT_PIXEL[1])
    print(f"Scale: {scale_x}, {scale_y}")


    x_inches = (pixel_x - TOP_LEFT_PIXEL[0]) * scale_x
    y_inches = (pixel_y - TOP_LEFT_PIXEL[1]) * scale_y
    print(f"Inches: {x_inches}, {y_inches}")

    current_pos = (x_inches, y_inches)
    print(f"Current position: {current_pos}")

def move_forward(distance_inches):
    print(f"Distance: {distance_inches}")
    global current_pos, current_direction
    time_to_move = (distance_inches / 12.0) * TIME_PER_FOOT
    print(f"Time to move: {time_to_move}")
    #kit.motor1.throttle = SPEED
    #kit.motor2.throttle = SPEED
    time.sleep(time_to_move)
    #kit.motor1.throttle = 0
    #kit.motor2.throttle = 0

    displacement = scale_vector(current_direction, distance_inches)
    print(f"Displacement: {displacement}")
    current_pos = add_vectors(current_pos, displacement)
    print(f"Current position: {current_pos}")
    update_position()
    print(f"Updated position: {current_pos}")

def turn_angle(angle_degrees):
    print(f"Angle: {angle_degrees}")
    global current_direction
    turn_time = abs(angle_degrees) / DEGREES_PER_SECOND
    print(f"Turn time: {turn_time}")
    if angle_degrees > 0:
        print("Turning right")
        #kit.motor1.throttle = SPEED
        #kit.motor2.throttle = -SPEED
    else:
        print("Turning left")
        #kit.motor1.throttle = -SPEED
        #kit.motor2.throttle = SPEED
    time.sleep(turn_time)
    #kit.motor1.throttle = 0
    #kit.motor2.throttle = 0

    current_angle, magnitude = get_angle_and_magnitude(current_direction)
    print(f"Current angle: {current_angle}, Magnitude: {magnitude}")
    new_angle = current_angle + angle_degrees
    print(f"New angle: {new_angle}")
    current_direction = create_vector(new_angle, magnitude)
    print(f"Current direction: {current_direction}")

def adjust_heading(target_angle):
    global current_direction
    while True:
        current_angle, _ = get_angle_and_magnitude(current_direction)
        print(f"Current angle: {current_angle}")
        angle_error = target_angle - current_angle
        print(f"Angle error: {angle_error}")

        if angle_error > 180:
            angle_error -= 360
        elif angle_error < -180:
            angle_error += 360

        if abs(angle_error) <= ANGLE_TOLERANCE:
            break

        turn_angle(angle_error)

def move_to_target(target):
    global current_pos, current_direction
    while True:
        update_position()
        print(f"Current position: {current_pos}")
        target_vector = subtract_vectors(target, current_pos)
        print(f"Target vector: {target_vector}")
        distance = get_angle_and_magnitude(target_vector)[1]
        print(f"Distance: {distance}")

        if distance <= POSITION_TOLERANCE:
            break

        desired_angle, _ = get_angle_and_magnitude(target_vector)
        print(f"Desired angle: {desired_angle}")

        current_angle, _ = get_angle_and_magnitude(current_direction)
        print(f"Current angle: {current_angle}")
        angle_error = desired_angle - current_angle
        print(f"Angle error: {angle_error}")
        if angle_error > 180:
            angle_error -= 360
        elif angle_error < -180:
            angle_error += 360

        steering = KP_STEERING * angle_error
        print(f"Steering: {steering}")
        steering = max(-1, min(1, steering))

        #kit.motor1.throttle = SPEED + steering
        #kit.motor2.throttle = SPEED - steering
        time.sleep(0.1)

    #kit.motor1.throttle = 0
    #kit.motor2.throttle = 0

def main():
    global current_pos, current_direction
    update_position()

    initial_pos = current_pos
    print(f"Initial position: {initial_pos}")
    move_forward(3)
    displacement = subtract_vectors(current_pos, initial_pos)
    print(f"Displacement: {displacement}")
    current_direction = create_vector(get_angle_and_magnitude(displacement)[0], 1.0)
    print(f"Current direction: {current_direction}")

    for target in targets:
        print(f"Target: {target}")
        target_vector = subtract_vectors(target, current_pos)
        print(f"Target vector: {target_vector}")
        target_angle, _ = get_angle_and_magnitude(target_vector)
        print(f"Target angle: {target_angle}")
        adjust_heading(target_angle)
        move_to_target(target)

if __name__ == "__main__":
    main()