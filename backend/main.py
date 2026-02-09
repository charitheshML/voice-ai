from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
import os
import uuid
from services.stt import speech_to_text
from services.llm import ask_llm
from services.tts import text_to_speech
from database import init_db, get_db, Conversation
from sqlalchemy.orm import Session

app=FastAPI()

@app.on_event("startup")
def startup():
    init_db()

def cleanup_files(*files):
    for f in files:
        if os.path.exists(f):
            os.remove(f)

@app.post("/voice")
async def voice_handler(file:UploadFile=File(...), session_id:str=None, db:Session=Depends(get_db)):
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Create session folder
    session_folder = f"temp/{session_id}"
    os.makedirs(session_folder, exist_ok=True)
    
    # Count existing conversations for this session
    convo_count = db.query(Conversation).filter(Conversation.session_id == session_id).count() + 1
    
    temp_input = f"{session_folder}/{convo_count}_input.wav"
    temp_output = f"{session_folder}/{convo_count}_output.wav"
    
    try:
        #save the file
        audio_bytes = await file.read()
        with open(temp_input,"wb") as buffer:
            buffer.write(audio_bytes)

        #speech to text with language detection
        try:
            text, lang = speech_to_text(temp_input)
            print(f"Detected: {text} (lang: {lang})")
        except Exception as stt_error:
            if "UNSUPPORTED_LANGUAGE" in str(stt_error):
                # Language not supported - send message in English
                response = "Sorry, I don't know that language. I can help you with English, Tamil, or Hindi. Which language do you prefer?"
                text_to_speech(response, temp_output, 'en')
                return FileResponse(temp_output, media_type="audio/wav", headers={"X-Session-Id": session_id})
            else:
                raise stt_error
        
        #get previous user data from session
        last_convo = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).order_by(Conversation.created_at.desc()).first()
        
        user_data = {}
        if last_convo:
            user_data = {
                "name": last_convo.name,
                "phone": last_convo.phone,
                "company": last_convo.company,
                "requirements": last_convo.requirements
            }
        
        #llm with language context and user data
        response, updated_data = ask_llm(text, lang, user_data)
        print(f"Response: {response}")
        print(f"Updated data: {updated_data}")

        #text to speech in detected language
        text_to_speech(response, temp_output, lang)
        
        #save to database
        convo = Conversation(
            id=str(uuid.uuid4()),
            session_id=session_id,
            audio_data=audio_bytes,
            transcription=text,
            response=response,
            language=lang,
            name=updated_data.get("name"),
            phone=updated_data.get("phone"),
            company=updated_data.get("company"),
            requirements=updated_data.get("requirements")
        )
        db.add(convo)
        db.commit()
        print(f"Saved to DB: {convo.id}")
        print(f"Session folder: {session_folder}")

        return FileResponse(temp_output, media_type="audio/wav", headers={"X-Session-Id": session_id})
    except Exception as e:
        print(f"Error: {e}")
        cleanup_files(temp_input, temp_output)
        raise HTTPException(500, str(e))
