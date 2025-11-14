import json
import os
from typing import List, Optional, Dict
from .models import EscalationLevel, EscalationContact, CustomerPersona, ConversationContext

class EscalationManager:
    def __init__(self, contacts_path: str = "data/escalation_contacts.json"):
        self.contacts_path = contacts_path
        self.contacts: List[EscalationContact] = self._load_contacts()
    
    def _load_contacts(self) -> List[EscalationContact]:
        """Load escalation contacts"""
        if os.path.exists(self.contacts_path):
            with open(self.contacts_path, 'r') as f:
                contacts_data = json.load(f)
                return [EscalationContact(**contact) for contact in contacts_data]
        return []
    
    def should_escalate(self, context: ConversationContext) -> Dict:
        """Determine if escalation is needed and to what level"""
        escalation_reason = None
        escalation_level = EscalationLevel.NONE
        
        # Check frustration level
        if context.detected_persona.is_frustrated:
            if context.sentiment_score < -0.7:
                escalation_level = EscalationLevel.MANAGER
                escalation_reason = "Highly frustrated customer requiring executive attention"
            elif context.sentiment_score < -0.4:
                escalation_level = EscalationLevel.TIER_2
                escalation_reason = "Frustrated customer needing specialized support"
        
        # Check technical complexity
        if context.technical_complexity >= 4 and escalation_level.value < EscalationLevel.TIER_2.value:
            escalation_level = EscalationLevel.TIER_2
            escalation_reason = "Highly technical issue requiring expert support"
        
        # Check for repeated issues (simplified)
        if len(context.messages) > 5 and any('issue' in msg.get('content', '').lower() for msg in context.messages[-3:]):
            if escalation_level.value < EscalationLevel.TIER_1.value:
                escalation_level = EscalationLevel.TIER_1
                escalation_reason = "Persistent issue requiring dedicated attention"
        
        return {
            'needs_escalation': escalation_level != EscalationLevel.NONE,
            'level': escalation_level,
            'reason': escalation_reason
        }
    
    def get_escalation_contact(self, level: EscalationLevel, expertise: List[str] = None) -> Optional[EscalationContact]:
        """Get appropriate escalation contact"""
        suitable_contacts = [c for c in self.contacts if c.escalation_level == level]
        
        if expertise and suitable_contacts:
            # Find contact with matching expertise
            for contact in suitable_contacts:
                if any(exp in contact.expertise for exp in expertise):
                    return contact
        
        return suitable_contacts[0] if suitable_contacts else None
    
    def create_escalation_context(self, context: ConversationContext, 
                                escalation_reason: str) -> Dict:
        """Create context package for escalation handoff"""
        return {
            'customer_id': context.customer_id,
            'persona_type': context.detected_persona.persona_type.value,
            'conversation_summary': self._summarize_conversation(context.messages),
            'escalation_reason': escalation_reason,
            'technical_complexity': context.technical_complexity,
            'sentiment_analysis': context.sentiment_score,
            'key_issues': self._extract_key_issues(context.messages),
            'recommended_approach': self._get_recommended_approach(context.detected_persona)
        }
    
    def _summarize_conversation(self, messages: List[Dict]) -> str:
        """Create conversation summary for handoff"""
        customer_messages = [msg for msg in messages if msg.get('role') == 'customer']
        if customer_messages:
            last_three = customer_messages[-3:]
            return " | ".join([msg.get('content', '')[:100] for msg in last_three])
        return "No customer messages recorded"
    
    def _extract_key_issues(self, messages: List[Dict]) -> List[str]:
        """Extract key issues from conversation"""
        issues = set()
        for msg in messages:
            content = msg.get('content', '').lower()
            if 'not working' in content:
                issues.add('Functionality issue')
            if 'error' in content:
                issues.add('System error')
            if 'how to' in content:
                issues.add('Guidance needed')
            if 'price' in content or 'cost' in content:
                issues.add('Pricing inquiry')
        return list(issues)
    
    def _get_recommended_approach(self, persona: CustomerPersona) -> str:
        """Get recommended approach based on persona"""
        if persona.is_frustrated:
            return "Focus on empathy and immediate solution delivery"
        elif persona.persona_type.value == 'technical_expert':
            return "Provide detailed technical specifications and options"
        elif persona.persona_type.value == 'business_exec':
            return "Focus on business value and strategic implications"
        return "Standard supportive approach"