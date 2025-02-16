import os
import uuid
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from groq import Groq
import pygame
import speech_recognition as sr

# Load environment variables from .env file
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

def send_to_llm(text):
    print("Sending to LLM: ", text)

    # Initialize Groq client
    client = Groq(
        api_key=os.getenv("GROQ_API_KEY"),
    )

    # Create chat completion with Groq model
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "you are a chill guy, and your name is jarvis, act like a normal dude don't be robotic or AI or don't act like an assiatant and respond with less than 20 words"
            },
            {
                "role": "user",
                "content": text,
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    # Print the LLM response
    print(chat_completion.choices[0].message.content)
    return chat_completion.choices[0].message.content

def text_to_speech_file(text: str) -> str:
    # Calling the text_to_speech conversion API with detailed parameters
    print("Converting text to speech...")
    response = client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",  # Adam pre-made voice
        output_format="mp3_22050_32",    # Set output format to MP3 (lower quality for faster processing)
        text=text,
        model_id="eleven_turbo_v2_5",    # Use the turbo model for low latency
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    # Generating a unique file name for the output MP3 file
    save_file_path = f"{uuid.uuid4()}.mp3"

    # Writing the audio to a file by iterating through response chunks
    with open(save_file_path, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)

    print(f"{save_file_path}: A new audio file was saved successfully!")

    # Initialize pygame mixer
    pygame.mixer.init()

    # Load the audio file
    pygame.mixer.music.load(save_file_path)

    # Play the audio
    pygame.mixer.music.play()

    # Wait for the music to finish before continuing
    while pygame.mixer.music.get_busy():  # While the music is playing
        pygame.time.Clock().tick(10)

    print("Speech finished playing.")

    # Return the path of the saved audio file
    return save_file_path

# Function to listen to the microphone and get speech-to-text
recognizer = sr.Recognizer()
mic = sr.Microphone()

LISTEN_TIMEOUT = 30
SILENCE_THRESHOLD = 300

print("Listening... Speak now!")

while True:
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)  # Adjust for ambient noise
        try:
            audio_data = recognizer.listen(source, timeout=LISTEN_TIMEOUT, phrase_time_limit=LISTEN_TIMEOUT)
            print("Audio detected, processing...")

            # Recognize speech using Google speech recognition
            text = recognizer.recognize_google(audio_data)
            print("Recognized text:", text)

            # Send the recognized text to the LLM and also convert it to speech
            llm_response = send_to_llm(text)  # You can send the recognized text to the LLM here
            text_to_speech_file(llm_response)  # Respond with text-to-speech

        except sr.WaitTimeoutError:
            print("Listening timeout reached. No speech detected.")
        except sr.UnknownValueError:
            print("Sorry, I didn't catch that.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")


