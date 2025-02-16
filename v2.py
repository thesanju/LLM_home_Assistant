import os
import io
import json
import pygame
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

def load_memory():
    """Loads chat history from a file if it exists."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as file:
            return json.load(file)
    return [{"role": "system", "content": "You're Jarvis, a smart, intuitive, and friendly personal assistant. You can remember past conversations and also keep responses concise (10-15 words) and natural."}]

def save_memory(history):
    """Saves chat history to a file."""
    with open(MEMORY_FILE, "w") as file:
        json.dump(history, file)

# Load chat memory
history = load_memory()

def send_to_llm(text):
    global history  # Maintain memory of past messages

    print("Sending to LLM:", text)
    client = Groq(api_key=GROQ_API_KEY)
    
    # Add user input to history
    history.append({"role": "user", "content": text})
    
    # Generate response with full conversation history
    chat_completion = client.chat.completions.create(
        messages=history,
        model="llama-3.3-70b-versatile",
    )
    
    response_text = chat_completion.choices[0].message.content
    print("LLM Response:", response_text)
    
    # Add assistant response to history
    history.append({"role": "assistant", "content": response_text})
    save_memory(history)  # Save memory to file
    return response_text

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
    
    # Load audio into memory
    audio_data = io.BytesIO()
    for chunk in response:
        if chunk:
            audio_data.write(chunk)
    audio_data.seek(0)
    
    # Play audio directly from memory
    pygame.mixer.music.load(audio_data, "mp3")
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():  # Wait until speech finishes
        pygame.time.Clock().tick(10)
    
    print("Speech finished playing.")

# Initialize Speech Recognition
recognizer = sr.Recognizer()
mic = sr.Microphone()

print("Listening... Speak now!")

while True:
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)  # Adjust for background noise
        try:
            audio_data = recognizer.listen(source)  # Listen for speech
            print("Audio detected, processing...")

            # Recognize speech using Google Speech Recognition
            text = recognizer.recognize_google(audio_data)
            print("Recognized text:", text)

            # Send text to LLM and get response
            llm_response = send_to_llm(text)
            
            # Convert response to speech and play
            text_to_speech_and_play(llm_response)

        except sr.WaitTimeoutError:
            print("Listening timeout reached. No speech detected.")
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service: {e}")