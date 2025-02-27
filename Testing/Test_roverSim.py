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

# Targets (inverted y-axis: larger y = bottom)
targets = [(14.5, 16), (16.5, 16), (19.5,16),
           (22.5,16), (34,6), (38, 10.5),
           (46, 7.8), (53, 12), (59,13.5),
           (60.5,18.5)]
current_pos = [9.7, 12.5]  # Top-left
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
        self.theta = -math.pi / 2  # Facing up (smaller y)
        self.motor1_throttle = 0.0
        self.motor2_throttle = 0.0
        self.full_speed = (12 / TIME_PER_FOOT) / 10  # Slower speed
        self.full_turn_rate = math.radians(360 / TIME_PER_360) / 10  # Slower turn
        self.current_time = 0.0
        self.last_dx = 0.0
        self.last_dy = -1.0  # Default up

    def set_motor1_throttle(self, value):
        self.motor1_throttle = value
        #print(f"Set motor1 throttle: {value}")

    def set_motor2_throttle(self, value):
        self.motor2_throttle = value
        #print(f"Set motor2 throttle: {value}")

    def advance_time(self, dt):
        avg_throttle = (self.motor1_throttle + self.motor2_throttle) / 2
        diff_throttle = self.motor1_throttle - self.motor2_throttle
        v = avg_throttle * self.full_speed
        omega = diff_throttle * self.full_turn_rate / 2
        old_pos = self.position.copy()
        if abs(omega) < 1e-6:
            dx = v * math.cos(self.theta) * dt
            dy = v * math.sin(self.theta) * dt
            self.position[0] += dx
            self.position[1] += dy
            if dx != 0 or dy != 0:
                self.last_dx, self.last_dy = dx, dy
            print(f"Forward: v={v:.2f}, dx={dx:.2f}, dy={dy:.2f}, Pos: {self.position}")
        else:
            R = v / omega
            dtheta = omega * dt
            cx = self.position[0] - R * math.sin(self.theta)
            cy = self.position[1] + R * math.cos(self.theta)
            self.position[0] = cx + R * math.sin(self.theta + dtheta)
            self.position[1] = cy - R * math.cos(self.theta + dtheta)
            self.theta += dtheta
            dx = self.position[0] - old_pos[0]
            dy = self.position[1] - old_pos[1]
            if dx != 0 or dy != 0:
                self.last_dx, self.last_dy = dx, dy
            print(f"Turning: omega={omega:.2f}, dtheta={math.degrees(dtheta):.2f}, Pos: {self.position}")
        self.theta %= 2 * math.pi
        self.current_time += dt

    def get_current_pixel(self):
        real_point = np.array([[self.position]], dtype=np.float32)
        pixel_point = cv2.perspectiveTransform(real_point, M_inv)
        return (pixel_point[0][0][0], pixel_point[0][0][1])

    def get_current_direction(self):
        mag = math.hypot(self.last_dx, self.last_dy)
        if mag > 0:
            return [self.last_dx / mag, self.last_dy / mag]
        return [math.cos(self.theta), math.sin(self.theta)]

# PID Controller
class PIDController:
    def __init__(self, Kp=0.5, Ki=0.01, Kd=0.1, sample_time=0.1):
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
            print(f"PID too soon: dt={dt:.2f} < sample_time={self.sample_time}")
            return None
        P = self.Kp * error
        self.integral += error * dt
        I = self.Ki * self.integral
        D = 0 if self.previous_error is None else self.Kd * (error - self.previous_error) / dt
        self.previous_error = error
        self.last_time = current_time
        output = P + I + D
        print(f"PID: error={error:.2f}, P={P:.2f}, I={I:.2f}, D={D:.2f}, output={output:.2f}")
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
ax.set_title('Rover Simulation (Y Inverted: 0 at Top)')
ax.grid(True)
ax.invert_yaxis()

target_x, target_y = zip(*targets)
ax.plot(target_x, target_y, 'ro', label='Targets')
rover_dot, = ax.plot([sim.position[0]], [sim.position[1]], 'bo', label='Rover')
rover_arrow = ax.quiver([sim.position[0]], [sim.position[1]],
                        [sim.get_current_direction()[0]], [sim.get_current_direction()[1]],
                        color='blue', scale=20)
ax.legend()
plt.draw()

