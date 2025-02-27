import time
import math
from adafruit_motorkit import MotorKit
import requests
from bs4 import BeautifulSoup

kit = MotorKit() # TODO MAY HAVE TO ADJUST MOVEMENT

TIME_PER_360 = 1.55
DEGREES_PER_SECOND = 360.0 / TIME_PER_360
ANGLE_TOLERANCE = 15
POSITION_TOLERANCE = 50 #TODO ADJUST AS NECESARY
KP_STEERING = 1/0.75
TIME_PER_FOOT = 0.54
SPEED = 0.75

targets = [(570,260 ), (1130, 710), (1120, 642)]  # TODO MAKE TS UP
current_pos = (0, 0)  # TODO ESTIMATE TS

# TODO AQUIRE TS
TOP_LEFT_PIXEL = (0, 0)
TOP_RIGHT_PIXEL = (0, 640*2)
BOTTOM_LEFT_PIXEL = (480*2, 0)
BOTTOM_RIGHT_PIXEL = (754, 23)

current_direction = (90.0, 1.0)

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


def update_position():
    global current_pos

    while True:
        try:
            # Fetch the HTML content from the root directory of the website
            response = requests.get('http://192.168.0.100:8080/', timeout=5)
            if response.status_code != 200:
                print(f"Failed to fetch coordinates: HTTP {response.status_code}. Retrying...")
                time.sleep(0.5)
                continue

            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the element with coordinates - looking for various possible formats
            # First try to find a paragraph tag
            p_tag = soup.find('p')

            if p_tag and ',' in p_tag.text:
                coord_text = p_tag.text.strip()
            else:
                # If not in a p tag, try looking for div with id="coords" or "position"
                coord_div = soup.find('div', id=['coords', 'position'])
                if coord_div:
                    coord_text = coord_div.text.strip()
                    # Extract just the numbers if there's additional text
                    if 'Position:' in coord_text:
                        coord_text = coord_text.replace('Position:', '').strip()
                else:
                    print("Coordinates not found in the HTML. Retrying...")
                    time.sleep(0.1)
                    continue

            # Clean up and extract coordinates
            # Remove any non-numeric characters except for comma and period
            coord_text = ''.join(c for c in coord_text if c.isdigit() or c in '.,')
            coordinates = coord_text.split(',')

            if len(coordinates) != 2:
                print(f"Invalid coordinate format: {coord_text}. Retrying...")
                time.sleep(0.1)
                continue

            x, y = float(coordinates[0]), float(coordinates[1])
            current_pos = (x, y)
            print(f"Updated position: ({x}, {y})")

            # Brief pause before the next update
            time.sleep(0.1)

        except (requests.RequestException, ValueError) as e:
            print(f"Error fetching coordinates: {e}. Retrying...")
            time.sleep(1)

def move_forward(distance_inches):
    print("Moving forward: " + str(distance_inches))
    global current_pos, current_direction
    time_to_move = distance_inches * (TIME_PER_FOOT / 12)
    kit.motor1.throttle = -SPEED
    kit.motor2.throttle = SPEED
    time.sleep(time_to_move)
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0

    displacement = scale_vector(current_direction, distance_inches)
    current_pos = add_vectors(current_pos, displacement)
    update_position()

def turn_angle(angle_degrees):
    while True:
        print("Turning angle: " + str(angle_degrees))
        global current_direction
        turn_time = abs(angle_degrees) / DEGREES_PER_SECOND
        if angle_degrees > 0:
            kit.motor1.throttle = SPEED
            kit.motor2.throttle = SPEED
        else:
            kit.motor1.throttle = -SPEED
            kit.motor2.throttle = -SPEED
        time.sleep(turn_time)
        kit.motor1.throttle = 0
        kit.motor2.throttle = 0

        current_angle, magnitude = get_angle_and_magnitude(current_direction)
        new_angle = current_angle + angle_degrees
        current_direction = create_vector(new_angle, magnitude)



def adjust_heading(target_angle):
        global current_direction
        current_angle, _ = get_angle_and_magnitude(current_direction)
        angle_error = target_angle - current_angle

        if angle_error > 180:
            angle_error -= 360
        elif angle_error < -180:
            angle_error += 360
        print("flag1")
        turn_angle(angle_error)
        print("flag2")

def move_to_target(target):
    global current_pos, current_direction
    while True:
        update_position()
        target_vector = subtract_vectors(target, current_pos)
        distance = get_angle_and_magnitude(target_vector)[1]

        if distance <= POSITION_TOLERANCE:
            break
        else:
            move_forward(distance)
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0

def main():
    global current_pos, current_direction
    update_position()

    initial_pos = current_pos
    move_forward(10) # TODO CHECK TS
    displacement = subtract_vectors(current_pos, initial_pos)
    current_direction = create_vector(get_angle_and_magnitude(displacement)[0], 1.0)
    print("CurrentDirection: " + str(current_direction))

    for target in targets:
        print("Target: " + str(target))
        target_vector = subtract_vectors(target, current_pos)
        target_angle, _ = get_angle_and_magnitude(target_vector)
        adjust_heading(target_angle)
        move_to_target(target)


if __name__ == "__main__":
    main()