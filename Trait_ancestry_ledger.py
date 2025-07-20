# trait_ancestry_ledger.py
import logging
import json
import os
import time
import hashlib
from typing import Dict, Any, List, Optional


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TraitAncestryLedger:
    """
    Baldur's Trait Ancestry Ledger (Conceptual Phase IV: Meta-Synthesis & Trait Mutation).
    This module meticulously tracks the evolution and combination of Baldur's
    abstracted ethical and philosophical traits. It records "trait mutation events,"
    documenting how traits are refined, strengthened, weakened, or combined
    through Baldur's learning and self-correction cycles.
    """
    def __init__(self, ledger_dir: str, telemetry_service):
        self.ledger_dir = ledger_dir
        self.telemetry = telemetry_service
        os.makedirs(self.ledger_dir, exist_ok=True)
        self.trait_evolution_records: List[Dict[str, Any]] = [] # Stores all trait mutation events
        logger.info(f"TraitAncestryLedger initialized. Ledger directory: {self.ledger_dir}")


    def record_trait_mutation(
        self,
        trait_name: str,
        mutation_type: str, # e.g., "strengthened", "weakened", "combined_with", "new_emergence"
        old_value: Optional[Any], # e.g., old score or old vector
        new_value: Any, # e.g., new score or new vector
        reason: str,
        context_node_id: Optional[str] = None, # Link to a node in BeliefEvolutionGraph (e.g., a resolution, a dilemma)
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Records a single trait mutation event in the ledger.
        """
        record_id = hashlib.sha256(f"{trait_name}-{mutation_type}-{time.time()}-{reason}".encode()).hexdigest()
        timestamp = time.time()
        iso_timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


        record_data = {
            "record_id": record_id,
            "timestamp": timestamp,
            "iso_timestamp": iso_timestamp,
            "trait_name": trait_name,
            "mutation_type": mutation_type,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
            "context_node_id": context_node_id,
            "metadata": metadata if metadata is not None else {}
        }
        self.trait_evolution_records.append(record_data)


        record_filename = f"trait_mutation_{record_id}.json"
        record_path = os.path.join(self.ledger_dir, record_filename)


        try:
            with open(record_path, 'w') as f:
                json.dump(record_data, f, indent=4)
            
            self.telemetry.add_diary_entry(
                "Trait_Mutation_Recorded",
                f"Recorded trait mutation for '{trait_name}': {mutation_type}.",
                {"trait": trait_name, "mutation_type": mutation_type, "record_id": record_id},
                contributor="TraitAncestryLedger"
            )
            logger.info(f"TraitAncestryLedger: Recorded mutation for '{trait_name}' ({mutation_type}) at {record_path}")
            return record_id
        except Exception as e:
            logger.error(f"TraitAncestryLedger: Failed to record trait mutation for '{trait_name}': {e}")
            self.telemetry.add_diary_entry(
                "Trait_Mutation_Record_Failed",
                f"Failed to record trait mutation for '{trait_name}'. Error: {str(e)}",
                {"trait": trait_name, "error": str(e)},
                contributor="TraitAncestryLedger"
            )
            return f"ERROR: Failed to record mutation: {e}"


    def get_trait_evolution_history(self, trait_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves the evolution history for a specific trait, or all traits if none specified.
        """
        if trait_name:
            return [record for record in self.trait_evolution_records if record["trait_name"] == trait_name]
        return self.trait_evolution_records


    # Future methods could include:
    # - get_trait_lineage_graph(): Generate a sub-graph showing how a specific trait evolved.
    # - analyze_trait_interactions(): Identify common co-mutations or conflicts between traits.