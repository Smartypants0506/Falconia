import adafruit_dht
import board
import time

# Define sensor type and GPIO pin
sensor = adafruit_dht.DHT11(board.D26)  # Change to your GPIO pin

while True:
    try:
        temperature = sensor.temperature
        humidity = sensor.humidity
        print(f"Temperature: {temperature:.1f}°C  Humidity: {humidity:.1f}%")
    except RuntimeError as e:
        print(f"Sensor error: {e}")

    time.sleep(0.1)  # Wait 2 seconds before next reading
