"""Production RAG Knowledge Base with Vector Store"""
from typing import List, Dict
from dataclasses import dataclass
import os

@dataclass
class Document:
    content: str
    metadata: Dict[str, str]
    embedding: List[float] = None

class KnowledgeBase:
    """In-memory vector store for company knowledge"""
    
    COMPANY_DOCS = [
        # Products
        {
            "content": """Synviora: An integrated business management platform that combines CRM, HRMS, payroll, and financial management into one unified system.
It helps organizations manage customer relationships, handle employee records, automate payroll processing, track salaries and financial data, 
manage attendance and leave, and maintain financial transparency. Suitable for small businesses, medium enterprises, and corporate organizations.""",
            "metadata": {"category": "product", "product_type": "synviora", "keywords": "synviora,crm,hrms,payroll,finance,business,management,platform"}
        },
        {
            "content": """Fitviora: A gym management platform designed for gym owners and fitness studios. It allows gym owners to manage memberships, 
handle subscriptions and payments, provide personalized fitness suggestions, and track trainers and members. 
Deployment options: Gym owners can publish using their own custom domain (additional cost) or use our organization's domain. 
Fitviora simplifies gym operations and improves member engagement.""",
            "metadata": {"category": "product", "product_type": "fitviora", "keywords": "fitviora,gym,fitness,membership,subscription,trainer"}
        },
        
        # Services
        {
            "content": """Voice Bots: AI-powered conversational systems that understand user questions in real-time audio and respond in natural voice. 
Support continuous conversations and provide organization-specific answers. Suitable for customer support, sales inquiries, internal assistance, 
and 24/7 virtual voice automation. Allow hands-free, natural interaction tailored to your organization.""",
            "metadata": {"category": "service", "service_type": "voice_bot", "keywords": "voice,bot,audio,conversation,call,speak,talk,24/7"}
        },
        {
            "content": """Chatbots: AI-powered text-based assistants that allow users to ask questions via chat and get real-time responses. 
Use organization-specific knowledge and can be deployed on websites and digital platforms. 
Help automate support, improve engagement, and reduce manual workload.""",
            "metadata": {"category": "service", "service_type": "chatbot", "keywords": "chatbot,chat,text,message,website,support"}
        },
        {
            "content": """AI Strategy & Consulting: We analyze your business operations to identify where AI can create real impact. 
Focus on business outcomes, not just technology. Create AI roadmaps and guide implementation.""",
            "metadata": {"category": "service", "service_type": "consulting", "keywords": "strategy,consulting,roadmap,analyze,business"}
        },
        {
            "content": """Custom AI Development: We design and develop AI-first products tailored to your needs - including intelligent chatbots, 
voice assistants, recommendation engines, internal automation tools, and intelligent platforms.""",
            "metadata": {"category": "service", "service_type": "development", "keywords": "custom,development,build,product,ai"}
        },
        {
            "content": """Business Process Automation: We automate repetitive tasks, workflows, and manual operations including data entry, 
document processing, email responses, and workflow orchestration to reduce human effort, errors, and operational costs.""",
            "metadata": {"category": "service", "service_type": "automation", "keywords": "automation,workflow,process,repetitive,tasks"}
        },
        {
            "content": """System Integration: We connect AI systems with your existing tools like CRMs, ERPs, WhatsApp, websites, 
and internal dashboards to ensure seamless operations and data flow.""",
            "metadata": {"category": "service", "service_type": "integration", "keywords": "integration,crm,erp,api,connect,whatsapp"}
        },
        {
            "content": """Performance Optimization & Scaling: We continuously monitor, improve, and scale AI systems to match business growth. 
We improve accuracy, reduce latency, and scale infrastructure.""",
            "metadata": {"category": "service", "service_type": "optimization", "keywords": "performance,scaling,optimization,monitor,improve"}
        },
        {
            "content": """Security & Compliance: We ensure every system is secure, reliable, and designed with data privacy and business continuity in mind. 
Enterprise-grade security, GDPR compliance, and 99.9% uptime SLAs.""",
            "metadata": {"category": "service", "service_type": "security", "keywords": "security,compliance,privacy,gdpr,reliable"}
        },
        {
            "content": """Long-Term Partnership: We work as a strategic partner supporting clients beyond launch with continuous improvements, 
insights, and future-ready AI solutions. We help businesses move faster with confidence.""",
            "metadata": {"category": "service", "service_type": "partnership", "keywords": "partnership,support,maintenance,long-term"}
        },
        
        # Overview
        {
            "content": """Synvolve Intellis Overview: We design, build, and operate AI-powered systems.

Our Products: 1) Synviora - Business management platform (CRM, HRMS, Payroll, Finance) 2) Fitviora - Gym management platform

Our Services: 1) Voice Bots - AI voice assistants 2) Chatbots - Text-based AI assistants 3) AI Strategy & Consulting 
4) Custom AI Development 5) Business Process Automation 6) System Integration 7) Performance Optimization 8) Security & Compliance 9) Long-Term Partnership""",
            "metadata": {"category": "overview", "keywords": "services,products,all,what,offer,do,about,company,synvolve"}
        },
        {
            "content": "Pricing is customized based on project scope, complexity, and business needs. Our team provides detailed quotes after understanding your requirements.",
            "metadata": {"category": "pricing", "keywords": "price,cost,quote,budget,how much"}
        },
        {
            "content": "Implementation timelines vary by project complexity. Typical projects range from 4-12 weeks. We provide detailed timelines during consultation.",
            "metadata": {"category": "timeline", "keywords": "timeline,duration,time,when,how long"}
        }
    ]
    
    def __init__(self):
        self.documents = [Document(**doc) for doc in self.COMPANY_DOCS]
        self._build_index()
    
    def _build_index(self):
        """Build keyword index for fast retrieval"""
        self.keyword_index = {}
        for idx, doc in enumerate(self.documents):
            keywords = doc.metadata.get("keywords", "").split(",")
            for kw in keywords:
                kw = kw.strip().lower()
                if kw not in self.keyword_index:
                    self.keyword_index[kw] = []
                self.keyword_index[kw].append(idx)
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Document]:
        """Retrieve relevant documents using keyword matching"""
        query_lower = query.lower()
        scores = {}
        
        # Score documents by keyword matches
        for keyword, doc_indices in self.keyword_index.items():
            if keyword in query_lower:
                for idx in doc_indices:
                    scores[idx] = scores.get(idx, 0) + 1
        
        # Get top-k documents
        if not scores:
            # Fallback: return service overview docs
            return [self.documents[i] for i in range(min(3, len(self.documents)))]
        
        top_indices = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]
        return [self.documents[idx] for idx in top_indices]
    
    def get_context(self, query: str) -> str:
        """Get formatted context for LLM"""
        docs = self.retrieve(query, top_k=2)
        context = "\n\n".join([f"- {doc.content}" for doc in docs])
        return f"Relevant Information:\n{context}"

# Singleton instance
_kb_instance = None

def get_knowledge_base() -> KnowledgeBase:
    """Get or create knowledge base singleton"""
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = KnowledgeBase()
    return _kb_instance
