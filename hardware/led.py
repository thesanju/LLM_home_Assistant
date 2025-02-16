import gpiod
import time

# Define the chip and line (pin) you want to use
chip = gpiod.Chip('gpiochip0')  # Use 'gpiochip0' for Raspberry Pi 4
led_line = chip.get_line(17)  # Use GPIO 17 (BCM numbering for physical pin 11)

# Request the line as an output
led_line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)

try:
    while True:
        led_line.set_value(1)  # Turn on
        time.sleep(1)          # Sleep for 1 second
        led_line.set_value(0)  # Turn off
        time.sleep(1)          # Sleep for 1 second
finally:
    # Clean up
    led_line.release()