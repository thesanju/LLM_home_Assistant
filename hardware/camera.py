import os

# Define the path where the image will be saved
image_path = "/home/pi/captured_image.jpg"

# Command to capture the image using fswebcam
command = f"fswebcam --no-banner -r 1280x720 {image_path}"

# Execute the command
os.system(command)

print(f"Photo captured and saved to {image_path}")