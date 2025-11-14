from typing import List, Dict
from .models import CustomerPersona, PersonaType, KnowledgeArticle

class ResponseGenerator:
    def __init__(self):
        self.tone_templates = {
            PersonaType.TECHNICAL_EXPERT: {
                'greeting': "I understand you're looking for technical details.",
                'explanation': "Here's the technical implementation:",
                'closing': "Let me know if you need more technical specifics.",
                'style': 'precise, detailed, technical'
            },
            PersonaType.BUSINESS_EXEC: {
                'greeting': "I appreciate you reaching out about this business matter.",
                'explanation': "From a business perspective:",
                'closing': "I'm happy to discuss the business implications further.",
                'style': 'strategic, high-level, value-focused'
            },
            PersonaType.FRUSTRATED_USER: {
                'greeting': "I understand this is frustrating and I'm here to help resolve this.",
                'explanation': "Let me help you fix this:",
                'closing': "I'll personally ensure this gets resolved for you.",
                'style': 'empathetic, reassuring, solution-oriented'
            },
            PersonaType.GENERAL: {
                'greeting': "Thanks for reaching out! I'm here to help.",
                'explanation': "Here's what I can tell you:",
                'closing': "Hope this helps! Let me know if you have other questions.",
                'style': 'friendly, clear, helpful'
            }
        }
    
    def generate_response(self, query: str, persona: CustomerPersona, 
                         articles: List[KnowledgeArticle], 
                         needs_escalation: bool = False) -> str:
        """Generate persona-appropriate response"""
        template = self.tone_templates[persona.persona_type]
        
        if needs_escalation:
            return self._generate_escalation_response(persona, template)
        
        # Build response with appropriate tone
        response_parts = []
        
        # Greeting
        response_parts.append(template['greeting'])
        
        # Main content from knowledge articles
        if articles:
            response_parts.append(template['explanation'])
            for i, article in enumerate(articles, 1):
                response_parts.append(f"\n{i}. {article.title}")
                response_parts.append(self._adapt_content(article.content, persona))
        else:
            response_parts.append("I don't have specific information on that, but here's what I can suggest:")
            response_parts.append(self._provide_general_guidance(query, persona))
        
        # Closing
        response_parts.append(f"\n{template['closing']}")
        
        return "\n".join(response_parts)
    
    def _adapt_content(self, content: str, persona: CustomerPersona) -> str:
        """Adapt content to match persona preferences"""
        if persona.persona_type == PersonaType.TECHNICAL_EXPERT:
            # Keep technical details
            return content
        elif persona.persona_type == PersonaType.BUSINESS_EXEC:
            # Simplify technical jargon, focus on outcomes
            simplified = content.replace("API", "system connection")
            simplified = simplified.replace("integration", "connection")
            simplified = simplified.replace("deployment", "setup")
            return f"Key point: {simplified.split('.')[0]}. This helps streamline your business processes."
        elif persona.persona_type == PersonaType.FRUSTRATED_USER:
            # Focus on immediate solutions and reassurance
            return f"To resolve this quickly: {content.split('.')[0]}. I'll guide you through each step."
        else:
            # General - balanced approach
            return content
    
    def _provide_general_guidance(self, query: str, persona: CustomerPersona) -> str:
        """Provide general guidance when no specific articles are found"""
        base_guidance = "I recommend checking our documentation or contacting support for specific details."
        
        if persona.persona_type == PersonaType.FRUSTRATED_USER:
            return f"I understand this is important. {base_guidance} I've flagged this as priority."
        elif persona.persona_type == PersonaType.BUSINESS_EXEC:
            return f"For business-critical matters, {base_guidance} Our team can provide ROI analysis."
        else:
            return base_guidance
    
    def _generate_escalation_response(self, persona: CustomerPersona, template: Dict) -> str:
        """Generate response when escalation is needed"""
        if persona.persona_type == PersonaType.FRUSTRATED_USER:
            return (f"{template['greeting']}\n\n"
                   "I'm escalating this to our senior support team who will provide immediate assistance. "
                   "They'll contact you within the hour with a solution.\n\n"
                   "Thank you for your patience - we'll get this sorted out for you.")
        else:
            return (f"{template['greeting']}\n\n"
                   "I'm connecting you with a specialist who has deeper expertise in this area. "
                   "They'll be able to provide the comprehensive support you need.\n\n"
                   f"{template['closing']}")