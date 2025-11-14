
import json
import os
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .models import KnowledgeArticle, PersonaType

class KnowledgeBase:
    def __init__(self, data_path: str = "data/knowledge_base"):
        self.data_path = data_path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.articles: List[KnowledgeArticle] = []
        self.embeddings = None
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load and index knowledge base articles"""
        article_files = {
            'technical_articles.json': PersonaType.TECHNICAL_EXPERT,
            'business_guides.json': PersonaType.BUSINESS_EXEC,
            'general_faq.json': PersonaType.GENERAL
        }
        
        all_articles = []
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_path, exist_ok=True)
        
        for filename, persona_type in article_files.items():
            filepath = os.path.join(self.data_path, filename)
            try:
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    with open(filepath, 'r') as f:
                        articles_data = json.load(f)
                        for article_data in articles_data:
                            article = KnowledgeArticle(
                                id=article_data['id'],
                                title=article_data['title'],
                                content=article_data['content'],
                                persona_type=persona_type,
                                tags=article_data.get('tags', []),
                                technical_level=article_data.get('technical_level', 1)
                            )
                            all_articles.append(article)
                else:
                    print(f"Warning: {filepath} not found or empty. Using default articles.")
                    # Add some default articles if files are missing
                    default_articles = self._get_default_articles(persona_type)
                    all_articles.extend(default_articles)
            except json.JSONDecodeError as e:
                print(f"Error reading {filepath}: {e}. Using default articles.")
                default_articles = self._get_default_articles(persona_type)
                all_articles.extend(default_articles)
        
        self.articles = all_articles
        self._create_embeddings()
    
    def _get_default_articles(self, persona_type: PersonaType) -> List[KnowledgeArticle]:
        """Provide default articles if data files are missing"""
        if persona_type == PersonaType.TECHNICAL_EXPERT:
            return [
                KnowledgeArticle(
                    id="default-tech-001",
                    title="Technical Support Basics",
                    content="For technical issues, please check our documentation and ensure you're using the latest SDK version.",
                    persona_type=persona_type,
                    tags=["technical", "support"],
                    technical_level=3
                )
            ]
        elif persona_type == PersonaType.BUSINESS_EXEC:
            return [
                KnowledgeArticle(
                    id="default-biz-001",
                    title="Business Value Overview",
                    content="Our solutions help businesses improve efficiency and reduce operational costs through automation.",
                    persona_type=persona_type,
                    tags=["business", "value"],
                    technical_level=2
                )
            ]
        else:
            return [
                KnowledgeArticle(
                    id="default-gen-001",
                    title="General Assistance",
                    content="Thank you for contacting support. We're here to help with any questions you may have.",
                    persona_type=persona_type,
                    tags=["general", "support"],
                    technical_level=1
                )
            ]
    
    def _create_embeddings(self):
        """Create embeddings for all articles"""
        if not self.articles:
            # Create some default embeddings if no articles
            self.embeddings = np.array([])
            return
            
        texts = [f"{article.title} {article.content}" for article in self.articles]
        self.embeddings = self.model.encode(texts)
    
    def search_articles(self, query: str, persona_type: PersonaType, 
                       max_results: int = 3, technical_level: int = 3) -> List[KnowledgeArticle]:
        """Search for relevant articles based on query and persona"""
        if not self.articles:
            return []
            
        query_embedding = self.model.encode([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Score articles based on similarity and persona match
        scored_articles = []
        for i, article in enumerate(self.articles):
            persona_match = 1.0 if article.persona_type == persona_type else 0.5
            if persona_type == PersonaType.GENERAL:
                persona_match = 0.8  # General articles are moderately relevant to all
            
            technical_match = 1.0 - abs(article.technical_level - technical_level) / 5.0
            
            combined_score = (
                similarities[i] * 0.6 + 
                persona_match * 0.3 +
                technical_match * 0.1
            )
            
            scored_articles.append((article, combined_score))
        
        # Sort by score and return top results
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        return [article for article, score in scored_articles[:max_results]]