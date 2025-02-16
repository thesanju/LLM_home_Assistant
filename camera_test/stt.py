import pyaudio
import wave
import whisper

# Initialize the Whisper model
model = whisper.load_model("base")

# Function to record audio
def record_audio(filename):
    p = pyaudio.PyAudio()

    # Try using a different sample rate, here using 44100 Hz as an example
    sample_rate = 44100  # Change this based on your system's supported sample rate
    
    try:
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, input=True, frames_per_buffer=1024)
    except IOError as e:
        print(f"Error opening stream: {e}")
        return

    print("Recording...")
    frames = []

    # Record for 5 seconds (you can change the duration as needed)
    for i in range(0, int(sample_rate / 1024 * 5)):  # Adjust to your desired duration
        data = stream.read(1024)
        frames.append(data)

    print("Recording finished.")
    
    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the audio to a file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

# Function to transcribe the audio file
def transcribe_audio(filename):
    print("Transcribing audio...")
    
    # Transcribe the recorded audio using Whisper
    result = model.transcribe(filename)
    
    # Print the transcribed text
    print(f"Transcription: {result['text']}")

# Main function to record and transcribe
def record_and_transcribe():
    audio_filename = "test.wav"
    
    # Record audio
    record_audio(audio_filename)
    
    # Transcribe audio
    transcribe_audio(audio_filename)

# Call the function to record and transcribe
if __name__ == "__main__":
    record_and_transcribe()
