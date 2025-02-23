import time
import math
from adafruit_motorkit import MotorKit

kit = MotorKit()

TIME_PER_360 = 4.0  # TODO CALCULATE TS
DEGREES_PER_SECOND = 360.0 / TIME_PER_360
ANGLE_TOLERANCE = 5.0
POSITION_TOLERANCE = 1.0
KP_STEERING = 0.5
TIME_PER_FOOT = 2.0  # TODO CALCULATE TS
SPEED = 0.5

#  TODO CHECK TS
MAP_WIDTH_INCHES = 94
MAP_HEIGHT_INCHES = 143
IMAGE_WIDTH_PIXELS = 300
IMAGE_HEIGHT_PIXELS = 500

targets = [(50, 50), (30, 80), (90, 120)]  # TODO MAKE TS UP
current_pos = (0, 0)  # TODO ESTIMATE TS

# TODO AQUIRE TS
TOP_LEFT_PIXEL = (243, 359)
TOP_RIGHT_PIXEL = (543, 359)
BOTTOM_LEFT_PIXEL = (243, 859)
BOTTOM_RIGHT_PIXEL = (543, 859)

current_direction = (0.0, 1.0)

def create_vector(angle_degrees, magnitude):
    angle_radians = math.radians(angle_degrees)
    return (magnitude * math.cos(angle_radians), magnitude * math.sin(angle_radians))

def get_angle_and_magnitude(vector):
    x, y = vector
    magnitude = math.hypot(x, y)
    angle_degrees = math.atan2(y, x) * 180 / math.pi
    return angle_degrees, magnitude

def add_vectors(v1, v2):
    return (v1[0] + v2[0], v1[1] + v2[1])

def subtract_vectors(v1, v2):
    return (v1[0] - v2[0], v1[1] - v2[1])

def scale_vector(vector, scalar):
    return (vector[0] * scalar, vector[1] * scalar)

def get_current_pixel():  # TODO HIT UP ESTEP
    return (393, 609)

def update_position():
    global current_pos

    current_pixel = get_current_pixel()
    pixel_x, pixel_y = current_pixel

    scale_x = MAP_WIDTH_INCHES / (TOP_RIGHT_PIXEL[0] - TOP_LEFT_PIXEL[0])
    scale_y = MAP_HEIGHT_INCHES / (BOTTOM_LEFT_PIXEL[1] - TOP_LEFT_PIXEL[1])

    x_inches = (pixel_x - TOP_LEFT_PIXEL[0]) * scale_x
    y_inches = (pixel_y - TOP_LEFT_PIXEL[1]) * scale_y

    current_pos = (x_inches, y_inches)

def move_forward(distance_inches):
    global current_pos, current_direction
    time_to_move = (distance_inches / 12.0) * TIME_PER_FOOT
    kit.motor1.throttle = SPEED
    kit.motor2.throttle = SPEED
    time.sleep(time_to_move)
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0

    displacement = scale_vector(current_direction, distance_inches)
    current_pos = add_vectors(current_pos, displacement)
    update_position()

def turn_angle(angle_degrees):
    global current_direction
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

    current_angle, magnitude = get_angle_and_magnitude(current_direction)
    new_angle = current_angle + angle_degrees
    current_direction = create_vector(new_angle, magnitude)

def adjust_heading(target_angle):
    global current_direction
    while True:
        current_angle, _ = get_angle_and_magnitude(current_direction)
        angle_error = target_angle - current_angle

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
        target_vector = subtract_vectors(target, current_pos)
        distance = get_angle_and_magnitude(target_vector)[1]

        if distance <= POSITION_TOLERANCE:
            break

        desired_angle, _ = get_angle_and_magnitude(target_vector)

        current_angle, _ = get_angle_and_magnitude(current_direction)
        angle_error = desired_angle - current_angle
        if angle_error > 180:
            angle_error -= 360
        elif angle_error < -180:
            angle_error += 360

        steering = KP_STEERING * angle_error
        steering = max(-1, min(1, steering))

        kit.motor1.throttle = SPEED + steering
        kit.motor2.throttle = SPEED - steering
        time.sleep(0.1)

    kit.motor1.throttle = 0
    kit.motor2.throttle = 0

def main():
    global current_pos, current_direction
    update_position()

    initial_pos = current_pos
    move_forward(3)
    displacement = subtract_vectors(current_pos, initial_pos)
    current_direction = create_vector(get_angle_and_magnitude(displacement)[0], 1.0)

    for target in targets:
        target_vector = subtract_vectors(target, current_pos)
        target_angle, _ = get_angle_and_magnitude(target_vector)
        adjust_heading(target_angle)
        move_to_target(target)

if __name__ == "__main__":
    main()