import cv2
import time
from groq import Groq

# Initialize Groq client
client = Groq()

def capture_image(image_path="captured_image.jpg"):
    """Captures an image using the webcam and saves it."""
    cap = cv2.VideoCapture(0)  # Open default camera (0)
    time.sleep(2)  # Allow camera to warm up
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(image_path, frame)
        print("Image captured successfully.")
    else:
        print("Failed to capture image.")
    cap.release()
    return image_path if ret else None

def chat_or_vision(user_input):
    """Decides whether to use vision or chat model based on user query."""
    
    # Keywords that imply vision-related questions
    vision_keywords = ["see", "what's in front", "look at", "describe this scene"]

    if any(keyword in user_input.lower() for keyword in vision_keywords):
        print("User asked for vision capabilities. Capturing image...")
        image_path = capture_image()
        
        if image_path:
            model = "llama-3.2-11b-vision-preview"
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe what you see in this image."},
                        {"type": "image_url", "image_url": {"url": f"file://{image_path}"}}
                    ]
                }
            ]
        else:
            return "Sorry, I couldn't capture an image."

    else:
        # Use chat model for text-only queries
        model = "llama-3.3-70b-versatile"
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
        ]

    # Make API call
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.5,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
        stop=None,
    )

    return completion.choices[0].message.content

# Example Usage
print(chat_or_vision("Can you see what's in front of you?"))  # This should trigger image capture
print(chat_or_vision("Explain the importance of AI."))  # This should use chat model
