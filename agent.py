import sounddevice as sd 
import soundfile as sf
import requests 
import os
import numpy as np

SAMPLE_RATE = 16000
API_URL = "http://localhost:8000/voice"

os.makedirs("temp", exist_ok=True)

# Fix macOS audio issues
sd.default.device = None  # Use default device
sd.default.channels = 1
sd.default.samplerate = SAMPLE_RATE

print("🎙️  Voice AI Agent - Riya")
print("=" * 40)

while True:
    input("Press ENTER to start recording...")
    print("🔴 Recording... (Press ENTER to stop)")

    import threading
    recording = []
    is_recording = True
    
    def record():
        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32', blocksize=1024) as stream:
                while is_recording:
                    data, _ = stream.read(1024)
                    recording.append(data)
        except Exception as e:
            print(f"Recording error: {e}")
    
    thread = threading.Thread(target=record)
    thread.start()
    input()
    is_recording = False
    thread.join()
    
    print("⏹️  Recording complete")

    if not recording:
        print("⚠️  No audio recorded. Try again.")
        continue

    audio = np.concatenate(recording, axis=0)
    sf.write("temp/input.wav", audio, SAMPLE_RATE)

    print("🤖 Processing with AI...")

    try:
        with open("temp/input.wav", "rb") as f:
            response = requests.post(API_URL, files={"file": ("input.wav", f, "audio/wav")})

        if response.status_code == 200:
            with open("temp/output.wav", "wb") as f:
                f.write(response.content)
            print("🔊 Playing AI response...")

            try:
                audio_out, sr = sf.read("temp/output.wav")
                sd.play(audio_out, sr, blocking=True)
                print("✅ Audio playback complete")
            except Exception as audio_error:
                print(f"Audio playback error: {audio_error}")
                print("💡 Try: brew install portaudio && pip install --upgrade sounddevice")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 40)