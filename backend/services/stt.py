from openai import OpenAI
from langdetect import detect, LangDetectException
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def speech_to_text(audio_path):
    """Use OpenAI Whisper for better accuracy"""
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        text = transcript.text.strip()
        if not text:
            raise Exception("UNSUPPORTED_LANGUAGE")
        
        # Detect language
        try:
            detected = detect(text)
            lang_map = {'en': 'en', 'ta': 'ta', 'hi': 'hi', 'te': 'te', 'kn': 'kn', 'ml': 'ml'}
            lang = lang_map.get(detected, 'en')
        except LangDetectException:
            lang = 'en'
        
        print(f"Whisper transcribed: {text} (lang: {lang})")
        return text, lang
        
    except Exception as e:
        print(f"Whisper error: {e}")
        # Fallback to Google Speech Recognition
        return _fallback_google_stt(audio_path)

def _fallback_google_stt(audio_path):
    """Fallback to Google STT if Whisper fails"""
    import speech_recognition as sr
    
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    
    with sr.AudioFile(audio_path) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.record(source)
    
    try:
        text = recognizer.recognize_google(audio, language='en-IN')
        if text and len(text.strip()) > 0:
            try:
                detected = detect(text)
                lang_map = {'en': 'en', 'ta': 'ta', 'hi': 'hi', 'te': 'te', 'kn': 'kn', 'ml': 'ml'}
                lang = lang_map.get(detected, 'en')
                return text, lang
            except LangDetectException:
                return text, 'en'
    except (sr.UnknownValueError, sr.RequestError):
        pass
    
    # Try other languages
    languages = [('ta-IN', 'ta'), ('hi-IN', 'hi')]
    for lang_code, lang_short in languages:
        try:
            text = recognizer.recognize_google(audio, language=lang_code)
            if text and len(text.strip()) > 0:
                return text, lang_short
        except (sr.UnknownValueError, sr.RequestError):
            continue
    
    raise Exception("UNSUPPORTED_LANGUAGE")