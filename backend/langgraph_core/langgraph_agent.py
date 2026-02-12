"""Production LangGraph Agent with State Machine"""
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

from .knowledge_base import get_knowledge_base
from .schemas import ConversationState, Intent, LeadData
from agent.monitoring import Monitor

load_dotenv()

class AgentGraphState(TypedDict):
    """State for LangGraph agent"""
    session_id: str
    transcript: str
    language: str
    intent: str
    confidence: float
    lead: dict
    context: str
    response: str
    next_action: str
    turn_count: int

class LangGraphAgent:
    """Production LangGraph agent with RAG"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.kb = get_knowledge_base()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine"""
        workflow = StateGraph(AgentGraphState)
        
        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("extract_lead_data", self._extract_lead_data)
        workflow.add_node("generate_response", self._generate_response)
        
        # Define edges
        workflow.set_entry_point("classify_intent")
        
        workflow.add_conditional_edges(
            "classify_intent",
            self._route_after_classification,
            {
                "retrieve": "retrieve_context",
                "extract": "extract_lead_data",
                "generate": "generate_response"
            }
        )
        
        workflow.add_edge("retrieve_context", "generate_response")
        workflow.add_edge("extract_lead_data", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _classify_intent(self, state: AgentGraphState) -> AgentGraphState:
        """Classify user intent using LLM"""
        transcript = state["transcript"]
        lead = state["lead"]
        
        # Use LLM to classify intent
        classification_prompt = f"""Classify the user's intent from their message.

User message: "{transcript}"

Lead status:
- Name: {lead.get('name') or 'Not provided'}
- Phone: {lead.get('phone') or 'Not provided'}
- Company: {lead.get('company') or 'Not provided'}
- Requirement: {lead.get('requirement') or 'Not provided'}

Classify as ONE of:
1. GREETING - if greeting or introducing themselves
2. OBJECTION - if declining or not interested
3. SERVICE_INQUIRY - if asking about services, features, pricing, timeline, or any question
4. LEAD_QUALIFICATION - if providing personal info (name, phone, company) or lead is incomplete

Return ONLY the classification (GREETING, OBJECTION, SERVICE_INQUIRY, or LEAD_QUALIFICATION)."""
        
        result = self.llm.invoke([HumanMessage(content=classification_prompt)])
        intent_raw = result.content.strip().upper()
        
        # Map to intent and action
        if "GREETING" in intent_raw:
            state["intent"] = "greeting"
            state["next_action"] = "generate"
        elif "OBJECTION" in intent_raw:
            state["intent"] = "objection"
            state["next_action"] = "generate"
        elif "SERVICE_INQUIRY" in intent_raw or "SERVICE" in intent_raw:
            state["intent"] = "service_inquiry"
            state["next_action"] = "retrieve"
        else:
            state["intent"] = "lead_qualification"
            state["next_action"] = "extract"
        
        state["confidence"] = 0.9
        return state
    
    def _route_after_classification(self, state: AgentGraphState) -> str:
        """Route based on intent"""
        return state["next_action"]
    
    def _retrieve_context(self, state: AgentGraphState) -> AgentGraphState:
        """Retrieve relevant context from knowledge base"""
        context = self.kb.get_context(state["transcript"])
        state["context"] = context
        Monitor.log_rag_retrieval(state["session_id"], state["transcript"], len(context))
        return state
    
    def _extract_lead_data(self, state: AgentGraphState) -> AgentGraphState:
        """Extract lead information from transcript"""
        lead = state["lead"]
        transcript = state["transcript"]
        
        # Determine what to extract
        if not lead.get("name"):
            # Extract name using LLM
            prompt = f"Extract the person's name from: '{transcript}'. Return ONLY the name or 'NONE'."
            result = self.llm.invoke([HumanMessage(content=prompt)])
            extracted = result.content.strip()
            if extracted != "NONE" and len(extracted) > 1:
                lead["name"] = extracted
        
        elif not lead.get("phone"):
            # Extract phone
            import re
            phone_match = re.search(r'\b\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', transcript)
            if phone_match:
                lead["phone"] = phone_match.group()
        
        elif not lead.get("company"):
            # Extract company
            prompt = f"Extract the company name from: '{transcript}'. Return ONLY the company name or 'NONE'."
            result = self.llm.invoke([HumanMessage(content=prompt)])
            extracted = result.content.strip()
            if extracted != "NONE" and len(extracted) > 1:
                lead["company"] = extracted
        
        elif not lead.get("requirement"):
            # Extract requirement
            lead["requirement"] = transcript
        
        state["lead"] = lead
        return state
    
    def _generate_response(self, state: AgentGraphState) -> AgentGraphState:
        """Generate response using LLM with context"""
        intent = state["intent"]
        language = state["language"]
        transcript = state["transcript"]
        
        # Greeting response
        if intent == "greeting":
            greetings = {
                "en": "Hi! I'm Riya from Synvolve Intellis. We help businesses with AI solutions. How can I help you today?",
                "ta": "வணக்கம்! நான் சின்வால்வ் இன்டெலிஸ் நிறுவனத்தின் ரியா. நாங்கள் வணிகங்களுக்கு AI தீர்வுகளை வழங்குகிறோம். இன்று உங்களுக்கு எப்படி உதவலாம்?",
                "hi": "नमस्ते! मैं सिनवॉल्व इंटेलिस की रिया हूं। हम व्यवसायों को AI समाधान प्रदान करते हैं। आज मैं आपकी कैसे मदद कर सकती हूं?"
            }
            state["response"] = greetings.get(language, greetings["en"])
            return state
        
        # Objection response
        if intent == "objection":
            objections = {
                "en": "No worries! Feel free to reach out anytime you need. Have a great day!",
                "ta": "பரவாயில்லை! தேவைப்படும்போது எப்போது வேண்டுமானாலும் தொடர்பு கொள்ளுங்கள். நல்ல நாள்!",
                "hi": "कोई बात नहीं! जब भी जरूरत हो संपर्क करें। आपका दिन शुभ हो!"
            }
            state["response"] = objections.get(language, objections["en"])
            return state
        
        # Build prompt with context
        system_prompt = f"""You are Riya, a friendly AI assistant from Synvolve Intellis.

IMPORTANT RULES:
- Respond ONLY in {language} language (English/Tamil/Hindi based on user's language)
- Be conversational, warm, and natural - like talking to a friend
- Keep responses under 30 words
- When listing services, present them clearly with numbers
- NO pricing details - say "Our team will provide a custom quote based on your needs"
- NO technical jargon - keep it simple and business-focused

COMPANY INFO:
Synvolve Intellis designs, builds, and operates AI-powered systems that help businesses run smarter and faster.

{state.get('context', '')}"""
        
        # Generate next question for lead qualification
        lead = state["lead"]
        if intent == "lead_qualification":
            if not lead.get("name"):
                user_prompt = f"User said: '{transcript}'\n\nRespond warmly and ask for their name in a friendly way."
            elif not lead.get("phone"):
                user_prompt = f"User said: '{transcript}'\n\nThank them by name and ask for their phone number naturally."
            elif not lead.get("company"):
                user_prompt = f"User said: '{transcript}'\n\nThank them and ask which company they're from."
            elif not lead.get("requirement"):
                user_prompt = f"User said: '{transcript}'\n\nAsk what AI solution or service they're interested in."
            else:
                user_prompt = f"Thank them warmly and say our team will contact them soon at their phone number."
        else:
            user_prompt = f"""User asked: '{transcript}'

Based on the context provided, give a helpful, conversational response. 
If listing services, format clearly with numbers (1, 2, 3...). 
End with a friendly question to continue the conversation."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        result = self.llm.invoke(messages)
        state["response"] = result.content.strip()
        
        return state
    
    def process(self, session_id: str, transcript: str, language: str, 
                lead_data: dict, turn_count: int) -> tuple[str, dict]:
        """Process conversation turn"""
        
        # Initialize state
        initial_state = AgentGraphState(
            session_id=session_id,
            transcript=transcript,
            language=language,
            intent="",
            confidence=0.0,
            lead=lead_data,
            context="",
            response="",
            next_action="",
            turn_count=turn_count
        )
        
        # Run graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state["response"], final_state["lead"]

# Singleton instance
_agent_instance = None

def get_langgraph_agent() -> LangGraphAgent:
    """Get or create agent singleton"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = LangGraphAgent()
    return _agent_instance
