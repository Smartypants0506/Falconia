import time
import requests
import csv
import os
import spidev
from adafruit_motorkit import MotorKit

# Initialize motor kit
kit = MotorKit()

# Rover-specific constants
SPEED = 0.75  # Default motor speed (-1.0 to 1.0)
STEP_TIME = 0.1  # Time per movement step (seconds)

# Camera server URLs (replace with your camera Pi's IP)
CAMERA_URL = 'http://192.168.0.103:12345'
FLASK_SERVER_URL = 'http://192.168.0.103:5000/get_markers'

# Sensor setup
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 4  # GPIO pin where the DHT11 is connected

# SPI setup for MCP3008 ADC
spi = spidev.SpiDev()
spi.open(0, 0)  # SPI bus 0, device 0
spi.max_speed_hz = 1350000  # SPI speed

# MQ2 sensor channel on the MCP3008
MQ2_CHANNEL = 0  # Analog channel for the MQ2 sensor

# Function to read ADC data from the MCP3008
def read_adc(channel):
    if channel < 0 or channel > 7:
        return -1  # Invalid channel
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

# Function to read gas level from the MQ2 sensor
def read_gas_level():
    return read_adc(MQ2_CHANNEL)

# Function to read sensor data
def read_sensor_data():
    humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
    gas_level = read_gas_level()
    return temperature, humidity, gas_level

# Function to fetch position data from the Flask server
def fetch_position_data():
    try:
        response = requests.get(FLASK_SERVER_URL)
        if response.status_code == 200:
            data = response.json()
            return data.get('center', {}).get('x'), data.get('center', {}).get('y')
        else:
            print(f"Failed to fetch position data: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Error fetching position data: {e}")
        return None, None

# Function to write data to CSV
def write_to_csv(center_x, center_y, temperature, humidity, gas_level):
    file_exists = os.path.isfile('sensor_data.csv')
    with open('sensor_data.csv', mode='a') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Center X', 'Center Y', 'Temperature', 'Humidity', 'Gas Level'])
        writer.writerow([center_x, center_y, temperature, humidity, gas_level])

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
    """Main control loop for autonomous navigation and data logging."""
    while True:
        # Get the action from the camera server
        action, distance, angle = get_action()

        # Log the action, distance, and angle for debugging
        print(f"Action: {action}, Distance: {distance}, Angle: {angle}")

        # Fetch position data from the Flask server
        center_x, center_y = fetch_position_data()

        if center_x is not None and center_y is not None:
            # Read sensor data
            temperature, humidity, gas_level = read_sensor_data()

            # Write data to CSV
            write_to_csv(center_x, center_y, temperature, humidity, gas_level)

            # Print data to console (for debugging)
            print(f"Position: ({center_x}, {center_y}), Temperature: {temperature}, Humidity: {humidity}, Gas Level: {gas_level}")

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