import os
import io
import pygame
import speech_recognition as sr
from elevenlabs import VoiceSettings, ElevenLabs
from dotenv import load_dotenv
from groq import Groq

# Load API keys
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Initialize Pygame Mixer for Audio Playback
pygame.mixer.init()

import json
from gpio_control import control_led  # Import GPIO function

def send_to_llm(text):
    print("Sending to LLM:", text)

    client = Groq(api_key=GROQ_API_KEY)

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": """you are a chill guy, your name is jarvis, Whenever user says look front, right or left just keep the conversation and say okay looking left or direction user says,
             act like a normal dude don't be robotic or AI or don't act like an assiatant"""},
            {"role": "user", "content": text},
        ],
        model="llama-3.3-70b-versatile",
    )

    response_text = chat_completion.choices[0].message.content
    print("LLM Response:", response_text)

    # **Check if response requires function calling**
    if "turn on led" in text.lower():
        result = control_led("on")
        return json.dumps(result)  # Return structured response

    elif "turn off led" in text.lower():
        result = control_led("off")
        return json.dumps(result)

    return response_text  # Default response if no LED control requested


def text_to_speech_and_play(text):
    """ Converts text to speech and plays it without saving to file """
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

    # Load the audio into memory instead of saving it to a file
    audio_data = io.BytesIO()
    for chunk in response:
        if chunk:
            audio_data.write(chunk)
    audio_data.seek(0)

    # Play audio directly from memory
    pygame.mixer.music.load(audio_data, "mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():  # Wait until speech finishes playing
        pygame.time.Clock().tick(10)

    print("Speech finished playing.")

# Initialize Speech Recognition
recognizer = sr.Recognizer()
mic = sr.Microphone()

# **Improve Speech Recognition Settings**
recognizer.dynamic_energy_threshold = True  # Automatically adjust for noise
recognizer.energy_threshold = 300  # Sensitivity for voice detection
recognizer.pause_threshold = 1.0  # Wait time after speech before processing (Default is 0.8, increased to 1.0)
recognizer.non_speaking_duration = 0.5  # Minimum silence time before ending capture

print("Listening... Speak now!")

while True:
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)  # Adjust for noise dynamically
        try:
            print("Waiting for speech...")
            audio_data = recognizer.listen(source, timeout=10, phrase_time_limit=15)  # Allow up to 15 seconds per speech
            print("Audio detected, processing...")

            # Recognize speech using Google Speech Recognition
            text = recognizer.recognize_google(audio_data)
            print("Recognized text:", text)

            # Send to LLM and play response
            llm_response = send_to_llm(text)
            text_to_speech_and_play(llm_response)

        except sr.WaitTimeoutError:
            print("Listening timeout reached. No speech detected.")
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service: {e}")
