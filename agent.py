import sounddevice as sd 
import soundfile as sf
import requests 
import os

SAMPLE_RATE = 16000
API_URL = "http://localhost:8000/voice"

os.makedirs("temp", exist_ok=True)

print("🎙️  Voice AI Agent - Riya")
print("=" * 40)

while True:
    input("Press ENTER to start recording...")
    print("🔴 Recording... (Press ENTER to stop)")

    import threading
    recording = []
    is_recording = True
    
    def record():
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
            while is_recording:
                data, _ = stream.read(1024)
                recording.append(data)
    
    thread = threading.Thread(target=record)
    thread.start()
    input()
    is_recording = False
    thread.join()
    
    print("⏹️  Recording complete")

    import numpy as np
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

            audio_out, sr = sf.read("temp/output.wav")
            sd.play(audio_out, sr)
            sd.wait()
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 40)