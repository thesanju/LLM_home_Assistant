from picamera import PiCamera
from time import sleep

# Initialize the camera
camera = PiCamera()

# Optional: Set resolution (default is the camera's maximum resolution)
camera.resolution = (1920, 1080)

# Warm-up time for the camera
sleep(2)

# Capture a photo and save it
camera.capture('/home/pi/image.jpg')
print("Photo captured and saved as image.jpg")
