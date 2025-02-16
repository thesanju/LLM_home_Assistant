import os
import io
import pygame
import speech_recognition as sr
from elevenlabs import VoiceSettings, ElevenLabs
from dotenv import load_dotenv
from groq import Groq

# Load API keys from .env file
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Initialize Pygame Mixer
pygame.mixer.init()

def send_to_llm(text):
    """ Sends text to the LLM and returns the response """
    print("Sending to LLM:", text)
    
    # Initialize Groq client
    client = Groq(api_key=GROQ_API_KEY)

    # Generate response
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": text},
        ],
        model="llama-3.3-70b-versatile",
    )

    response_text = chat_completion.choices[0].message.content
    print("LLM Response:", response_text)
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

    # Load the audio into memory instead of saving it to a file
    audio_data = io.BytesIO()
    for chunk in response:
        if chunk:
            audio_data.write(chunk)
    audio_data.seek(0)

    # Play audio directly from memory
    pygame.mixer.music.load(audio_data, "mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():  # Wait for the speech to finish playing
        pygame.time.Clock().tick(10)

    print("Speech finished playing.")

# Initialize Speech Recognition
recognizer = sr.Recognizer()
mic = sr.Microphone()

print("Listening... Speak now!")

while True:
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        try:
            audio_data = recognizer.listen(source)  # Listen for speech
            print("Audio detected, processing...")

            # Recognize speech using Google Speech Recognition
            text = recognizer.recognize_google(audio_data)
            print("Recognized text:", text)

            # Send text to LLM and get a response
            llm_response = send_to_llm(text)
            
            # Convert response to speech and play it
            text_to_speech_and_play(llm_response)

        except sr.WaitTimeoutError:
            print("Listening timeout reached. No speech detected.")
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service: {e}")

    # No need to prompt for user input, conversation continues automatically
