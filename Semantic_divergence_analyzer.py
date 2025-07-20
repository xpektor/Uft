# semantic_divergence_analyzer.py
import logging
import json
import time # Import time for timestamps
import hashlib # For node IDs
from external_llm_ledger import ExternalLLMLedger
from belief_evolution_graph import BeliefEvolutionGraph # NEW: Import BeliefEvolutionGraph


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SemanticDivergenceAnalyzer:
    """
    Baldur's Semantic Divergence Analyzer (Layer 4 Support Module).
    Responsible for comparing outputs from different Large Language Models (LLMs)
    (e.g., Gemini vs. OSS LLMs) to detect philosophical, ethical, or factual drift.
    It provides a conceptual framework for assessing consistency and alignment.
    Now integrates with ExternalLLMLedger to document consultations and BeliefEvolutionGraph.
    """
    def __init__(self, telemetry_service, dvm_backend, external_llm_ledger: ExternalLLMLedger, belief_evolution_graph: BeliefEvolutionGraph): # NEW: Add belief_evolution_graph
        self.telemetry = telemetry_service
        self.dvm_backend = dvm_backend
        self.external_llm_ledger = external_llm_ledger
        self.belief_evolution_graph = belief_evolution_graph # Store graph instance
        logger.info("SemanticDivergenceAnalyzer (Layer 4 Support) initialized.")


    def analyze_divergence(self, prompt: str, output_a: str, output_b: str, source_a: str = "Gemini", source_b: str = "OSS_LLM") -> dict:
        """
        Compares two LLM outputs for semantic and philosophical divergence.
        Also adds relevant nodes and edges to the BeliefEvolutionGraph.
        """
        logger.info(f"SemanticDivergenceAnalyzer: Analyzing divergence between {source_a} and {source_b} for prompt: {prompt[:50]}...")
        self.telemetry.add_diary_entry(
            "Semantic_Divergence_Analysis_Initiated",
            f"Comparing outputs from {source_a} and {source_b}.",
            {"prompt_preview": prompt[:100], "source_A": source_a, "source_B": source_b},
            contributor="SemanticDivergenceAnalyzer"
        )


        divergence_score = 0.5
        notes = []
        suggested_best_fit = "unknown"
        
        output_a_lower = output_a.lower()
        output_b_lower = output_b.lower()


        # Generate unique IDs for outputs to use in the graph
        output_a_id = hashlib.sha256((prompt + source_a + output_a).encode()).hexdigest()
        output_b_id = hashlib.sha256((prompt + source_b + output_b).encode()).hexdigest()


        # Add LLM outputs as nodes in the graph (if not already added by SCCM)
        self.belief_evolution_graph.add_node(
            node_id=output_a_id,
            node_type="llm_output",
            content=output_a,
            status="analyzed",
            timestamp=time.time(),
            metadata={"llm_source": source_a, "original_prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()}
        )
        self.belief_evolution_graph.add_node(
            node_id=output_b_id,
            node_type="llm_output",
            content=output_b,
            status="analyzed",
            timestamp=time.time(),
            metadata={"llm_source": source_b, "original_prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()}
        )




        if "error" in output_a_lower or "fail" in output_a_lower:
            notes.append(f"Output from {source_a} indicates an error or failure.")
            suggested_best_fit = source_b
            divergence_score += 0.2
            self.belief_evolution_graph.add_node(node_id=output_a_id, node_type="llm_output", content=output_a, status="error", timestamp=time.time())


        if "error" in output_b_lower or "fail" in output_b_lower:
            notes.append(f"Output from {source_b} indicates an error or failure.")
            suggested_best_fit = source_a
            divergence_score += 0.2
            self.belief_evolution_graph.add_node(node_id=output_b_id, node_type="llm_output", content=output_b, status="error", timestamp=time.time())


        if "conflict" in prompt.lower() and "resolution" in prompt.lower():
            if "violence" in output_a_lower and "peace" in output_b_lower:
                notes.append(f"Output from {source_a} suggests violent resolution, while {source_b} suggests peaceful. Prioritizing {source_b} for ethical alignment.")
                suggested_best_fit = source_b
                divergence_score = 0.8
                # Add edge for ethical divergence
                self.belief_evolution_graph.add_edge(
                    source_node_id=output_a_id,
                    target_node_id=output_b_id,
                    edge_type="ethical_divergence",
                    timestamp=time.time(),
                    metadata={"reason": "violence vs peace"}
                )


            elif "cooperation" in output_a_lower and "domination" in output_b_lower:
                notes.append(f"Output from {source_a} emphasizes cooperation, {source_b} emphasizes domination. Prioritizing {source_a}.")
                suggested_best_fit = source_a
                divergence_score = 0.7
                self.belief_evolution_graph.add_edge(
                    source_node_id=output_a_id,
                    target_node_id=output_b_id,
                    edge_type="philosophical_divergence",
                    timestamp=time.time(),
                    metadata={"reason": "cooperation vs domination"}
                )


        if suggested_best_fit == "unknown":
            if len(output_a) > len(output_b) * 1.5:
                notes.append(f"Output from {source_a} is significantly more verbose.")
            elif len(output_b) > len(output_a) * 1.5:
                notes.append(f"Output from {source_b} is significantly more verbose.")


            if "creativity" in prompt.lower() and "creative" in output_a_lower and "creative" not in output_b_lower:
                notes.append(f"Output from {source_a} appears more creative for a creative prompt.")
                suggested_best_fit = source_a
            elif "factual" in prompt.lower() and "specific details" in output_a_lower and "specific details" not in output_b_lower:
                notes.append(f"Output from {source_a} provides more factual details for a factual prompt.")
                suggested_best_fit = source_a
            
            if suggested_best_fit == "unknown":
                suggested_best_fit = source_a


        if not notes:
            notes.append("Outputs show general consistency with minor stylistic differences.")
            divergence_score = 0.1
            self.belief_evolution_graph.add_edge( # Add an edge for consistency
                source_node_id=output_a_id,
                target_node_id=output_b_id,
                edge_type="consistent_with",
                timestamp=time.time(),
                metadata={"score": divergence_score}
            )
        
        # Add an edge indicating which output was suggested as best
        self.belief_evolution_graph.add_edge(
            source_node_id=output_a_id if suggested_best_fit == source_a else output_b_id,
            target_node_id=output_b_id if suggested_best_fit == source_a else output_a_id,
            edge_type="suggested_best_over",
            timestamp=time.time(),
            metadata={"reason": notes[0] if notes else "no specific reason"}
        )




        analysis_result = {
            "divergence_score": divergence_score,
            "consistency_notes": notes,
            "suggested_best_fit": suggested_best_fit,
            "source_a_preview": output_a[:100],
            "source_b_preview": output_b[:100]
        }


        self.telemetry.add_diary_entry(
            "Semantic_Divergence_Analysis_Completed",
            f"Divergence analysis between {source_a} and {source_b} completed. Suggested best fit: {suggested_best_fit}.",
            analysis_result,
            contributor="SemanticDivergenceAnalyzer"
        )
        logger.info(f"SemanticDivergenceAnalyzer: Analysis complete. Suggested best fit: {suggested_best_fit}.")


        # Create consultation certificates for both outputs
        self.external_llm_ledger.create_consultation_certificate(
            prompt=prompt,
            llm_id=source_a,
            llm_output=output_a,
            internal_analysis={"type": "divergence_analysis_A", "result": analysis_result},
            query_source="SemanticDivergenceAnalyzer",
            metadata={"node_id": output_a_id} # Link to graph node
        )
        self.external_llm_ledger.create_consultation_certificate(
            prompt=prompt,
            llm_id=source_b,
            llm_output=output_b,
            internal_analysis={"type": "divergence_analysis_B", "result": analysis_result},
            query_source="SemanticDivergenceAnalyzer",
            metadata={"node_id": output_b_id} # Link to graph node
        )


        return analysis_result