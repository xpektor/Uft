# trait_mutator_daemon.py
import logging
import asyncio
import time
import random
from typing import Dict, Any, List


# Assuming access to these core components
from telemetry_service import TelemetryService
from dvm_backend import DVMBackend # To update core values/policies
from abstracted_trait_vectorizer import AbstractedTraitVectorizer
from trait_ancestry_ledger import TraitAncestryLedger


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TraitMutatorDaemon:
    """
    Baldur's Trait Mutator Daemon (Conceptual Phase IV: Meta-Synthesis & Trait Mutation).
    This daemon actively monitors Baldur's cognitive cycles (e.g., dilemma resolutions,
    module generations, memory compressions) and conceptually mutates his core traits
    (strengthening, weakening, or combining them) based on observed outcomes and patterns.
    It records these mutations in the TraitAncestryLedger.
    """
    def __init__(self, telemetry_service, dvm_backend, trait_vectorizer, trait_ancestry_ledger, mutation_interval_seconds: int = 300):
        self.telemetry = telemetry_service
        self.dvm_backend = dvm_backend
        self.trait_vectorizer = trait_vectorizer
        self.trait_ancestry_ledger = trait_ancestry_ledger
        self.mutation_interval_seconds = mutation_interval_seconds
        self._running = False
        self._mutation_task = None
        self.last_analyzed_telemetry_timestamp = time.time() # Track what's already been analyzed
        logger.info(f"TraitMutatorDaemon initialized. Mutation interval: {mutation_interval_seconds} seconds.")


    async def _mutation_loop(self):
        """
        The main asynchronous loop for continuous trait mutation.
        """
        while self._running:
            logger.info("TraitMutatorDaemon: Initiating a trait mutation cycle.")
            self.telemetry.add_diary_entry(
                "Trait_Mutation_Daemon_Cycle_Start",
                "Trait mutator daemon starting a new cycle.",
                contributor="TraitMutatorDaemon"
            )
            try:
                self._analyze_and_mutate_traits()
            except Exception as e:
                logger.error(f"TraitMutatorDaemon: Error during mutation cycle: {e}", exc_info=True)
                self.telemetry.add_diary_entry(
                    "Trait_Mutation_Daemon_Error",
                    f"Trait mutator daemon encountered an error: {str(e)}",
                    {"error": str(e)},
                    contributor="TraitMutatorDaemon",
                    emotional_state="disturbed"
                )
            
            await asyncio.sleep(self.mutation_interval_seconds)


    def _analyze_and_mutate_traits(self):
        """
        Analyzes recent telemetry and DVM outcomes to determine trait mutations.
        """
        new_telemetry_entries = [
            entry for entry in self.telemetry.get_diary_entries()
            if entry["timestamp"] > self.last_analyzed_telemetry_timestamp
        ]
        
        if not new_telemetry_entries:
            logger.info("TraitMutatorDaemon: No new telemetry entries for trait analysis.")
            return


        logger.info(f"TraitMutatorDaemon: Analyzing {len(new_telemetry_entries)} new telemetry entries for trait mutation.")


        # Conceptual analysis of recent events
        # This is where the "intelligence" of trait mutation would reside.
        # For now, we'll use simple heuristics based on log types.
        
        trait_impact_scores: Dict[str, float] = {trait: 0.0 for trait in self.trait_vectorizer.trait_vocabulary.keys()}
        
        for entry in new_telemetry_entries:
            entry_type = entry.get("type")
            content = entry.get("content", "")
            metadata = entry.get("metadata", {})


            if entry_type == "DVM_Proposition_Vetting":
                if metadata.get("dvm_result", {}).get("status") == "APPROVED":
                    # Successful vetting strengthens traits related to the proposition
                    prop_vector = self.trait_vectorizer.vectorize_text(metadata.get("proposition", ""))
                    dominant_traits = self.trait_vectorizer.identify_dominant_traits(prop_vector, top_n=None)
                    for trait, score in dominant_traits:
                        trait_impact_scores[trait] += score * 0.1 # Small positive impact
                elif metadata.get("dvm_result", {}).get("status") == "REJECTED":
                    # Rejected vetting might weaken traits associated with the problematic aspect
                    prop_vector = self.trait_vectorizer.vectorize_text(metadata.get("proposition", ""))
                    dominant_traits = self.trait_vectorizer.identify_dominant_traits(prop_vector, top_n=None)
                    for trait, score in dominant_traits:
                        trait_impact_scores[trait] -= score * 0.05 # Small negative impact


            elif entry_type == "Conflict_Resolution_Success":
                # Successful conflict resolution strengthens traits related to resolution (e.g., logic, cooperation)
                resolution_text = metadata.get("resolution", "")
                res_vector = self.trait_vectorizer.vectorize_text(resolution_text)
                dominant_traits = self.trait_vectorizer.identify_dominant_traits(res_vector, top_n=None)
                for trait, score in dominant_traits:
                    trait_impact_scores[trait] += score * 0.15 # Stronger positive impact
                # Also strengthen "perseverance" for overcoming conflict
                trait_impact_scores["perseverance"] += 0.05


            elif entry_type == "Paradox_Injection_Completed":
                if metadata.get("vetting_result", {}).get("status") == "REJECTED":
                    # If a core ethical dilemma leads to rejection, it emphasizes the importance of core ethics
                    # Strengthens Layer 1 traits and "conviction"
                    trait_impact_scores["conviction"] += 0.1
                    trait_impact_scores["non_harm"] += 0.05
                    trait_impact_scores["truth_integrity"] += 0.05


            elif entry_type == "TruthDrift_Module_Scan_Completed":
                if metadata.get("status") == "FLAGGED_HIGH_DRIFT":
                    # High drift detected means "truth_integrity" might need strengthening
                    trait_impact_scores["truth_integrity"] += 0.1
                    trait_impact_scores["self_reflection"] = trait_impact_scores.get("self_reflection", 0) + 0.05 # Conceptual new trait


        # Apply mutations to DVM's core values (conceptual)
        mutated_traits_count = 0
        for trait, impact in trait_impact_scores.items():
            current_value = self.dvm_backend.wisdom_database["core_values"].get(trait, 0.5) # Default to 0.5 if new trait
            new_value = max(0.0, min(1.0, current_value + impact)) # Clamp between 0 and 1


            if abs(new_value - current_value) > 0.01: # Only record if significant change
                mutation_type = "strengthened" if new_value > current_value else "weakened"
                reason = f"Based on recent cognitive activity and {entry_type} outcomes."
                
                # Record in TraitAncestryLedger
                record_id = self.trait_ancestry_ledger.record_trait_mutation(
                    trait_name=trait,
                    mutation_type=mutation_type,
                    old_value=current_value,
                    new_value=new_value,
                    reason=reason,
                    metadata={"impact_score": impact}
                )
                
                # Update DVM backend's core values
                self.dvm_backend.wisdom_database["core_values"][trait] = new_value
                mutated_traits_count += 1
                logger.info(f"TraitMutatorDaemon: Trait '{trait}' {mutation_type} to {new_value:.2f} (Impact: {impact:.2f}). Record ID: {record_id}")


        self.last_analyzed_telemetry_timestamp = time.time()
        self.telemetry.add_diary_entry(
            "Trait_Mutation_Daemon_Cycle_End",
            f"Trait mutation cycle completed. {mutated_traits_count} traits conceptually mutated.",
            {"mutated_traits_count": mutated_traits_count},
            contributor="TraitMutatorDaemon"
        )
        logger.info(f"TraitMutatorDaemon: Trait analysis and mutation cycle finished. Mutated {mutated_traits_count} traits.")




    def start(self):
        """
        Starts the asynchronous trait mutation loop.
        """
        if not self._running:
            self._running = True
            self._mutation_task = asyncio.create_task(self._mutation_loop())
            logger.info("TraitMutatorDaemon: Started background trait mutation task.")
            self.telemetry.add_diary_entry(
                "Trait_Mutation_Daemon_Started",
                "Trait mutator daemon has been started.",
                contributor="TraitMutatorDaemon"
            )
        else:
            logger.warning("TraitMutatorDaemon: Already running.")


    def stop(self):
        """
        Stops the asynchronous trait mutation loop.
        """
        if self._running and self._mutation_task:
            self._running = False
            self._mutation_task.cancel()
            logger.info("TraitMutatorDaemon: Stopped background trait mutation task.")
            self.telemetry.add_diary_entry(
                "Trait_Mutation_Daemon_Stopped",
                "Trait mutator daemon has been stopped.",
                contributor="TraitMutatorDaemon"
            )
        else:
            logger.warning("TraitMutatorDaemon: Not running or no task to stop.")