import time
import curses
from adafruit_motorkit import MotorKit

# Initialize the motor hat
kit = MotorKit()

# Configuration
MAX_SPEED = 1.0  # Maximum throttle (range: 0 to 1)
ACCELERATION_STEP = 0.05  # How fast it speeds up
DECELERATION_STEP = 0.05  # Ensure both motors decelerate at the same rate
UPDATE_RATE = 0.05  # Update interval (lower = smoother, higher = more responsive)

# Current speed levels
motor1_speed = 0.0
motor2_speed = 0.0

def motor_control(stdscr):
    global motor1_speed, motor2_speed
    curses.cbreak()
    curses.halfdelay(1)  # Reduce delay for key holds (1 = 100ms)
    stdscr.nodelay(True)  # Do not block waiting for user input
    stdscr.keypad(True)
    stdscr.clear()
    stdscr.addstr("Use arrow keys to control motors. Press 'q' to exit.\n")

    while True:
        key = stdscr.getch()

        # Determine target speeds
        if key == curses.KEY_UP:
            kit.motor1.throttle = 0.75
            kit.motor2.throttle = 0.75
            motor1_speed = 0.75
            motor2_speed = 0.75
        elif key == curses.KEY_DOWN:
            kit.motor1.throttle = -0.75
            kit.motor2.throttle = -0.75
            motor1_speed = -0.75
            motor2_speed = -0.75
        elif key == curses.KEY_LEFT:
            kit.motor1.throttle = 1
            kit.motor2.throttle = -1
            motor1_speed = 1
            motor2_speed = -1
        elif key == curses.KEY_RIGHT:
            kit.motor1.throttle = -1
            kit.motor2.throttle = 1
            motor1_speed = -1
            motor2_speed = 1
        else:
            kit.motor1.throttle = 0
            kit.motor2.throttle = 0
            motor1_speed = 0
            motor2_speed = 0

        # Display status
        stdscr.clear()
        stdscr.addstr("Use arrow keys to control motors. Press 'q' to exit.\n")
        stdscr.addstr(f"Motor 1 Speed: {motor1_speed}\n")
        stdscr.addstr(f"Motor 2 Speed: {motor2_speed}\n")
        stdscr.refresh()

        # Exit on 'q' key
        if key == ord('q'):
            break

        time.sleep(UPDATE_RATE)

    # Ensure motors fully stop when exiting
    kit.motor1.throttle = 0
    kit.motor2.throttle = 0

if __name__ == "__main__":
    curses.wrapper(motor_control)