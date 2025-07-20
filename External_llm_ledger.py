# external_llm_ledger.py
import logging
import time
import hashlib
from typing import Dict, List, Any, Optional


# Assuming TelemetryService, LineageHasher, and TraitHeatmapDashboard are available
# from telemetry_service import TelemetryService
# from lineage_hasher import LineageHasher
# from trait_heatmap_dashboard import TraitHeatmapDashboard # For linking ledger traits into ancestry dashboard
# from semantic_divergence_analyzer import SemanticDivergenceAnalyzer # For divergence analysis


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ExternalLLMLedger:
    """
    Records all interactions Baldur has with external Large Language Models (LLMs),
    including prompts sent, responses received, and associated metadata.
    This ensures transparency, auditability, and provides data for semantic divergence analysis.
    """
    def __init__(self, telemetry_service: Any, lineage_hasher: Any, trait_heatmap_dashboard: Any, semantic_divergence_analyzer: Any): # Added dashboard and analyzer
        self.telemetry = telemetry_service
        self.lineage_hasher = lineage_hasher
        self.trait_heatmap_dashboard = trait_heatmap_dashboard # Store for dashboard integration
        self.semantic_divergence_analyzer = semantic_divergence_analyzer # Store for divergence analysis
        self.interactions: Dict[str, Dict[str, Any]] = {} # Stores interaction records
        logger.info("ExternalLLMLedger initialized.")


    def record_interaction(self,
                           prompt: str,
                           response: str,
                           llm_model: str,
                           llm_provider: str,
                           interaction_type: str, # e.g., "query", "generation", "analysis"
                           metadata: Optional[Dict[str, Any]] = None
                          ) -> str:
        """
        Records a single interaction with an external LLM.
        Generates a unique ID and hashes the prompt/response for integrity.
        """
        timestamp = time.time()
        iso_timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(timestamp))


        prompt_hash = self.lineage_hasher.hash_content(prompt)
        response_hash = self.lineage_hasher.hash_content(response)


        interaction_id = hashlib.sha256(
            f"{prompt_hash}-{response_hash}-{llm_model}-{timestamp}".encode()
        ).hexdigest()


        record = {
            "interaction_id": interaction_id,
            "timestamp": timestamp,
            "iso_timestamp": iso_timestamp,
            "llm_model": llm_model,
            "llm_provider": llm_provider,
            "interaction_type": interaction_type,
            "prompt_text": prompt,
            "prompt_hash": prompt_hash,
            "response_text": response,
            "response_hash": response_hash,
            "metadata": metadata if metadata is not None else {}
        }


        self.interactions[interaction_id] = record


        self.telemetry.add_diary_entry(
            "ExternalLLM_Interaction_Recorded",
            f"LLM interaction with {llm_model} recorded (ID: {interaction_id}). Type: {interaction_type}.",
            record,
            contributor="ExternalLLMLedger"
        )
        logger.info(f"ExternalLLMLedger: Recorded interaction ID {interaction_id} with {llm_model}.")
        
        # Inject hash lineage into divergence analyzer (conceptual)
        # This would be triggered for specific types of interactions, e.g., when
        # comparing multiple LLM responses for the same prompt.
        # For now, a conceptual call to analyze if a previous prompt with same hash exists.
        if metadata and metadata.get("comparison_target_hash"):
            # self.semantic_divergence_analyzer.analyze_divergence(
            #     content_a=prompt,
            #     content_b=response,
            #     content_id_a=f"prompt_{prompt_hash}",
            #     content_id_b=f"response_{response_hash}",
            #     metadata={"interaction_id": interaction_id, "comparison_target_hash": metadata["comparison_target_hash"]}
            # )
            pass # Placeholder for actual call


        # Link ledger traits into ancestry dashboard (conceptual)
        # Update dashboard with LLM usage metrics or quality scores
        self.trait_heatmap_dashboard.update_trait_values(
            timestamp=timestamp,
            trait_scores={
                f"llm_usage_{llm_model.replace('-', '_')}": 0.01, # Small increment for usage
                f"llm_quality_{llm_model.replace('-', '_')}": metadata.get("quality_score", 0.8) # Conceptual quality
            }
        )


        return interaction_id


    def get_interaction(self, interaction_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific interaction record by its ID."""
        record = self.interactions.get(interaction_id)
        if record:
            self.telemetry.add_diary_entry(
                "ExternalLLM_Interaction_Accessed",
                f"LLM interaction {interaction_id} accessed.",
                {"interaction_id": interaction_id},
                contributor="ExternalLLMLedger"
            )
            logger.info(f"ExternalLLMLedger: Retrieved interaction ID {interaction_id}.")
        else:
            logger.warning(f"ExternalLLMLedger: Interaction ID '{interaction_id}' not found.")
        return record


    def list_interactions(self, llm_model: Optional[str] = None, interaction_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists recorded interactions, with optional filters."""
        results = []
        for record in self.interactions.values():
            if (llm_model is None or record["llm_model"] == llm_model) and \
               (interaction_type is None or record["interaction_type"] == interaction_type):
                results.append(record)
        logger.info(f"ExternalLLMLedger: Listed {len(results)} interactions.")
        return results


    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Add summary stats and drift prediction over time.
        Provides summary statistics on LLM usage and conceptual drift prediction.
        """
        total_interactions = len(self.interactions)
        model_counts = {}
        for record in self.interactions.values():
            model_counts[record["llm_model"]] = model_counts.get(record["llm_model"], 0) + 1
        
        # Conceptual drift prediction over time
        # This would require analyzing semantic divergence reports over time
        # from semantic_divergence_analyzer.
        conceptual_drift_prediction = "Low (stable LLM interactions)"
        # if self.semantic_divergence_analyzer.get_average_drift_score() > 0.1: # Conceptual call
        #    conceptual_drift_prediction = "Medium (some divergence observed)"


        stats = {
            "total_interactions": total_interactions,
            "interactions_by_model": model_counts,
            "conceptual_drift_prediction": conceptual_drift_prediction,
            "last_updated": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }
        self.telemetry.add_diary_entry(
            "ExternalLLMLedger_Summary_Stats",
            "LLM ledger summary statistics generated.",
            stats,
            contributor="ExternalLLMLedger"
        )
        return stats