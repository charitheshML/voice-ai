from pydantic import BaseModel, Field, validator
from typing import Literal, Optional
from enum import Enum

class Intent(str, Enum):
    GREETING = "greeting"
    SERVICE_INQUIRY = "service_inquiry"
    LEAD_QUALIFICATION = "lead_qualification"
    OBJECTION = "objection"
    CLOSING = "closing"

class IntentClassification(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    entities: dict[str, str] = Field(default_factory=dict)
    
    @validator('confidence')
    def confidence_must_be_valid(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0 and 1')
        return v

class ExtractedField(BaseModel):
    field_name: str
    value: str
    confidence: float
    validated: bool = False
    
class LeadData(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    requirement: Optional[str] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError('Phone must contain only digits')
        if v and len(v) != 10:
            raise ValueError('Phone must be 10 digits')
        if v and not v[0] in '6789':
            raise ValueError('Invalid Indian mobile number')
        return v

class ConversationState(BaseModel):
    session_id: str
    language: Literal["en", "ta", "hi"] = "en"
    intent: Optional[Intent] = None
    lead: LeadData = Field(default_factory=LeadData)
    stage: Literal["greeting", "qualification", "information", "closing", "complete"] = "greeting"
    confidence: float = 0.0
    turn_count: int = 0
    topics_discussed: set[str] = Field(default_factory=set)
    
    class Config:
        use_enum_values = True
