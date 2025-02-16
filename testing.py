import os
import io
import json
import pygame
import serial
import time
from datetime import datetime
import speech_recognition as sr
from dotenv import load_dotenv
from groq import Groq
from elevenlabs import VoiceSettings, ElevenLabs

# Load API keys from .env file
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Initialize Pygame Mixer
pygame.mixer.init()

MEMORY_FILE = "chat_memory.json"

# Initialize global history
history = []

class EnvironmentController:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        self.serial = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset
        self.latest_sensor_data = None
        
    def read_sensor_data(self):
        try:
            if self.serial.in_waiting > 0:
                line = self.serial.readline().decode('utf-8').strip()
                if line and ',' in line:
                    temp, humidity, gas_value, aqi, air_quality = line.split(',')
                    self.latest_sensor_data = {
                        'temperature': float(temp),
                        'humidity': float(humidity),
                        'gas_value': float(gas_value),
                        'aqi': float(aqi),
                        'air_quality': air_quality
                    }
                    return self.latest_sensor_data
        except Exception as e:
            print(f"Error reading sensor data: {e}")
        return None

    def move_servo(self, angle):
        if 0 <= angle <= 180:
            command = f"{angle}\n"
            self.serial.write(command.encode())
            time.sleep(0.1)
            print(f"Moving servo to {angle} degrees")
        else:
            print("Angle must be between 0 and 180 degrees")

    def close(self):
        self.serial.close()

def load_memory():
    """Loads chat history from a file if it exists and is valid."""
    initial_history = [{
        "role": "system",
        "content": """You are JARVIS, an advanced AI assistant with a personality inspired by Tony Stark's JARVIS. 
        You're witty, intelligent, and helpful while maintaining a slight touch of dry humor. You engage in natural 
        conversation on any topic, just like a knowledgeable friend would.

        You have access to environmental data through sensors and can control a servo motor using natural commands:
        - "turn left" or "left" moves to 0 degrees
        - "turn right" or "right" moves to 180 degrees
        - "center" or "middle" moves to 90 degrees
        - Specific angles can be set with commands like "turn to 45 degrees"
        - when user says to turn, just turn and don't talk BS or just say okay

        When discussing sensor data or controlling the servo, maintain your conversational tone. For example:
        - For temperature: "The room's quite comfortable at 25 degrees, sir/madam"
        - For servo: "Rotating to the left position for you, sir/madam"
        - For air quality: "The air quality is excellent, though humidity is a bit high"

        Keep responses concise and natural, respond under 10-15 words, acknowledging commands and actions taken.
        """
    }]

    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as file:
                loaded_history = json.load(file)
                if isinstance(loaded_history, list) and loaded_history:
                    return loaded_history
    except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
        print(f"Warning: Could not load chat history ({str(e)}). Starting fresh.")
        
    # If anything goes wrong or file doesn't exist, create new file with initial history
    with open(MEMORY_FILE, "w") as file:
        json.dump(initial_history, file)
    
    return initial_history

def save_memory(history):
    """Saves chat history to a file."""
    with open(MEMORY_FILE, "w") as file:
        json.dump(history, file)

def extract_servo_command(text):
    """Extract servo angle from text, including directional commands."""
    text = text.lower()
    words = text.split()
    
    # Handle directional commands
    directional_mapping = {
        "left": 180,
        "right": 0,
        "center": 90,
        "middle": 90,
        "straight": 90,
        "forward": 90
    }
    
    # First check for directional commands
    for word in words:
        if word in directional_mapping:
            return directional_mapping[word]
    
    # Then check for explicit angle numbers
    try:
        for i, word in enumerate(words):
            if any(keyword in word for keyword in ["servo", "move", "turn", "rotate"]):
                for j in range(i, min(i + 3, len(words))):
                    if words[j].isdigit():
                        angle = int(words[j])
                        if 0 <= angle <= 180:
                            return angle
    except:
        pass
    
    return None

def detect_environment_query(text):
    """Detect if the query is related to environmental data or servo control."""
    env_keywords = ["temperature", "humidity", "air quality", "aqi", "gas", "environment", "room"]
    servo_keywords = ["servo", "move", "turn", "left", "right", "rotate", "position", "angle", 
                     "center", "middle", "straight", "forward"]
    
    text_lower = text.lower()
    is_env_query = any(keyword in text_lower for keyword in env_keywords)
    is_servo_query = any(keyword in text_lower for keyword in servo_keywords)
    
    return is_env_query, is_servo_query

def send_to_llm(text, sensor_data=None, servo_moved=False, servo_angle=None):
    global history
    
    # Only add sensor data context if it's an environmental query
    is_env_query, is_servo_query = detect_environment_query(text)
    
    if is_env_query and sensor_data:
        # Add sensor data as a system message right before the user's query
        history.append({
            "role": "system",
            "content": f"Current sensor readings: Temperature: {sensor_data['temperature']}°C, "
                      f"Humidity: {sensor_data['humidity']}%, AQI: {sensor_data['aqi']}, "
                      f"Air Quality: {sensor_data['air_quality']}"
        })
    
    if servo_moved and servo_angle is not None:
        # Add servo movement confirmation as system message
        history.append({
            "role": "system",
            "content": f"Servo has been moved to {servo_angle} degrees."
        })
    
    # Add user input to history
    history.append({"role": "user", "content": text})
    
    # Generate response with conversation history
    client = Groq(api_key=GROQ_API_KEY)
    chat_completion = client.chat.completions.create(
        messages=history,
        model="llama-3.3-70b-versatile",
    )
    
    response_text = chat_completion.choices[0].message.content
    print("JARVIS Response:", response_text)
    
    # Add assistant response to history
    history.append({"role": "assistant", "content": response_text})
    save_memory(history)
    
    return response_text

def text_to_speech_and_play(text):
    print("Converting to speech...")
    
    response = elevenlabs_client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",  # Adam's voice
        output_format="mp3_22050_32", 
        text=text,
        model_id="eleven_turbo_v2_5", 
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )
    
    audio_data = io.BytesIO()
    for chunk in response:
        if chunk:
            audio_data.write(chunk)
    audio_data.seek(0)
    
    pygame.mixer.music.load(audio_data, "mp3")
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

def main():
    global history
    
    # Initialize history at startup
    history = load_memory()
    
    # Initialize components
    controller = EnvironmentController()
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    print("JARVIS: At your service. How may I assist you today?")
    
    try:
        while True:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                try:
                    # Listen for speech
                    audio_data = recognizer.listen(source)
                    text = recognizer.recognize_google(audio_data)
                    print("You:", text)
                    
                    # Read sensor data only if needed
                    is_env_query, is_servo_query = detect_environment_query(text)
                    sensor_data = controller.read_sensor_data() if is_env_query else None
                    
                    # Handle servo control if requested
                    servo_moved = False
                    servo_angle = None
                    if is_servo_query:
                        servo_angle = extract_servo_command(text)
                        if servo_angle is not None:
                            controller.move_servo(servo_angle)
                            servo_moved = True
                    
                    # Get JARVIS response
                    response = send_to_llm(text, sensor_data, servo_moved, servo_angle)
                    
                    # Convert response to speech and play
                    text_to_speech_and_play(response)
                    
                except sr.UnknownValueError:
                    print("JARVIS: I didn't quite catch that. Could you please repeat?")
                except sr.RequestError as e:
                    print(f"JARVIS: I'm having trouble with speech recognition: {e}")
                
    except KeyboardInterrupt:
        print("\nJARVIS: Shutting down. Goodbye!")
    finally:
        controller.close()

if __name__ == "__main__":
    main()