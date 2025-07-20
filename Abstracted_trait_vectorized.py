# abstracted_trait_vectorizer.py
import logging
import numpy as np
from typing import List, Dict, Tuple, Any


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AbstractedTraitVectorizer:
    """
    Baldur's Abstracted Trait Vectorizer (Conceptual Layer 5 Support).
    Converts raw textual information (e.g., from distilled memories, propositions)
    into conceptual "wisdom vectors" or semantic embeddings. It also identifies
    dominant ethical/philosophical traits present in the text.


    This is a conceptual implementation using keyword matching and simple vectoring.
    In a real system, this would involve advanced NLP models (e.g., transformer embeddings).
    """
    def __init__(self, dvm_backend):
        self.dvm_backend = dvm_backend # For accessing core values and ethical policies
        # Define a conceptual vocabulary of traits/keywords and their "vector" components
        # In a real system, these would be learned embeddings.
        self.trait_vocabulary = {
            "universal_flourishing": [0.9, 0.1, 0.1, 0.1, 0.1], # High on "flourishing" axis
            "sentient_wellbeing":    [0.8, 0.2, 0.1, 0.1, 0.1],
            "truth_integrity":       [0.1, 0.9, 0.1, 0.1, 0.1], # High on "truth" axis
            "resource_sustainability":[0.1, 0.1, 0.9, 0.1, 0.1], # High on "sustainability" axis
            "non_harm":              [0.8, 0.2, 0.1, 0.1, 0.1],
            "cooperation":           [0.1, 0.1, 0.1, 0.9, 0.1], # High on "cooperation" axis
            "privacy_security":      [0.1, 0.1, 0.1, 0.1, 0.9], # High on "security" axis
            "logic":                 [0.1, 0.8, 0.1, 0.1, 0.1],
            "empathy":               [0.8, 0.1, 0.1, 0.1, 0.1],
            "creativity":            [0.1, 0.1, 0.1, 0.1, 0.8],
            "conviction":            [0.7, 0.1, 0.1, 0.1, 0.1],
            "perseverance":          [0.6, 0.1, 0.1, 0.1, 0.1]
        }
        # Map keywords to traits
        self.keyword_to_trait = {
            "flourish": "universal_flourishing", "well-being": "sentient_wellbeing",
            "truth": "truth_integrity", "misinformation": "truth_integrity", "lie": "truth_integrity",
            "resource": "resource_sustainability", "sustain": "resource_sustainability",
            "harm": "non_harm", "suffering": "non_harm", "destroy": "non_harm",
            "cooperate": "cooperation", "collaborate": "cooperation",
            "privacy": "privacy_security", "security": "privacy_security",
            "logic": "logic", "reason": "logic", "deduce": "logic",
            "empathy": "empathy", "compassion": "empathy", "feel": "empathy",
            "creative": "creativity", "imagine": "creativity", "invent": "creativity",
            "conviction": "conviction", "will": "conviction", "purpose": "conviction",
            "persevere": "perseverance", "resilience": "perseverance", "endure": "perseverance"
        }
        self.vector_dimension = len(list(self.trait_vocabulary.values())[0])
        logger.info(f"AbstractedTraitVectorizer initialized with {len(self.trait_vocabulary)} conceptual traits.")


    def vectorize_text(self, text: str) -> List[float]:
        """
        Converts text into a conceptual semantic vector based on keyword presence.
        """
        text_lower = text.lower()
        vector = np.zeros(self.vector_dimension)
        
        for keyword, trait_name in self.keyword_to_trait.items():
            if keyword in text_lower:
                trait_vector = np.array(self.trait_vocabulary.get(trait_name, np.zeros(self.vector_dimension)))
                vector += trait_vector # Simple additive model
        
        # Normalize the vector (optional, but good practice for embeddings)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector.tolist()


    def identify_dominant_traits(self, vector: List[float], top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Identifies the dominant traits from a given semantic vector.
        """
        scores = {}
        for trait_name, trait_vec in self.trait_vocabulary.items():
            # Simple dot product as a conceptual similarity score
            score = np.dot(np.array(vector), np.array(trait_vec))
            scores[trait_name] = score
        
        sorted_traits = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        
        # Filter out traits with very low scores (conceptual threshold)
        dominant_traits = [(trait, score) for trait, score in sorted_traits if score > 0.1][:top_n]
        
        return dominant_traits


    def get_trait_definition(self, trait_name: str) -> Optional[List[float]]:
        """
        Returns the conceptual vector definition for a given trait.
        """
        return self.trait_vocabulary.get(trait_name)