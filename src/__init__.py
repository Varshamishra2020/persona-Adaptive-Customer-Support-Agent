from .persona_detector import PersonaDetector
from .knowledge_base import KnowledgeBase
from .response_generator import ResponseGenerator
from .escalation_manager import EscalationManager
from .models import ConversationContext, CustomerPersona

class CustomerServiceAgent:
    def __init__(self):
        self.persona_detector = PersonaDetector()
        self.knowledge_base = KnowledgeBase()
        self.response_generator = ResponseGenerator()
        self.escalation_manager = EscalationManager()
        self.conversation_contexts = {}
    
    def process_message(self, customer_id: str, message: str) -> Dict:
        """Process customer message and return appropriate response"""
        # Get or create conversation context
        context = self.conversation_contexts.get(customer_id, ConversationContext(
            customer_id=customer_id,
            messages=[],
            detected_persona=CustomerPersona(
                persona_type='general',
                confidence=0.0,
                characteristics={}
            ),
            escalation_level='none',
            technical_complexity=1,
            sentiment_score=0.0
        ))
        
        # Add new message to context
        context.messages.append({'role': 'customer', 'content': message})
        
        # Detect persona
        persona = self.persona_detector.detect_persona(message, context.messages)
        context.detected_persona = persona
        
        # Update context metrics
        context.sentiment_score = persona.characteristics['sentiment_score']
        context.technical_complexity = int(persona.characteristics['technical_score'] * 5)
        
        # Check for escalation
        escalation_result = self.escalation_manager.should_escalate(context)
        
        # Search knowledge base
        articles = self.knowledge_base.search_articles(
            message, 
            persona.persona_type,
            technical_level=context.technical_complexity
        )
        
        # Generate response
        response = self.response_generator.generate_response(
            message,
            persona,
            articles,
            needs_escalation=escalation_result['needs_escalation']
        )
        
        # Prepare escalation data if needed
        escalation_data = None
        if escalation_result['needs_escalation']:
            escalation_contact = self.escalation_manager.get_escalation_contact(
                escalation_result['level'],
                ['technical' if context.technical_complexity > 3 else 'general']
            )
            
            escalation_data = {
                'level': escalation_result['level'].value,
                'reason': escalation_result['reason'],
                'contact': escalation_contact.name if escalation_contact else 'Senior Support',
                'context': self.escalation_manager.create_escalation_context(
                    context, escalation_result['reason']
                )
            }
            
            context.escalation_level = escalation_result['level']
        
        # Update context
        context.messages.append({'role': 'agent', 'content': response})
        self.conversation_contexts[customer_id] = context
        
        return {
            'response': response,
            'detected_persona': {
                'type': persona.persona_type.value,
                'confidence': round(persona.confidence, 2),
                'characteristics': persona.characteristics
            },
            'articles_used': [article.title for article in articles],
            'escalation': escalation_data,
            'technical_complexity': context.technical_complexity
        }
    
    def get_conversation_history(self, customer_id: str) -> List[Dict]:
        """Get conversation history for customer"""
        context = self.conversation_contexts.get(customer_id)
        return context.messages if context else []