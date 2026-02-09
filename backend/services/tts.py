from gtts import gTTS


LANG_MAP = {
    'en': 'en',
    'ta': 'ta',
    'hi': 'hi'
}

def text_to_speech(text, out_path, lang='en'):
    tts_lang = LANG_MAP.get(lang, 'en')
    tts = gTTS(text=text, lang=tts_lang)
    tts.save(out_path)