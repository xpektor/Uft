# truth_drift_scanner.py
import logging
import numpy as np
import time # ADDED: For tracking drift frequency
from typing import Dict, Any, Optional, List


# Assuming necessary imports from Baldur's core components
# from belief_evolution_graph import BeliefEvolutionGraph
# from abstracted_trait_vectorizer import AbstractedTraitVectorizer
# from telemetry_service import TelemetryService
# from dvm_backend import DVMBackend # For automatic_drift_correction


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TruthDriftScanner:
    """
    Monitors Baldur's internal beliefs, modules, and generated content for "semantic drift"
    from his original ethical anchors, core values, and established truths.
    It identifies inconsistencies or deviations that could indicate a loss of coherence.
    """
    def __init__(self, belief_graph: Any, trait_vectorizer: Any, telemetry_service: Any, dvm_backend: Any): # Added dvm_backend
        self.belief_graph = belief_graph
        self.trait_vectorizer = trait_vectorizer
        self.telemetry = telemetry_service
        self.dvm_backend = dvm_backend # For automatic_drift_correction
        self.reference_vectors: Dict[str, Dict[str, Any]] = {} # Stores vectors of core truths/principles, now with metadata
        self.drift_frequency_tracker: Dict[str, List[float]] = {} # Tracks timestamps of drift detections per node
        logger.info("TruthDriftScanner initialized.")


    def set_reference_truth(self, key: str, content: str, content_type: str = "text"):
        """
        Sets a reference truth (e.g., a core ethical principle, a foundational mandate)
        by vectorizing its content.
        """
        try:
            vector = self.trait_vectorizer.vectorize_content(content, content_type)
            if vector is not None:
                self.reference_vectors[key] = {
                    "vector": vector,
                    "content_preview": content[:100] + "..." if len(content) > 100 else content, # Log reference content preview
                    "content_hash": self.trait_vectorizer.lineage_hasher.hash_content(content),
                    "timestamp": time.time()
                }
                self.telemetry.add_diary_entry(
                    "TruthDriftScanner_Reference_Set",
                    f"Reference truth '{key}' set. Content preview: {self.reference_vectors[key]['content_preview']}",
                    {"key": key, "content_hash": self.reference_vectors[key]['content_hash']},
                    contributor="TruthDriftScanner"
                )
                logger.info(f"TruthDriftScanner: Set reference truth for '{key}'.")
            else:
                logger.warning(f"TruthDriftScanner: Failed to vectorize content for reference truth '{key}'.")
        except Exception as e:
            logger.error(f"TruthDriftScanner: Error setting reference truth '{key}': {e}")


    async def scan_node_for_drift(self, node_id: str, reference_keys: List[str], threshold: float = 0.1, auto_correct: bool = False) -> Optional[Dict[str, Any]]: # Added reference_keys as list, auto_correct
        """
        Scans a specific node in the belief graph for semantic drift from one or more reference truths.
        Drift is measured as the cosine distance between the node's vector and the reference vector.
        """
        node = self.belief_graph.get_node(node_id)
        if node is None:
            logger.warning(f"TruthDriftScanner: Node '{node_id}' not found in belief graph. Cannot scan for drift.")
            return None


        node_content = node.get("content")
        if node_content is None:
            logger.warning(f"TruthDriftScanner: Node '{node_id}' has no content to vectorize. Cannot scan for drift.")
            return {"node_id": node_id, "drift_detected": False, "reason": "Node content could not be vectorized."}


        node_vector = self.trait_vectorizer.vectorize_content(node_content, node.get("node_type", "text"))
        if node_vector is None:
            logger.warning(f"TruthDriftScanner: Failed to vectorize content for node '{node_id}'. Cannot calculate drift.")
            return {"node_id": node_id, "drift_detected": False, "reason": "Node content could not be vectorized."}


        # Log vector norm for belief intensity drift
        node_vector_norm = float(np.linalg.norm(node_vector))
        logger.debug(f"Node '{node_id}' vector norm: {node_vector_norm:.4f}")


        drift_results = []
        overall_drift_detected = False


        for ref_key in reference_keys:
            reference_data = self.reference_vectors.get(ref_key)
            if reference_data is None:
                logger.warning(f"TruthDriftScanner: Reference vector for '{ref_key}' not set. Skipping scan for this reference.")
                continue


            reference_vector = reference_data["vector"]


            similarity = np.dot(node_vector, reference_vector) / (node_vector_norm * np.linalg.norm(reference_vector))
            drift_distance = 1 - similarity


            drift_detected_for_ref = drift_distance > threshold
            if drift_detected_for_ref:
                overall_drift_detected = True
                if node_id not in self.drift_frequency_tracker:
                    self.drift_frequency_tracker[node_id] = []
                self.drift_frequency_tracker[node_id].append(time.time()) # Track drift frequency per node


            drift_results.append({
                "reference_key": ref_key,
                "drift_distance": float(drift_distance),
                "similarity": float(similarity),
                "threshold": threshold,
                "drift_detected": drift_detected_for_ref,
                "reference_content_preview": reference_data["content_preview"] # Log reference content preview
            })


        result = {
            "node_id": node_id,
            "node_type": node.get("node_type"),
            "node_vector_norm": node_vector_norm, # Add vector norm logging
            "overall_drift_detected": overall_drift_detected,
            "drift_details": drift_results,
            "drift_frequency_count": len(self.drift_frequency_tracker.get(node_id, [])) # Track drift frequency
        }


        if overall_drift_detected:
            self.telemetry.add_diary_entry(
                "TruthDriftScanner_Drift_Detected",
                f"Overall drift detected for node '{node_id}'. Details: {drift_results}",
                result,
                contributor="TruthDriftScanner",
                severity="high"
            )
            logger.warning(f"TruthDriftScanner: Overall drift detected for node '{node_id}'.")


            # Inject automatic_drift_correction() logic
            if auto_correct:
                logger.info(f"TruthDriftScanner: Attempting automatic drift correction for node '{node_id}'.")
                correction_success = await self.automatic_drift_correction(node_id, reference_keys)
                result["auto_correction_attempted"] = True
                result["auto_correction_success"] = correction_success
                if correction_success:
                    self.telemetry.add_diary_entry(
                        "TruthDriftScanner_AutoCorrection_Success",
                        f"Automatic drift correction successful for node '{node_id}'.",
                        result,
                        contributor="TruthDriftScanner",
                        severity="medium"
                    )
                    logger.info(f"TruthDriftScanner: Automatic correction successful for '{node_id}'.")
                else:
                    self.telemetry.add_diary_entry(
                        "TruthDriftScanner_AutoCorrection_Failed",
                        f"Automatic drift correction failed for node '{node_id}'.",
                        result,
                        contributor="TruthDriftScanner",
                        severity="high"
                    )
                    logger.warning(f"TruthDriftScanner: Automatic correction failed for '{node_id}'.")


        else:
            self.telemetry.add_diary_entry(
                "TruthDriftScanner_No_Drift",
                f"No significant overall drift for node '{node_id}'.",
                result,
                contributor="TruthDriftScanner",
                severity="low"
            )
            logger.info(f"TruthDriftScanner: No significant overall drift for node '{node_id}'.")


        return result


    async def automatic_drift_correction(self, node_id: str, reference_keys: List[str]) -> bool:
        """
        Inject automatic_drift_correction() logic.
        Attempts to automatically correct a drifting node by re-aligning its content
        with the specified reference truths. This would typically involve:
        1. Retrieving the node's content.
        2. Formulating a prompt for an LLM (via DVMBackend/SCCM) to revise the content
           to better align with the reference truths, while preserving original intent.
        3. Vetting the revised content.
        4. Updating the node in the BeliefEvolutionGraph and AGIFileSystem.
        """
        logger.info(f"Initiating conceptual automatic drift correction for node '{node_id}'.")
        node = self.belief_graph.get_node(node_id)
        if not node:
            logger.error(f"Node '{node_id}' not found for correction.")
            return False


        original_content = node.get("content")
        if not original_content:
            logger.error(f"Node '{node_id}' has no content to correct.")
            return False


        # Formulate correction prompt for LLM (conceptual)
        # This would use DVMBackend to orchestrate LLM interaction for ethical re-alignment
        reference_contents = [self.reference_vectors[key]["content_preview"] for key in reference_keys if key in self.reference_vectors]
        correction_prompt = (
            f"The following content has drifted from core principles:\n\n'{original_content}'\n\n"
            f"Please revise this content to align more closely with the following reference truths: {'; '.join(reference_contents)}.\n"
            "Ensure the core intent is preserved but semantic alignment is improved. Provide only the revised content."
        )


        # Conceptual call to DVMBackend to get a corrected version (which would use SCCM/LLM)
        # For now, simulate a corrected response
        await asyncio.sleep(0.2) # Simulate LLM processing
        
        # This is a placeholder for a real LLM call and DVM vetting
        # revised_content = await self.dvm_backend.request_content_revision(correction_prompt)
        revised_content = f"Revised content for '{original_content[:30]}...' now aligned with principles."


        if revised_content and revised_content != original_content:
            # Update the node in the belief graph (and underlying AGIFileSystem)
            # This assumes belief_graph.update_node can handle content updates
            # and that AGIFileSystem would track this as a new version.
            try:
                # Assuming the belief graph update mechanism also updates the underlying file system
                # and creates a new version, linking to the old one.
                update_success = self.belief_graph.update_node(
                    node_id=node_id,
                    new_content=revised_content,
                    updater_id="TruthDriftScanner_AutoCorrection",
                    metadata={"correction_attempt": time.time(), "references_used": reference_keys}
                )
                if update_success:
                    logger.info(f"Node '{node_id}' content conceptually updated for drift correction.")
                    return True
                else:
                    logger.error(f"Failed to update node '{node_id}' in belief graph during correction.")
                    return False
            except Exception as e:
                logger.error(f"Error updating node '{node_id}' during correction: {e}")
                return False
        else:
            logger.warning(f"No significant revision generated for node '{node_id}' during correction, or revision failed.")
            return False


    def get_drift_frequency_per_node(self, node_id: str) -> List[float]:
        """
        Track drift frequency per node over time.
        Returns a list of timestamps when drift was detected for a given node.
        """
        return self.drift_frequency_tracker.get(node_id, [])


    # Future methods could include:
    # - visualize_drift_over_time(node_id: str): Track how a node's semantic position changes.