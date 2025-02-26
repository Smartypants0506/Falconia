import math
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, TextBox

# Constants
MAP_WIDTH_INCHES = 142
MAP_HEIGHT_INCHES = 92
SPEED = 0.75
TIME_PER_360 = 1.6
TIME_PER_FOOT = 0.54

# Initial state
targets = [(14.5, 16), (16.5, 16), (19.5, 16), (22.5, 16), (34, 16),
           (38, 10.5), (46, 7.8), (53, 12), (59, 13.5), (60.5, 18.5)]
current_pos = [9.7, 12.5]
current_direction = [0.0, 1.0]

# Perspective transform
real_corners = np.array([[0, 0], [MAP_WIDTH_INCHES, 0], [0, MAP_HEIGHT_INCHES], [MAP_WIDTH_INCHES, MAP_HEIGHT_INCHES]], dtype=np.float32)
pixel_corners = np.array([(58, 23), (760, 23), (58, 469), (760, 469)], dtype=np.float32)
M = cv2.getPerspectiveTransform(pixel_corners, real_corners)
M_inv = np.linalg.inv(M)

# Rover Simulation
class RoverSimulation:
    def __init__(self):
        self.position = [9.7, 12.5]
        self.theta = math.pi / 2
        self.motor1_throttle = 0.0
        self.motor2_throttle = 0.0
        self.full_speed = 12 / TIME_PER_FOOT
        self.full_turn_rate = math.radians(360 / TIME_PER_360)
        self.current_time = 0.0

    def set_motor1_throttle(self, value):
        self.motor1_throttle = value

    def set_motor2_throttle(self, value):
        self.motor2_throttle = value

    def advance_time(self, dt):
        avg_throttle = (self.motor1_throttle + self.motor2_throttle) / 2
        diff_throttle = self.motor1_throttle - self.motor2_throttle
        v = avg_throttle * self.full_speed
        omega = diff_throttle * self.full_turn_rate / 2
        if abs(omega) < 1e-6:
            dx = v * math.cos(self.theta) * dt
            dy = v * math.sin(self.theta) * dt
            self.position[0] += dx
            self.position[1] += dy
            print(f"Forward: v={v:.2f}, dx={dx:.2f}, dy={dy:.2f}")
        else:
            R = v / omega
            dtheta = omega * dt
            cx = self.position[0] - R * math.sin(self.theta)
            cy = self.position[1] + R * math.cos(self.theta)
            self.position[0] = cx + R * math.sin(self.theta + dtheta)
            self.position[1] = cy - R * math.cos(self.theta + dtheta)
            self.theta += dtheta
            print(f"Turning: omega={omega:.2f}, dtheta={math.degrees(dtheta):.2f}")
        self.theta %= 2 * math.pi
        self.current_time += dt

    def get_current_pixel(self):
        real_point = np.array([[self.position]], dtype=np.float32)
        pixel_point = cv2.perspectiveTransform(real_point, M_inv)
        return (pixel_point[0][0][0], pixel_point[0][0][1])

# PID Controller
class PIDController:
    def __init__(self, Kp=1.0, Ki=0.1, Kd=0.05, sample_time=0.1):
        self.Kp, self.Ki, self.Kd = Kp, Ki, Kd
        self.sample_time = sample_time
        self.output_limits = (-1, 1)
        self.reset()

    def reset(self):
        self.integral = 0
        self.previous_error = None
        self.last_time = 0.0

    def compute(self, error, current_time):
        dt = current_time - self.last_time
        if dt < self.sample_time:
            return None
        P = self.Kp * error
        self.integral += error * dt
        I = self.Ki * self.integral
        D = 0 if self.previous_error is None else self.Kd * (error - self.previous_error) / dt
        self.previous_error = error
        self.last_time = current_time
        output = P + I + D
        return max(self.output_limits[0], min(output, self.output_limits[1]))

# Initialize
sim = RoverSimulation()
pid_steering = PIDController()

# GUI Setup
plt.ion()
fig, ax = plt.subplots(figsize=(10, 8))
ax.set_xlim(0, MAP_WIDTH_INCHES)
ax.set_ylim(0, MAP_HEIGHT_INCHES)
ax.set_xlabel('X (inches)')
ax.set_ylabel('Y (inches)')
ax.set_title('Rover Simulation')
ax.grid(True)

