import speech_recognition as sr

def speech_to_text(audio_path):
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    
    with sr.AudioFile(audio_path) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.record(source)
    
    
    languages = [
        ('en-IN', 'en'),
        ('ta-IN', 'ta'),
        ('hi-IN', 'hi')
    ]
    
    for lang_code, lang_short in languages:
        try:
            text = recognizer.recognize_google(audio, language=lang_code)
            if text and len(text.strip()) > 0:
                print(f"Detected language: {lang_short}")
                return text, lang_short
        except sr.UnknownValueError:
            continue
        except sr.RequestError as e:
            print(f"API error: {e}")
            continue
    
    raise Exception("UNSUPPORTED_LANGUAGE")