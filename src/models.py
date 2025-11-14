from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

class PersonaType(Enum):
    TECHNICAL_EXPERT = "technical_expert"
    FRUSTRATED_USER = "frustrated_user"
    BUSINESS_EXEC = "business_exec"
    GENERAL = "general"

class EscalationLevel(Enum):
    NONE = "none"
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    MANAGER = "manager"

@dataclass
class CustomerPersona:
    persona_type: PersonaType
    confidence: float
    characteristics: Dict[str, Any]
    
    @property
    def is_frustrated(self) -> bool:
        return self.persona_type == PersonaType.FRUSTRATED_USER

@dataclass
class KnowledgeArticle:
    id: str
    title: str
    content: str
    persona_type: PersonaType
    tags: List[str]
    technical_level: int  # 1-5 scale

@dataclass
class ConversationContext:
    customer_id: str
    messages: List[Dict[str, str]]
    detected_persona: CustomerPersona
    escalation_level: EscalationLevel
    technical_complexity: int
    sentiment_score: float

@dataclass
class EscalationContact:
    name: str
    role: str
    expertise: List[str]
    email: str
    escalation_level: EscalationLevel