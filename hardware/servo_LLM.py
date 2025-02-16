import os
import time
import io
import serial
import pygame
import speech_recognition as sr
from dotenv import load_dotenv
from groq import Groq
from elevenlabs import VoiceSettings, ElevenLabs
import re

# --------------------------
# Configuration
# --------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
pygame.mixer.init()

arduino_port = "/dev/ttyUSB0"  # Adjust to your system (e.g., "COM3" on Windows)
baud_rate = 9600

try:
    arduino_serial = serial.Serial(arduino_port, baud_rate, timeout=1)
    time.sleep(2)  # Wait for serial connection to initialize
except serial.SerialException:
    print("Failed to connect to Arduino.")
    arduino_serial = None

# --------------------------
# Helper Functions
# --------------------------

def send_command_to_arduino(command):
    """Send a command to the Arduino followed by a newline."""
    if arduino_serial:
        full_command = command + "\n"
        print(f"Sending command to Arduino: {full_command.strip()}")
        arduino_serial.write(full_command.encode())
        time.sleep(0.1)  # Brief pause to allow Arduino to process
    else:
        print("Arduino not connected. Skipping command.")

def get_llm_response(user_input):
    """
    Get conversational reply and servo command from LLM.
    """
    prompt = f"""You are an AI assistant controlling a servo motor. The user will provide simple commands to move the servo in one of four directions: 'left', 'right', 'back', or 'front'.

- The movement directions are as follows:
  - "left" -> Move the servo to the left position (e.g., 180 degrees)
  - "right" -> Move the servo to the right position (e.g., 0 degrees)
  - "back" -> Move the servo to the back position (e.g., 90 degrees)
  - "front" -> Move the servo to the front position (e.g., 90 degrees)

The assistant should:
- If the user gives a command to move the servo, return a command in the format:
  `CMD:POS:<angle>` where `<angle>` is the corresponding angle for the direction.
- If the user asks something unrelated, return `CMD:NO_COMMAND`.
- Always prioritize detecting **servo commands** based on these simple directions.

User input: "{user_input}"
Your reply:"""

    print("Sending to LLM:", user_input)
    client = Groq(api_key=GROQ_API_KEY)
    chat_completion = client.chat.completions.create(
        messages=[{"role": "system", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )

    response_text = chat_completion.choices[0].message.content.strip()
    print("LLM Response:\n", response_text)
    return response_text

def parse_llm_response(response_text):
    """
    Parse the LLM's response into a conversational reply and a servo command.
    """
    if "CMD:" not in response_text:
        return response_text, "CMD:NO_COMMAND"

    parts = response_text.split("CMD:")
    conversational_reply = parts[0].strip()
    command_line = "CMD:" + parts[1].strip()
    return conversational_reply, command_line

def parse_command(command_line):
    """
    Extract the servo command from the command line.
    """
    if command_line.startswith("CMD:POS:"):
        try:
            angle = int(command_line.split("CMD:POS:")[1])
            if 0 <= angle <= 180:
                return f"POS:{angle}"
        except ValueError:
            pass
    return None

def correct_speech_numbers(text):
    """
    Converts spoken numbers (e.g., 'one hundred' → '100') to digits.
    """
    text = text.lower()

    # Common misheard phrases to correct
    misheard_corrections = {
        "move the server": "move the servo",
        "move to ": "move servo to ",
    }

    for wrong, correct in misheard_corrections.items():
        text = text.replace(wrong, correct)

    # Extract numbers
    numbers = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
        "hundred": 100, "one hundred": 100, "one fifty": 150, "hundred eighty": 180,
    }

    for word, num in numbers.items():
        text = re.sub(rf'\b{word}\b', str(num), text)

    return text

def text_to_speech_and_play(text, servo_command):
    """ Convert text to speech and play it while executing servo command. """
    print("Converting text to speech...")

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

    # Save to temporary file
    temp_audio_file = "/tmp/speech.mp3"
    with open(temp_audio_file, "wb") as f:
        f.write(audio_data.getvalue())

    pygame.mixer.music.load(temp_audio_file)
    pygame.mixer.music.play()

    # Execute the servo command while speech is playing
    if servo_command:
        send_command_to_arduino(servo_command)

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    print("Speech finished playing.")

# --------------------------
# Speech Recognition Setup
# --------------------------
recognizer = sr.Recognizer()
mic = sr.Microphone()

print("Listening... Speak now!")

# --------------------------
# Main Function
# --------------------------

def main():
    try:
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)  # Reduce background noise
            while True:
                print("Waiting for voice command...")
                try:
                    audio_data = recognizer.listen(source, timeout=5)  # Wait for speech
                    print("Processing speech...")
                    user_input = recognizer.recognize_google(audio_data, language="en-US")
                    
                    # Fix misheard words & numbers
                    user_input = correct_speech_numbers(user_input)
                    print("Recognized text:", user_input)

                    if user_input.lower() in ["exit", "quit", "stop"]:
                        print("Exiting program...")
                        break

                    # Get response from LLM
                    llm_response = get_llm_response(user_input)
                    conversational_reply, command_line = parse_llm_response(llm_response)

                    # Print and play conversational reply while moving servo
                    print("\nLLM Conversational Reply:")
                    print(conversational_reply)

                    # Extract and send servo command while speaking
                    servo_command = parse_command(command_line)
                    text_to_speech_and_play(conversational_reply, servo_command)

                except sr.WaitTimeoutError:
                    print("Listening timeout reached. No speech detected.")
                except sr.UnknownValueError:
                    print("Sorry, I didn't catch that.")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service: {e}")

    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if arduino_serial:
            arduino_serial.close()
            print("Serial connection closed.")

if __name__ == "__main__":
    main()