target_x, target_y = zip(*targets)
ax.plot(target_x, target_y, 'ro', label='Targets')
rover_dot, = ax.plot([sim.position[0]], [sim.position[1]], 'bo', label='Rover')
rover_arrow = ax.quiver([sim.position[0]], [sim.position[1]],
                        [math.cos(sim.theta)], [math.sin(sim.theta)],
                        color='blue', scale=20)
ax.legend()
plt.draw()

# Sliders and TextBox (simplified)
ax_kp = plt.axes([0.15, 0.01, 0.65, 0.03])
slider_kp = Slider(ax_kp, 'Kp', 0.0, 2.0, valinit=1.0)
slider_kp.on_changed(lambda val: setattr(pid_steering, 'Kp', val))

ax_targets = plt.axes([0.15, 0.15, 0.65, 0.03])
text_box = TextBox(ax_targets, 'Targets', initial='14.5,16;16.5,16')
text_box.on_submit(lambda text: update_targets(text))

def update_targets(text):
    global targets
    targets = [tuple(map(float, pair.split(','))) for pair in text.split(';')]
    target_x, target_y = zip(*targets)
    ax.plot(target_x, target_y, 'ro')
    fig.canvas.draw()

# GUI Update
def update_gui():
    rover_dot.set_data([sim.position[0]], [sim.position[1]])
    rover_arrow.set_offsets([[sim.position[0], sim.position[1]]])
    rover_arrow.set_UVC([math.cos(sim.theta)], [math.sin(sim.theta)])
    print(f"GUI Update - Pos: {sim.position}, Theta: {math.degrees(sim.theta)}")
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.01)

# Simulate Sleep
def simulate_sleep(t):
    dt = 0.1
    steps = int(t / dt)
    for _ in range(steps):
        sim.advance_time(dt)
        update_gui()
    remaining = t % dt
    if remaining > 0:
        sim.advance_time(remaining)
        update_gui()

# Helper Functions
def pixel_to_inches(pixel_point):
    px = np.array([[pixel_point]], dtype=np.float32)
    transformed = cv2.perspectiveTransform(px, M)
    return (transformed[0][0][0], transformed[0][0][1])

def update_direction_using_displacement(old_pos, new_pos):
    global current_direction
    dx = new_pos[0] - old_pos[0]
    dy = new_pos[1] - old_pos[1]
    if dx != 0 or dy != 0:
        heading = math.atan2(dy, dx)
        current_direction = [math.cos(heading), math.sin(heading)]

def get_current_pixel():
    return sim.get_current_pixel()

def update_position():
    global current_pos
    current_pixel = get_current_pixel()
    current_pos = list(pixel_to_inches(current_pixel))

def turn_to_angle(target_heading_deg):
    pid_steering.reset()
    ANGLE_TOLERANCE = 15.0
    last_throttle = 0.0
    TIME_STEP = 0.1
    while True:
        update_position()
        current_heading = math.degrees(math.atan2(current_direction[1], current_direction[0]))
        error = (target_heading_deg - current_heading) % 360
        if error > 180:
            error -= 360
        if abs(error) < ANGLE_TOLERANCE:
            sim.set_motor1_throttle(0)
            sim.set_motor2_throttle(0)
            break
        pid_output = pid_steering.compute(error, sim.current_time)
        if pid_output is not None:
            last_throttle = pid_output
        sim.set_motor1_throttle(last_throttle)
        sim.set_motor2_throttle(-last_throttle)
        simulate_sleep(TIME_STEP)
        new_pos = pixel_to_inches(get_current_pixel())
        update_direction_using_displacement(current_pos, new_pos)

def move_to_target(target_pos):
    POSITION_TOLERANCE = 3.0
    while True:
        update_position()
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]
        distance = math.hypot(dx, dy)
        if distance < POSITION_TOLERANCE:
            break
        target_heading = math.degrees(math.atan2(dy, dx))
        turn_to_angle(target_heading)
        sim.set_motor1_throttle(SPEED)
        sim.set_motor2_throttle(SPEED)
        simulate_sleep(distance * TIME_PER_FOOT / 12)
        sim.set_motor1_throttle(0)
        sim.set_motor2_throttle(0)

# Main
def main():
    update_gui()  # Show initial state
    for target in targets:
        print(f"Moving to target: {target}")
        move_to_target(target)
    print("Simulation complete")

if __name__ == "__main__":
    main()
    plt.ioff()
    plt.show()