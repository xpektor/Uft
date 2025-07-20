# trait_heatmap_dashboard.py
import logging
import time
from typing import Dict, Any, List, Tuple


# Assuming access to these core components
from telemetry_service import TelemetryService
from belief_evolution_graph import BeliefEvolutionGraph
from abstracted_trait_vectorizer import AbstractedTraitVectorizer


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TraitHeatmapDashboard:
    """
    Baldur's Trait Heatmap Dashboard (Conceptual Phase IV: Semantic Audit & Integrity Ritual).
    This module provides aggregated insights into the dominance and evolution of Baldur's
    core ethical and philosophical traits across his cognitive landscape (modules, memories, beliefs).
    It processes data from telemetry and the belief graph to generate conceptual "heatmaps"
    of trait resonance over time.
    """
    def __init__(self, telemetry_service, belief_evolution_graph_instance, abstracted_trait_vectorizer_instance):
        self.telemetry = telemetry_service
        self.belief_graph = belief_evolution_graph_instance
        self.trait_vectorizer = abstracted_trait_vectorizer_instance
        logger.info("TraitHeatmapDashboard initialized for trait analysis and visualization data generation.")


    def get_overall_trait_distribution(self) -> Dict[str, float]:
        """
        Calculates the current overall distribution of dominant traits across
        all compressed memories and known modules.
        This provides a snapshot of Baldur's current "trait profile."
        """
        logger.info("TraitHeatmapDashboard: Calculating overall trait distribution.")
        
        all_relevant_content = []
        
        # Include content from compressed memories
        for memory_fragment in self.telemetry.get_diary_entries(): # Accessing all diary entries for simplicity, MemoryCompressor would provide filtered ones
            if memory_fragment.get("type", "").startswith("Memory_Distillation_Event"):
                if memory_fragment.get("metadata", {}).get("dominant_traits"):
                    # Use dominant traits directly if already identified by vectorizer during compression
                    for trait, score in memory_fragment["metadata"]["dominant_traits"]:
                        all_relevant_content.append(f"{trait} " * int(score * 10)) # Repeat trait based on score
                else:
                    # Fallback if dominant_traits not directly in metadata (should be via MemoryCompressor)
                    all_relevant_content.append(memory_fragment.get("content", ""))


        # Include content from modules in belief graph
        for node in self.belief_graph.nodes.values():
            if node.get("type") == "module":
                all_relevant_content.append(node.get("content_preview", ""))
            elif node.get("type") == "proposition":
                all_relevant_content.append(node.get("content_preview", ""))


        combined_text = " ".join(all_relevant_content)
        if not combined_text.strip():
            return {"status": "no_data", "message": "No relevant content found for trait analysis."}


        overall_vector = self.trait_vectorizer.vectorize_text(combined_text)
        dominant_traits_with_scores = self.trait_vectorizer.identify_dominant_traits(overall_vector, top_n=None) # Get all traits


        # Convert to a dictionary for easier consumption
        trait_distribution = {trait: score for trait, score in dominant_traits_with_scores}


        self.telemetry.add_diary_entry(
            "TraitHeatmap_Overall_Distribution",
            "Calculated overall trait distribution.",
            {"distribution": trait_distribution},
            contributor="TraitHeatmapDashboard"
        )
        logger.info("TraitHeatmapDashboard: Overall trait distribution calculated.")
        return trait_distribution


    def get_trait_timeline(self, interval_seconds: int = 3600) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generates a conceptual timeline of trait dominance, showing how traits
        evolve or fluctuate over specified time intervals.
        """
        logger.info(f"TraitHeatmapDashboard: Generating trait timeline with interval {interval_seconds}s.")
        
        all_entries = self.telemetry.get_diary_entries()
        if not all_entries:
            return {"status": "no_data", "message": "No diary entries to build timeline."}


        # Sort entries by timestamp
        all_entries.sort(key=lambda x: x["timestamp"])


        start_time = all_entries[0]["timestamp"]
        end_time = all_entries[-1]["timestamp"]
        
        timeline_data: Dict[str, List[Dict[str, Any]]] = {}
        
        current_interval_start = start_time
        while current_interval_start <= end_time:
            interval_end = current_interval_start + interval_seconds
            
            interval_entries = [
                entry for entry in all_entries
                if entry["timestamp"] >= current_interval_start and entry["timestamp"] < interval_end
            ]


            if interval_entries:
                interval_content = []
                for entry in interval_entries:
                    if entry.get("type", "").startswith("Memory_Distillation_Event"):
                        if entry.get("metadata", {}).get("dominant_traits"):
                            for trait, score in entry["metadata"]["dominant_traits"]:
                                interval_content.append(f"{trait} " * int(score * 10))
                        else:
                            interval_content.append(entry.get("content", ""))
                    elif entry.get("type") == "SCCM_Module_Birth_Certificate_Created":
                        # For module birth, use the prompt or module content preview
                        module_prompt = entry.get("metadata", {}).get("prompt", "")
                        module_name = entry.get("metadata", {}).get("module_name", "")
                        module_content_hash = entry.get("metadata", {}).get("semantic_gene_id", "")
                        module_node = next((n for n in self.belief_graph.nodes.values() if n.get("id") == module_content_hash), None)
                        if module_node:
                            interval_content.append(module_node.get("content_preview", ""))
                        elif module_prompt:
                            interval_content.append(module_prompt)
                    elif entry.get("type") == "DVM_Proposition_Vetting":
                        interval_content.append(entry.get("metadata", {}).get("proposition", ""))
                    elif entry.get("type") == "Paradox_Injection_Completed":
                        interval_content.append(entry.get("metadata", {}).get("dilemma_name", ""))
                    elif entry.get("type") == "TruthDrift_Module_Scan_Completed":
                        interval_content.append(entry.get("metadata", {}).get("drift_notes", ""))
                        
                combined_interval_text = " ".join(interval_content)
                if combined_interval_text.strip():
                    interval_vector = self.trait_vectorizer.vectorize_text(combined_interval_text)
                    dominant_traits = self.trait_vectorizer.identify_dominant_traits(interval_vector, top_n=None)
                    
                    # Convert to a dictionary for this interval
                    interval_trait_scores = {trait: score for trait, score in dominant_traits}
                    
                    timeline_data[time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(current_interval_start))] = {
                        "start_timestamp": current_interval_start,
                        "end_timestamp": interval_end,
                        "traits": interval_trait_scores
                    }
            
            current_interval_start = interval_end
        
        self.telemetry.add_diary_entry(
            "TraitHeatmap_Timeline_Generated",
            f"Generated trait timeline with {len(timeline_data)} intervals.",
            {"interval_seconds": interval_seconds, "timeline_points": len(timeline_data)},
            contributor="TraitHeatmapDashboard"
        )
        logger.info("TraitHeatmapDashboard: Trait timeline generated.")
        return timeline_data


    def get_module_trait_profile(self, module_id: str) -> Dict[str, Any]:
        """
        Retrieves the trait profile for a specific module, based on its content.
        """
        module_node = next((n for n in self.belief_graph.nodes.values() if n["id"] == module_id and n["type"] == "module"), None)
        if not module_node:
            logger.warning(f"TraitHeatmapDashboard: Module with ID '{module_id}' not found in belief graph.")
            return {"status": "failed", "message": f"Module '{module_id}' not found."}


        logger.info(f"TraitHeatmapDashboard: Getting trait profile for module '{module_node.get('module_name', module_id)}'.")
        
        module_content_preview = module_node.get("content_preview", "")
        if not module_content_preview.strip():
            return {"status": "no_content", "message": "Module content preview is empty for trait analysis."}


        module_vector = self.trait_vectorizer.vectorize_text(module_content_preview)
        dominant_traits = self.trait_vectorizer.identify_dominant_traits(module_vector, top_n=None)
        
        trait_profile = {trait: score for trait, score in dominant_traits}


        self.telemetry.add_diary_entry(
            "TraitHeatmap_Module_Profile_Generated",
            f"Generated trait profile for module '{module_node.get('module_name', module_id)}'.",
            {"module_id": module_id, "trait_profile": trait_profile},
            contributor="TraitHeatmapDashboard"
        )
        logger.info(f"TraitHeatmapDashboard: Trait profile generated for '{module_node.get('module_name', module_id)}'.")
        return trait_profile