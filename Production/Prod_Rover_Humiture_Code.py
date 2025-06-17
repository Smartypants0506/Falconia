import csv
import time
import requests
import board
import adafruit_dht
import smbus
from datetime import datetime

# Constants
DHT_PIN = board.D26  # GPIO pin for DHT11
PCF8591_ADDRESS = 0x48  # Default I2C address of PCF8591
ADC_CHANNEL = 0  # MQ2 gas sensor connected to AIN0
JSON_URL = "http://192.168.0.100:5000/light_position"  # Replace with actual endpoint
CSV_FILE = "sensor_data.csv"

# Initialize DHT11 Sensor
dht_device = adafruit_dht.DHT11(DHT_PIN)

# Initialize I2C for PCF8591
bus = smbus.SMBus(1)  # Use I2C bus 1


def read_adc(channel):
    """Read analog value from PCF8591 ADC."""
    if not (0 <= channel <= 3):
        print("Invalid ADC channel")
        return None
    try:
        bus.write_byte(PCF8591_ADDRESS, channel)  # Select channel
        bus.read_byte(PCF8591_ADDRESS)  # Dummy read (needed for PCF8591)
        value = bus.read_byte(PCF8591_ADDRESS)  # Actual read
        return value
    except Exception as e:
        print(f"Error reading ADC: {e}")
        return None


def get_sensor_data():
    """Retrieve DHT11 and MQ2 sensor data."""
    try:
        temperature = dht_device.temperature
        humidity = dht_device.humidity
    except RuntimeError as e:
        print(f"DHT11 error: {e}")
        temperature, humidity = None, None

    gas_value = read_adc(ADC_CHANNEL)

    return temperature, humidity, gas_value


def fetch_json_data():
    """Fetch (x, y) coordinates from JSON endpoint."""
    try:
        response = requests.get(JSON_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        if "position" in data and isinstance(data["position"], list) and len(data["position"]) == 2:
            return data["position"][0], data["position"][1]
        else:
            print("Invalid JSON format")
            return None, None
    except requests.RequestException as e:
        print(f"Error fetching JSON: {e}")
        return None, None


def write_to_csv(data):
    """Write collected data to CSV."""
    file_exists = False
    try:
        with open(CSV_FILE, "r"):
            file_exists = True
    except FileNotFoundError:
        pass

    with open(CSV_FILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["Timestamp", "X", "Y", "Temperature (Â°C)", "Humidity (%)", "Gas Level"])
        writer.writerow(data)


def main():
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        x, y = fetch_json_data()
        temp, humidity, gas = get_sensor_data()

        if x is not None and y is not None:
            data = [timestamp, x, y, temp, humidity, gas]
            print("Logging data:", data)
            write_to_csv(data)

        time.sleep(0.1)  # Adjust as needed


if __name__ == "__main__":
    main()
