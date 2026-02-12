from sqlalchemy.orm import Session
from database_v2 import Conversation
import uuid

SERVICES = {
    "riya": "Riya Voice Bot - AI-powered voice assistant for businesses with multilingual support",
    "website": "Website Development - Custom responsive websites tailored for your business",
    "synvoira": "Synvoira - Comprehensive AI solutions platform for business automation",
    "fitviora": "Fitviora - Advanced fitness and wellness solutions platform"
}

def save_lead(db: Session, session_id: str, audio_bytes: bytes, transcription: str, 
              response: str, language: str, name: str = None, phone: str = None, 
              company: str = None, requirement: str = None) -> str:
    """Save conversation and lead data to database"""
    convo = Conversation(
        id=str(uuid.uuid4()),
        session_id=session_id,
        audio_storage_key=f"{session_id}/{uuid.uuid4()}.wav",
        transcription=transcription,
        response=response,
        language=language,
        name=name,
        phone=phone,
        company=company,
        requirements=requirement
    )
    db.add(convo)
    db.commit()
    return convo.id

def get_service_info(service_name: str) -> str:
    """Get information about a specific service"""
    service_key = service_name.lower()
    for key, info in SERVICES.items():
        if key in service_key:
            return info
    return None

def list_all_services() -> str:
    """List all available services"""
    return "\n".join([f"{i+1}. {info}" for i, info in enumerate(SERVICES.values())])

def get_conversation_history(db: Session, session_id: str) -> dict:
    """Retrieve previous conversation data for session"""
    last_convo = db.query(Conversation).filter(
        Conversation.session_id == session_id
    ).order_by(Conversation.created_at.desc()).first()
    
    if last_convo:
        return {
            "name": last_convo.name,
            "phone": last_convo.phone,
            "company": last_convo.company,
            "requirement": last_convo.requirements,
            "language": last_convo.language
        }
    return {}