# Sliders
ax_kp = plt.axes([0.15, 0.01, 0.65, 0.03])
ax_ki = plt.axes([0.15, 0.05, 0.65, 0.03])
ax_kd = plt.axes([0.15, 0.09, 0.65, 0.03])
slider_kp = Slider(ax_kp, 'Kp', 0.0, 2.0, valinit=0.5)
slider_ki = Slider(ax_ki, 'Ki', 0.0, 0.1, valinit=0.01)
slider_kd = Slider(ax_kd, 'Kd', 0.0, 1.0, valinit=0.1)

slider_kp.on_changed(lambda val: setattr(pid_steering, 'Kp', val))
slider_ki.on_changed(lambda val: setattr(pid_steering, 'Ki', val))
slider_kd.on_changed(lambda val: setattr(pid_steering, 'Kd', val))

# Targets TextBox
ax_targets = plt.axes([0.15, 0.15, 0.65, 0.03])
text_box = TextBox(ax_targets, 'Targets (x,y;...)', initial='14.5,76;16.5,76')
text_box.on_submit(lambda text: update_targets(text))

def update_targets(text):
    global targets
    targets = [tuple(map(float, pair.split(','))) for pair in text.split(';')]
    target_x, target_y = zip(*targets)
    ax.clear()
    ax.set_xlim(0, MAP_WIDTH_INCHES)
    ax.set_ylim(0, MAP_HEIGHT_INCHES)
    ax.invert_yaxis()
    ax.grid(True)
    ax.plot(target_x, target_y, 'ro', label='Targets')
    ax.legend()
    fig.canvas.draw()

# GUI Update
def update_gui():
    rover_dot.set_data([sim.position[0]], [sim.position[1]])
    direction = sim.get_current_direction()
    rover_arrow.set_offsets([[sim.position[0], sim.position[1]]])
    rover_arrow.set_UVC([direction[0]], [direction[1]])
    print(f"GUI Update - Pos: {sim.position}, Theta: {math.degrees(sim.theta):.2f}, Dir: {direction}")
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.01)

# Simulate Sleep
def simulate_sleep(t):
    dt = 0.5  # Slower updates
    steps = int(t / dt)
    print(f"Simulate sleep: t={t:.2f}, steps={steps}")
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
    print(f"Update direction: old={old_pos}, new={new_pos}, dir={current_direction}")

def get_current_pixel():
    return sim.get_current_pixel()

def update_position():
    global current_pos
    current_pixel = get_current_pixel()
    current_pos = list(pixel_to_inches(current_pixel))
    print(f"Update position: {current_pos}")

def turn_to_angle(target_heading_deg):
    pid_steering.reset()
    ANGLE_TOLERANCE = 15.0
    last_throttle = 0.0
    TIME_STEP = 0.5
    print(f"Turning to: {target_heading_deg:.2f}")
    while True:
        update_position()
        current_direction = sim.get_current_direction()
        current_heading = math.degrees(math.atan2(current_direction[1], current_direction[0]))
        error = (target_heading_deg - current_heading) % 360
        if error > 180:
            error -= 360
        print(f"Current heading: {current_heading:.2f}, Error: {error:.2f}")
        if abs(error) < ANGLE_TOLERANCE:
            sim.set_motor1_throttle(0)
            sim.set_motor2_throttle(0)
            break
        pid_output = pid_steering.compute(error, sim.current_time)
        if pid_output is not None:
            last_throttle = pid_output
        throttle = max(min(last_throttle, 0.5), -0.5)
        sim.set_motor1_throttle(throttle)
        sim.set_motor2_throttle(-throttle)
        simulate_sleep(TIME_STEP)

def move_to_target(target_pos):
    POSITION_TOLERANCE = 3.0
    print(f"Move to target: {target_pos}")
    while True:
        update_position()
        dx = target_pos[0] - current_pos[0]
        dy = target_pos[1] - current_pos[1]
        distance = math.hypot(dx, dy)
        print(f"Distance: {distance:.2f}")
        if distance < POSITION_TOLERANCE:
            break
        target_heading = math.degrees(math.atan2(dy, dx))
        turn_to_angle(target_heading)
        sim.set_motor1_throttle(SPEED)
        sim.set_motor2_throttle(SPEED)
        simulate_sleep(distance * TIME_PER_FOOT / 12)
        sim.set_motor1_throttle(0)
        sim.set_motor2_throttle(0)
        new_pos = pixel_to_inches(get_current_pixel())
        update_direction_using_displacement(current_pos, new_pos)

# Main
def main():
    update_gui()
    for target in targets:
        print(f"Starting move to target: {target}")
        move_to_target(target)
    print("Simulation complete")

if __name__ == "__main__":
    main()
    plt.ioff()
    plt.show()