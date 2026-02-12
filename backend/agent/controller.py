"""Production Agent Controller with RAG + LangGraph"""
import time
from sqlalchemy.orm import Session
from typing import Tuple

from langgraph_core.langgraph_agent import get_langgraph_agent
from langgraph_core.schemas import ConversationState, LeadData
from .monitoring import Monitor, trace_function
from .tools import save_lead, get_conversation_history

class ProductionAgentController:
    """Production-ready controller with RAG + LangGraph orchestration"""
    
    def __init__(self, db: Session):
        self.db = db
        self.agent = get_langgraph_agent()
    
    @trace_function
    def load_state(self, session_id: str, language: str = "en") -> ConversationState:
        """Load conversation state from database"""
        history = get_conversation_history(self.db, session_id)
        
        # Count turns
        from database_v2 import Conversation
        turn_count = self.db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).count()
        
        return ConversationState(
            session_id=session_id,
            language=history.get("language", language) if history else language,
            lead=LeadData(
                name=history.get("name") if history else None,
                phone=history.get("phone") if history else None,
                company=history.get("company") if history else None,
                requirement=history.get("requirement") if history else None
            ),
            turn_count=turn_count
        )
    
    @trace_function
    def process(self, session_id: str, transcript: str, language: str, 
                audio_bytes: bytes) -> Tuple[str, ConversationState]:
        """Main processing pipeline with RAG + LangGraph"""
        start_time = time.time()
        
        try:
            # Load state
            state = self.load_state(session_id, language)
            state.turn_count += 1
            
            # Convert lead to dict for agent
            lead_dict = {
                "name": state.lead.name,
                "phone": state.lead.phone,
                "company": state.lead.company,
                "requirement": state.lead.requirement
            }
            
            # Process with LangGraph agent (includes RAG)
            response, updated_lead = self.agent.process(
                session_id=session_id,
                transcript=transcript,
                language=language,
                lead_data=lead_dict,
                turn_count=state.turn_count
            )
            
            # Update state with new lead data
            state.lead.name = updated_lead.get("name")
            state.lead.phone = updated_lead.get("phone")
            state.lead.company = updated_lead.get("company")
            state.lead.requirement = updated_lead.get("requirement")
            
            # Check completion
            if all([state.lead.name, state.lead.phone, state.lead.company, state.lead.requirement]):
                state.stage = "complete"
                Monitor.log_lead_completion(session_id, state.turn_count, language)
            
            # Save to database
            save_lead(
                self.db, session_id, audio_bytes, transcript, response, language,
                state.lead.name, state.lead.phone, state.lead.company, state.lead.requirement
            )
            
            # Log metrics
            latency_ms = (time.time() - start_time) * 1000
            Monitor.log_interaction(
                session_id, state.turn_count, transcript, response,
                state.intent.value if state.intent else "unknown",
                state.confidence, language, latency_ms
            )
            
            # Alerts
            if latency_ms > 3000:
                Monitor.alert("MEDIUM", f"High latency: {latency_ms:.0f}ms", 
                            {"session_id": session_id})
            
            return response, state
            
        except Exception as e:
            Monitor.alert("HIGH", f"Processing failed: {str(e)}", 
                        {"session_id": session_id, "transcript": transcript})
            
            # Fallback response
            fallback = {
                "en": "I'm having trouble. Could you repeat that?",
                "ta": "எனக்கு சிக்கல் உள்ளது. மீண்டும் சொல்ல முடியுமா?",
                "hi": "मुझे समस्या हो रही है। क्या आप दोहरा सकते हैं?"
            }
            
            state = self.load_state(session_id, language)
            return fallback.get(language, fallback["en"]), state
