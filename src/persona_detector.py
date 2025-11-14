import re
from typing import Dict, List
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from .models import CustomerPersona, PersonaType

class PersonaDetector:
    def __init__(self):
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        self.technical_keywords = [
            'api', 'integration', 'sdk', 'documentation', 'debug', 'log', 
            'endpoint', 'authentication', 'deployment', 'configuration',
            'script', 'code', 'technical', 'implementation', 'architecture'
        ]
        self.business_keywords = [
            'roi', 'business', 'strategy', 'enterprise', 'scalability',
            'cost', 'budget', 'efficiency', 'productivity', 'workflow',
            'kpi', 'metrics', 'revenue', 'growth', 'competitive'
        ]
        self.frustration_indicators = [
            'frustrated', 'angry', 'annoyed', 'disappointed', 'upset',
            'not working', 'broken', 'failed', 'issue', 'problem',
            'urgent', 'immediately', 'help now', 'terrible', 'awful'
        ]
        
    def detect_persona(self, message: str, conversation_history: List[Dict]) -> CustomerPersona:
        """Detect customer persona from message and history"""
        message_lower = message.lower()
        
        # Analyze sentiment
        sentiment_result = self.sentiment_analyzer(message)[0]
        sentiment_score = sentiment_result['score'] if sentiment_result['label'] == 'POSITIVE' else -sentiment_result['score']
        
        # Calculate keyword scores
        technical_score = self._calculate_keyword_score(message_lower, self.technical_keywords)
        business_score = self._calculate_keyword_score(message_lower, self.business_keywords)
        frustration_score = self._calculate_keyword_score(message_lower, self.frustration_indicators)
        
        # Analyze writing style
        writing_style = self._analyze_writing_style(message)
        
        # Determine persona
        persona_scores = {
            PersonaType.TECHNICAL_EXPERT: technical_score * 0.7 + writing_style.get('technical_style', 0) * 0.3,
            PersonaType.BUSINESS_EXEC: business_score * 0.8 + writing_style.get('formal_style', 0) * 0.2,
            PersonaType.FRUSTRATED_USER: frustration_score * 0.6 + max(0, -sentiment_score) * 0.4
        }
        
        # Adjust based on conversation history
        persona_scores = self._adjust_with_history(persona_scores, conversation_history)
        
        # Select winning persona
        winning_persona = max(persona_scores.items(), key=lambda x: x[1])
        
        characteristics = {
            'sentiment_score': sentiment_score,
            'technical_score': technical_score,
            'business_score': business_score,
            'frustration_score': frustration_score,
            'writing_style': writing_style
        }
        
        return CustomerPersona(
            persona_type=winning_persona[0],
            confidence=winning_persona[1],
            characteristics=characteristics
        )
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculate presence score for keywords"""
        matches = sum(1 for keyword in keywords if keyword in text)
        return min(1.0, matches / max(1, len(keywords) * 0.3))
    
    def _analyze_writing_style(self, text: str) -> Dict[str, float]:
        """Analyze writing style characteristics"""
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = np.mean([len(sentence.split()) for sentence in sentences if sentence.strip()])
        
        # Technical style indicators
        code_patterns = len(re.findall(r'[{}();<>]|->|=>', text))
        acronyms = len(re.findall(r'\b[A-Z]{2,}\b', text))
        
        # Formal style indicators
        formal_words = len(re.findall(r'\b(please|thank you|would you|could you|regards|sincerely)\b', text.lower()))
        
        return {
            'technical_style': min(1.0, (code_patterns + acronyms) / max(1, len(text.split()) / 10)),
            'formal_style': min(1.0, formal_words / max(1, len(sentences))),
            'avg_sentence_length': avg_sentence_length
        }
    
    def _adjust_with_history(self, persona_scores: Dict, history: List[Dict]) -> Dict:
        """Adjust scores based on conversation history"""
        if not history:
            return persona_scores
        
        # Simple history weighting - recent messages matter more
        history_personas = []
        for i, msg in enumerate(reversed(history[-3:])):  # Last 3 messages
            if 'persona' in msg:
                weight = 0.5 / (i + 1)  # Decreasing weight
                history_personas.append((msg['persona'], weight))
        
        for persona_type, weight in history_personas:
            if persona_type in persona_scores:
                persona_scores[persona_type] += weight
        
        return persona_scores