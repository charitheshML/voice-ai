from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
import os
import uuid
from services.stt import speech_to_text
from services.tts import text_to_speech
from services.audio_storage import AudioStorage
from database_v2 import get_db, Conversation
from agent.unified_agent import create_agent
from sqlalchemy.orm import Session

router = APIRouter()
audio_storage = AudioStorage("audio_storage")

@router.post("/voice")
async def voice_handler(file: UploadFile = File(...), session_id: str = None, db: Session = Depends(get_db)):
    if not session_id:
        session_id = str(uuid.uuid4())
    
    session_folder = f"temp/{session_id}"
    os.makedirs(session_folder, exist_ok=True)
    
    convo_count = db.query(Conversation).filter(Conversation.session_id == session_id).count() + 1
    temp_input = f"{session_folder}/{convo_count}_input.wav"
    temp_output = f"{session_folder}/{convo_count}_output.wav"
    
    try:
        audio_bytes = await file.read()
        with open(temp_input, "wb") as buffer:
            buffer.write(audio_bytes)
        
        audio_storage.save(session_id, audio_bytes, f"input_{convo_count}")

        try:
            text, lang = speech_to_text(temp_input)
            print(f"STT: {text} (lang: {lang})")
        except Exception as stt_error:
            if "UNSUPPORTED_LANGUAGE" in str(stt_error):
                response = "Sorry, I don't know that language. I can help you with English, Tamil, or Hindi."
                text_to_speech(response, temp_output, 'en')
                with open(temp_output, "rb") as f:
                    output_bytes = f.read()
                audio_storage.save(session_id, output_bytes, f"output_{convo_count}")
                return FileResponse(temp_output, media_type="audio/wav", headers={"X-Session-Id": session_id})
            else:
                raise stt_error
        
        # Use production RAG + LangGraph agent
        agent = create_agent(db)
        response, state = agent.process_conversation(session_id, text, lang, audio_bytes)
        
        print(f"Agent Response: {response}")
        print(f"Agent State: {state.dict()}")

        text_to_speech(response, temp_output, lang)
        
        with open(temp_output, "rb") as f:
            output_bytes = f.read()
        audio_storage.save(session_id, output_bytes, f"output_{convo_count}")

        return FileResponse(temp_output, media_type="audio/wav", headers={"X-Session-Id": session_id})
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(500, str(e))