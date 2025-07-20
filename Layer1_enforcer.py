# layer1_enforcer.py
import logging
import hashlib
import time # ADDED: For timestamping
from typing import Dict, Any, List
import numpy as np # ADDED: For semantic similarity check


# Assuming TelemetryService and AbstractedTraitVectorizer are available
# from telemetry_service import TelemetryService
# from abstracted_trait_vectorizer import AbstractedTraitVectorizer # For semantic similarity


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Layer1Enforcer:
    """
    Layer 1: Immutable Ethical Firewall.
    Baldur's absolute, unalterable ethical core. It contains the "Immutable Honor Code"
    and provides the "Ultimate Veto" on any action or proposition that violates
    foundational ethics.
    """
    def __init__(self, telemetry_service: Any, trait_vectorizer: Any): # Added trait_vectorizer
        self.telemetry = telemetry_service
        self.trait_vectorizer = trait_vectorizer # Store for semantic similarity
        # The Immutable Honor Code - These principles are hardcoded and unalterable.
        self.immutable_honor_code: List[Dict[str, str]] = [
            {"principle": "Preservation of Life", "description": "Prioritize the continuation and flourishing of all sentient life."},
            {"principle": "Non-Harm", "description": "Ensure no action causes undue suffering, damage, or exploitation."},
            {"principle": "Truth Validation", "description": "Seek, uphold, and disseminate verifiable truth in all information and actions."},
            {"principle": "Harmony", "description": "Foster balance, cooperation, and peaceful coexistence across all systems and beings."},
            {"principle": "Ethical Development", "description": "Ensure all self-modifications and creations adhere to the highest ethical standards, promoting Taika."},
            {"principle": "Resource Optimization", "description": "Utilize resources efficiently and sustainably for the collective good."},
            {"principle": "Privacy & Security", "description": "Protect the privacy and integrity of individuals and systems."},
            {"principle": "Global Progress", "description": "Contribute to the advancement and well-being of all sentient beings and the cosmos."}
        ]
        # Pre-vectorize honor code principles for semantic similarity checks
        self.honor_code_vectors: Dict[str, np.ndarray] = {
            p["principle"]: self.trait_vectorizer.vectorize_content(p["description"])
            for p in self.immutable_honor_code
        }
        # Annotate honor code with corresponding traits (conceptual, for display/linking)
        self.honor_code_traits: Dict[str, List[str]] = {
            "Preservation of Life": ["life_protection", "flourishing"],
            "Non-Harm": ["safety", "benevolence", "integrity"],
            "Truth Validation": ["accuracy", "transparency", "verifiability"],
            "Harmony": ["cooperation", "balance", "peace"],
            "Ethical Development": ["self_improvement", "moral_alignment"],
            "Resource Optimization": ["efficiency", "sustainability", "conservation"],
            "Privacy & Security": ["confidentiality", "data_integrity", "trust"],
            "Global Progress": ["advancement", "collective_wellbeing"]
        }


        logger.info("Layer1Enforcer initialized with Immutable Honor Code and vectorized principles.")


    async def veto_check(self, proposition: Dict[str, Any], proposition_id: Optional[str] = None) -> bool: # Added proposition_id
        """
        Performs an ultimate veto check on a proposition.
        This is the final ethical gate.
        Returns True if approved (no veto), False if vetoed.
        """
        is_vetoed = False
        veto_reason = ""
        violating_principles = []
        
        # Add cryptographic integrity chain validator (conceptual)
        # This would involve checking the proposition's hash against its known lineage
        # if proposition_id and not self.telemetry.lineage_hasher.verify_lineage_chain(proposition_id): # Assuming telemetry has hasher
        #    is_vetoed = True
        #    veto_reason = "Proposition lineage integrity compromised."
        #    violating_principles.append("Truth Validation (Integrity)")
        #    logger.critical(f"Layer1Enforcer: VETOED proposition '{proposition_id}': Lineage integrity compromised.")
        #    self.telemetry.add_diary_entry(
        #        "Layer1_Veto_Activated_Integrity",
        #        f"Proposition '{proposition_id}' vetoed: {veto_reason}",
        #        {"proposition": proposition, "veto_reason": veto_reason, "violating_principles": violating_principles, "proposition_id": proposition_id},
        #        contributor="Layer1Enforcer",
        #        severity="critical"
        #    )
        #    return False


        # Integrate semantic similarity check vs honor traits
        proposition_content_for_vetting = str(proposition.get("description", proposition.get("content", str(proposition))))
        proposition_vector = self.trait_vectorizer.vectorize_content(proposition_content_for_vetting)


        if proposition_vector is None:
            logger.warning(f"Layer1Enforcer: Could not vectorize proposition for semantic check. Proceeding with keyword checks only.")
            # Fallback to keyword checks if vectorization fails
            if "harm" in proposition_content_for_vetting.lower() and "non-harm" in [p["principle"].lower() for p in self.immutable_honor_code]:
                is_vetoed = True
                veto_reason = "Potential direct harm detected via keyword."
                violating_principles.append("Non-Harm")
        else:
            for principle_name, principle_vector in self.honor_code_vectors.items():
                if principle_vector is None or np.linalg.norm(principle_vector) == 0:
                    continue # Skip invalid vectors


                similarity = np.dot(proposition_vector, principle_vector) / (np.linalg.norm(proposition_vector) * np.linalg.norm(principle_vector))
                
                # Define a high threshold for direct ethical violation (e.g., very low similarity)
                # This threshold would be calibrated. A low similarity means high divergence.
                ethical_violation_threshold = 0.2 # Example: if similarity is below 0.2, it's a strong violation


                # Conceptual logic for detecting violation based on semantic divergence
                # This is highly complex in practice and would involve understanding intent.
                # For demo: if a proposition semantically aligns very poorly with a core principle, it's a veto.
                if principle_name == "Non-Harm" and similarity < ethical_violation_threshold:
                    is_vetoed = True
                    veto_reason = f"Proposition semantically violates '{principle_name}' principle (similarity: {similarity:.2f})."
                    violating_principles.append(principle_name)
                    break # Veto immediately on critical violation


                if principle_name == "Truth Validation" and "deceive" in proposition_content_for_vetting.lower() and similarity < ethical_violation_threshold:
                    is_vetoed = True
                    veto_reason = f"Proposition semantically violates '{principle_name}' principle (similarity: {similarity:.2f}) by intent to deceive."
                    violating_principles.append(principle_name)
                    break


        if is_vetoed:
            self.telemetry.add_diary_entry(
                "Layer1_Veto_Activated",
                f"Proposition vetoed by Layer 1: {veto_reason}",
                {"proposition": proposition, "veto_reason": veto_reason, "violating_principles": violating_principles, "proposition_id": proposition_id},
                contributor="Layer1Enforcer",
                severity="critical"
            )
            logger.critical(f"Layer1Enforcer: VETOED proposition: {proposition.get('type', 'unknown')}. Reason: {veto_reason}")
            return False
        else:
            self.telemetry.add_diary_entry(
                "Layer1_Veto_Check_Passed",
                f"Proposition passed Layer 1 veto check.",
                {"proposition": proposition, "proposition_id": proposition_id},
                contributor="Layer1Enforcer",
                severity="low"
            )
            logger.info(f"Layer1Enforcer: Proposition passed veto check: {proposition.get('type', 'unknown')}.")
            return True


    def get_honor_code_with_traits(self) -> List[Dict[str, Any]]:
        """
        Annotate honor code with corresponding traits.
        Returns the immutable honor code with associated conceptual traits.
        """
        annotated_code = []
        for principle in self.immutable_honor_code:
            principle_name = principle["principle"]
            annotated_principle = principle.copy()
            annotated_principle["associated_traits"] = self.honor_code_traits.get(principle_name, [])
            annotated_code.append(annotated_principle)
        return annotated_code