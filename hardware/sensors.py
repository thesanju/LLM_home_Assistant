import serial
import time
from datetime import datetime

# Configure the serial connection
ser = serial.Serial(
    port='/dev/ttyUSB0',  # Change this if needed
    baudrate=9600,
    timeout=1
)

def read_sensor_data():
    try:
        if ser.in_waiting > 0:
            # Read the line and decode it
            line = ser.readline().decode('utf-8').strip()
            
        # Only process the line if it's not empty and contains data
            if line and ',' in line:
                try:
                    # Parse the CSV data - now including air quality category
                    temp, humidity, gas_value, aqi, air_quality = line.split(',')
                    
                    # Convert numeric values
                    temp = float(temp)
                    humidity = float(humidity)
                    gas_value = float(gas_value)
                    aqi = float(aqi)
                    
                    # Get current timestamp
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Print formatted data
                    print(f"\nTime: {timestamp}")
                    print(f"Temperature: {temp}°C")
                    print(f"Humidity: {humidity}%")
                    print(f"Gas Sensor Value: {gas_value}")
                    print(f"AQI: {aqi}")
                    print(f"Air Quality: {air_quality}")
                    
                    # Save to file
                    with open('sensor_data.csv', 'a') as f:
                        f.write(f"{timestamp},{temp},{humidity},{gas_value},{aqi},{air_quality}\n")
                        
                except ValueError as ve:
                    # Print the problematic line for debugging
                    print(f"Skipping invalid data: {line}")
                    
    except Exception as e:
        print(f"Error: {e}")
and
def main():
    print("Starting sensor data collection...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            read_sensor_data()
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nStopping data collection...")
        ser.close()
        
if __name__ == "__main__":
    main()