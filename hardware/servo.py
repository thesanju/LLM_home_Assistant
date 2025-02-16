import serial
import time

class ServoController:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        self.serial = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset
        
    def move_servo(self, angle):
        if 0 <= angle <= 180:
            command = f"{angle}\n"
            self.serial.write(command.encode())
            time.sleep(0.1)  # Give servo time to move
        else:
            print("Angle must be between 0 and 180 degrees")
            
    def close(self):
        self.serial.close()

def main():
    try:
        # Initialize servo controller
        servo = ServoController()  # Change port if needed
        print("Servo Controller initialized")
        print("Enter angles between 0-180, or 'q' to quit")
        
        while True:
            user_input = input("Enter angle (0-180): ")
            
            if user_input.lower() == 'q':
                break
                
            try:
                angle = int(user_input)
                servo.move_servo(angle)
            except ValueError:
                print("Please enter a valid number between 0 and 180")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'servo' in locals():
            servo.close()

if __name__ == "__main__":
    main()