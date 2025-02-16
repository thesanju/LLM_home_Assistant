import gpiod
import time

class LEDController:
    def __init__(self, gpio_chip='gpiochip0', gpio_pin=17):
        self.chip = gpiod.Chip(gpio_chip)
        self.led_line = self.chip.get_line(gpio_pin)
        self.led_line.request(consumer="LED", type=gpiod.LINE_REQ_DIR_OUT)

    def control_led(self, state: str):
        """Turn LED ON or OFF with proper error handling."""
        try:
            if state.lower() == "on":
                self.led_line.set_value(1)
                return {"status": "LED turned ON"}
            elif state.lower() == "off":
                self.led_line.set_value(0)
                return {"status": "LED turned OFF"}
            else:
                return {"error": "Invalid state. Use 'on' or 'off'."}
        except Exception as e:
            return {"error": f"GPIO Error: {e}"}

    def cleanup(self):
        """Release the GPIO line when done."""
        self.led_line.set_value(0)  # Ensure LED is off before releasing
        self.led_line.release()

# Initialize LED controller
led_controller = LEDController()

# Expose function for imports
def control_led(state):
    return led_controller.control_led(state)
