import adafruit_dht
import board
import time
from datetime import datetime

sensor = adafruit_dht.DHT11(board.D26)
log_file = "sensor_log.txt"

while True:
    try:
        temperature = sensor.temperature
        humidity = sensor.humidity
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Temperature: {temperature:.1f}°C  Humidity: {humidity:.1f}%\n"

        with open(log_file, "a") as file:
            file.write(log_entry)
    except RuntimeError as e:
        with open(log_file, "a") as file:
            file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Sensor error: {e}\n")

    time.sleep(0.1)
