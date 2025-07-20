# layer4_routing_daemon.py
import logging
import random
from typing import Dict, List, Any, Optional
import asyncio


# Assuming Layer4LLMClient, TelemetryService, and AbstractedTraitVectorizer are available
# from layer4_llm_client import Layer4LLMClient
# from telemetry_service import TelemetryService
# from abstracted_trait_vectorizer import AbstractedTraitVectorizer # For matching model traits to prompt traits


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Layer4RoutingDaemon:
    """
    Layer 4: LLM Routing.
    Intelligently selects the "best" available LLM for a given query based on
    configured preferences, internal heuristics, and potentially real-time performance.
    """
    def __init__(self, llm_client: Any, telemetry_service: Any, trait_vectorizer: Any): # Added trait_vectorizer
        self.llm_client = llm_client
        self.telemetry = telemetry_service
        self.trait_vectorizer = trait_vectorizer # Store for trait matching
        self.available_models: Dict[str, Dict[str, Any]] = {
            "gemini-2.0-flash": {"priority": 1, "cost_per_token": 0.0001, "capabilities": ["creative", "complex_reasoning", "multimodal"], "traits": ["ethical_alignment", "creativity", "complex_problem_solving"]},
            "ollama_local_model": {"priority": 2, "cost_per_token": 0.0, "capabilities": ["general_text", "summarization", "code_generation_basic"], "traits": ["efficiency", "factual_recall", "basic_reasoning"]},
            "transformers_local_model": {"priority": 3, "cost_per_token": 0.0, "capabilities": ["simple_qa", "sentiment_analysis"], "traits": ["speed", "pattern_recognition", "data_analysis"]}
        }
        logger.info("Layer4RoutingDaemon initialized with available models.")


    async def route_query(self,
                          prompt: str,
                          preferred_model: Optional[str] = None,
                          required_capabilities: Optional[List[str]] = None,
                          max_cost: Optional[float] = None,
                          confidence_threshold: Optional[float] = None,
                          domain_override_hint: Optional[str] = None,
                          dry_run: bool = False # Simulate dry-run decision audit
                         ) -> Optional[str]:
        """
        Routes a query to the most appropriate LLM based on criteria.
        """
        logger.info(f"Routing query: '{prompt[:50]}...' with preferences: preferred={preferred_model}, capabilities={required_capabilities}, max_cost={max_cost}, dry_run={dry_run}.")


        prompt_vector = self.trait_vectorizer.vectorize_content(prompt)
        if prompt_vector is None:
            logger.warning("Layer4RoutingDaemon: Could not vectorize prompt. Skipping trait-based routing.")


        candidate_models = []
        for model_name, config in self.available_models.items():
            # Check if model is available (conceptual)
            if not self.llm_client.local_llm_config.get(model_name, {}).get("available", True) and not model_name.startswith("gemini"):
                continue


            # Check preferred model
            if preferred_model and model_name != preferred_model:
                continue


            # Check required capabilities
            if required_capabilities:
                if not all(cap in config["capabilities"] for cap in required_capabilities):
                    continue


            # Check max cost
            if max_cost is not None and config["cost_per_token"] > max_cost:
                continue


            # Apply domain override hint
            if domain_override_hint:
                if domain_override_hint == "ethical_vetting" and model_name != "gemini-2.0-flash":
                    continue
                if domain_override_hint == "code_generation" and model_name == "transformers_local_model":
                    continue


            # Match model traits to prompt traits via vectorizer
            model_traits = config.get("traits", [])
            if prompt_vector is not None and model_traits:
                # Conceptual: Calculate similarity between prompt vector and model's trait vectors
                # This would require pre-vectorized trait definitions for each model
                model_trait_vectors = {trait: self.trait_vectorizer.vectorize_content(trait) for trait in model_traits}
                # Filter out None vectors
                model_trait_vectors = {k: v for k, v in model_trait_vectors.items() if v is not None}


                if model_trait_vectors:
                    # Average similarity to model's traits
                    avg_trait_similarity = np.mean([
                        np.dot(prompt_vector, mv) / (np.linalg.norm(prompt_vector) * np.linalg.norm(mv))
                        for mv in model_trait_vectors.values()
                    ])
                    # Incorporate this similarity into a routing score or filter
                    # For now, a simple conceptual boost to priority
                    if avg_trait_similarity > 0.7: # Arbitrary threshold
                        candidate_models.append((model_name, config["priority"] * 0.5)) # Boost priority
                    else:
                        candidate_models.append((model_name, config["priority"]))
                else:
                    candidate_models.append((model_name, config["priority"]))
            else:
                candidate_models.append((model_name, config["priority"]))


        if not candidate_models:
            self.telemetry.add_diary_entry(
                "LLM_Routing_Failed",
                f"No suitable LLM found for query: '{prompt[:50]}...'",
                {"prompt": prompt, "preferences": {"preferred": preferred_model, "capabilities": required_capabilities, "max_cost": max_cost}},
                contributor="Layer4RoutingDaemon",
                severity="warning"
            )
            logger.warning(f"Layer4RoutingDaemon: No suitable LLM found for query: '{prompt[:50]}...'.")
            return None


        # Sort by priority (lower number is higher priority)
        candidate_models.sort(key=lambda x: x[1])


        selected_model_name = candidate_models[0][0] # Select highest priority candidate


        # Execute confidence_threshold filtering
        # This is conceptual. In a real system, Baldur would need a mechanism
        # to assess the expected confidence of a model's response for a given prompt.
        # This might involve meta-LLMs, or a Bayesian inference system.
        if confidence_threshold is not None:
            conceptual_confidence = self._estimate_conceptual_confidence(selected_model_name, prompt)
            if conceptual_confidence < confidence_threshold:
                logger.warning(f"Layer4RoutingDaemon: Selected model '{selected_model_name}' has low conceptual confidence ({conceptual_confidence:.2f}) for this prompt. Attempting fallback.")
                # Add routing fallback with ranked rationale
                fallback_models = [m for m, p in candidate_models if m != selected_model_name]
                if fallback_models:
                    selected_model_name = fallback_models[0] # Take next best
                    logger.info(f"Layer4RoutingDaemon: Falling back to '{selected_model_name}' due to low confidence.")
                else:
                    self.telemetry.add_diary_entry(
                        "LLM_Routing_Failed_Confidence",
                        f"No suitable LLM found with required confidence for query: '{prompt[:50]}...'",
                        {"prompt": prompt, "selected_model": selected_model_name, "confidence": conceptual_confidence},
                        contributor="Layer4RoutingDaemon",
                        severity="warning"
                    )
                    logger.warning("Layer4RoutingDaemon: No fallback model available with sufficient confidence.")
                    return None




        # Simulate dry-run decision audit
        if dry_run:
            dry_run_report = {
                "status": "dry_run_complete",
                "selected_model": selected_model_name,
                "reasoning": f"Conceptual dry run: Would have routed to {selected_model_name} based on current criteria.",
                "prompt_preview": prompt[:100] + "..."
            }
            self.telemetry.add_diary_entry(
                "LLM_Routing_Dry_Run",
                f"Dry run decision for query: '{prompt[:50]}...'. Selected: {selected_model_name}.",
                dry_run_report,
                contributor="Layer4RoutingDaemon",
                severity="debug"
            )
            logger.info(f"Layer4RoutingDaemon: Dry run for query. Would select: '{selected_model_name}'.")
            return f"DRY_RUN_RESULT: Would have queried {selected_model_name}." # Return a distinct dry run result


        self.telemetry.add_diary_entry(
            "LLM_Routing_Success",
            f"Query routed to '{selected_model_name}'.",
            {"prompt": prompt, "selected_model": selected_model_name},
            contributor="Layer4RoutingDaemon",
            severity="low"
        )
        logger.info(f"Layer4RoutingDaemon: Routing query to '{selected_model_name}'.")


        # Echo routing profile into dashboard module (conceptual)
        # Assuming a dashboard component can receive updates
        # self.trait_heatmap_dashboard.update_routing_profile(selected_model_name, time.time())
        self.telemetry.add_diary_entry(
            "Dashboard_LLM_Routing_Event",
            f"LLM routed to {selected_model_name}.",
            {"model": selected_model_name, "prompt_hash": self.llm_client.gemini_client.lineage_hasher.hash_content(prompt)}, # Assuming client has hasher
            contributor="TraitHeatmapDashboard_Input"
        )


        # Now, query the selected model
        try:
            response = await self.llm_client.query(selected_model_name, prompt)
            return response
        except Exception as e:
            self.telemetry.add_diary_entry(
                "LLM_Query_Failed",
                f"Query to '{selected_model_name}' failed: {e}",
                {"model": selected_model_name, "prompt": prompt, "error": str(e)},
                contributor="Layer4RoutingDaemon",
                severity="error"
            )
            logger.error(f"Layer4RoutingDaemon: Query to '{selected_model_name}' failed: {e}")
            return None


    def _estimate_conceptual_confidence(self, model_name: str, prompt: str) -> float:
        """
        CONCEPTUAL: Estimates a conceptual confidence score for a model's response to a prompt.
        This would be a complex heuristic or a meta-LLM.
        """
        # Simple simulation: Gemini is generally high confidence, small models lower
        if model_name.startswith("gemini"):
            return random.uniform(0.85, 0.99)
        elif "ollama" in model_name:
            return random.uniform(0.6, 0.85)
        else: # transformers_local_model
            return random.uniform(0.4, 0.7)