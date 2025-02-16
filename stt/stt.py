import pyaudio
import logging
import threading
import time
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

# Your Deepgram API key
API_KEY = "damn it"  # <-- Update this with your API key

# WebSocket URL
URL = "wss://api.deepgram.com/v1/listen"

# Audio configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 512  # Lower chunk size to avoid overflow
BUFFER_SIZE = 2048  # Increase buffer size for better handling

def on_message(self, result, **kwargs):
    """Callback to handle transcribed messages."""
    sentence = result.channel.alternatives[0].transcript
    if sentence:
        print(f"Transcribed: {sentence}")

def start_audio_stream():
    """Captures real-time audio and sends it to Deepgram."""
    audio = pyaudio.PyAudio()
    
    device_index = 1
    # Open microphone stream
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=CHUNK)

    return stream, audio

def main():
    try:
        # Initialize Deepgram client with API key
        deepgram = DeepgramClient(api_key=API_KEY)

        # Create a WebSocket connection
        dg_connection = deepgram.listen.websocket.v("1")

        # Attach the message handler to the WebSocket connection
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        # Set WebSocket options
        options = LiveOptions(model="nova-2")

        # Start WebSocket connection
        if not dg_connection.start(options):
            print("Failed to start connection")
            return

        print("\n\nRecording... Press Enter to stop\n\n")

        # Capture and stream audio
        stream, audio = start_audio_stream()

        # Create a worker thread to send audio data to the WebSocket
        def audio_thread():
            while True:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    dg_connection.send(data)
                except IOError as e:
                    print(f"Audio error: {e}")
                    break
                except Exception as e:
                    print(f"Error while sending audio data: {e}")
                    break


        # Start audio capture in a separate thread
        worker_thread = threading.Thread(target=audio_thread)
        worker_thread.start()

        # Wait for user input to stop recording
        input("\nPress Enter to stop recording...\n")

        # Stop streaming
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Close the WebSocket connection
        dg_connection.finish()

        print("Finished")

    except Exception as e:
        print(f"Error: {e}")
        return

if __name__ == "__main__":
    main()
