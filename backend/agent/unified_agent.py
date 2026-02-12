"""Unified Agent Interface - Production Entry Point"""
from sqlalchemy.orm import Session
from typing import Tuple

from .controller import ProductionAgentController
from langgraph_core.schemas import ConversationState

class UnifiedAgent:
    """
    Production-ready unified agent interface.
    Uses RAG + LangGraph orchestration for intelligent conversation handling.
    """
    
    def __init__(self, db: Session):
        self.controller = ProductionAgentController(db)
    
    def process_conversation(
        self, 
        session_id: str, 
        transcript: str, 
        language: str = "en",
        audio_bytes: bytes = b""
    ) -> Tuple[str, ConversationState]:
        """
        Process a conversation turn with RAG-enhanced responses.
        
        Args:
            session_id: Unique session identifier
            transcript: User's speech transcription
            language: Language code (en, ta, hi)
            audio_bytes: Audio data for storage
            
        Returns:
            Tuple of (response_text, updated_state)
        """
        return self.controller.process(session_id, transcript, language, audio_bytes)
    
    def get_state(self, session_id: str, language: str = "en") -> ConversationState:
        """Get current conversation state"""
        return self.controller.load_state(session_id, language)

def create_agent(db: Session) -> UnifiedAgent:
    """Factory function to create agent instance"""
    return UnifiedAgent(db)
