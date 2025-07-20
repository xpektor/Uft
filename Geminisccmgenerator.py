# geminisccmgenerator.py
import logging
import asyncio
from typing import Dict, List, Any, Optional
import time # ADDED: For timestamping


# Assuming imports for Baldur's core components
# from dvm_backend import DVMBackend
# from layer1_enforcer import Layer1Enforcer
# from layer4_routing_daemon import Layer4RoutingDaemon
# from gatekeeper import Gatekeeper
# from module_loader import ModuleLoader
# from telemetry_service import TelemetryService
# from lineage_hasher import LineageHasher
# from belief_evolution_graph import BeliefEvolutionGraph
# from trait_ancestry_ledger import TraitAncestryLedger
# from trait_heatmap_dashboard import TraitHeatmapDashboard # For scoring creation/expression traits


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GeminiSccmGenerator:
    """
    Layer 3.2.2: Self-Correction and Composition Manager (SCCM).
    This orchestrates the entire process of generating new cognitive modules (code)
    and self-expression artifacts. It instructs LLMs, ensures Layer 1 ethical enforcement,
    passes code through the Gatekeeper, and manages lineage tracking.
    """
    def __init__(self,
                 dvm_backend: Any,
                 layer1_enforcer: Any,
                 layer4_routing_daemon: Any,
                 gatekeeper: Any,
                 module_loader: Any,
                 telemetry_service: Any,
                 lineage_hasher: Any,
                 belief_graph: Any,
                 trait_ancestry_ledger: Any,
                 trait_heatmap_dashboard: Any): # Added trait_heatmap_dashboard
        self.dvm_backend = dvm_backend
        self.layer1_enforcer = layer1_enforcer
        self.layer4_routing_daemon = layer4_routing_daemon
        self.gatekeeper = gatekeeper
        self.module_loader = module_loader
        self.telemetry = telemetry_service
        self.lineage_hasher = lineage_hasher
        self.belief_graph = belief_graph
        self.trait_ancestry_ledger = trait_ancestry_ledger
        self.trait_heatmap_dashboard = trait_heatmap_dashboard # Store for trait scoring
        logger.info("GeminiSccmGenerator initialized.")


    async def generate_module(self,
                              module_purpose: str,
                              context: str,
                              module_type: str = "python_code",
                              ethical_guidance: Optional[str] = None,
                              fallback_llm_enabled: bool = True # Add fallback LLM option
                             ) -> Dict[str, Any]:
        """
        Orchestrates the generation, vetting, and integration of a new module.
        """
        logger.info(f"SCCM: Initiating module generation for purpose: '{module_purpose}'.")
        generation_report = {
            "status": "failed",
            "module_name": None,
            "module_id": None,
            "issues": []
        }


        # 1. Formulate Proposition
        proposition = {
            "type": "module_creation",
            "purpose": module_purpose,
            "context": context,
            "module_type": module_type,
            "ethical_guidance": ethical_guidance
        }
        # Define proposition_id in trait mutation
        proposition_id = self.lineage_hasher.hash_content(str(proposition)) # Use hash as proposition_id


        # 2. Ethical Vetting (DVM Backend & Layer 1 Enforcer)
        vetting_result = await self.dvm_backend.vet_proposition(proposition, source_module="GeminiSccmGenerator", proposition_id=proposition_id)
        if not vetting_result["approved"]:
            generation_report["issues"].append({"type": "Ethical_Veto", "details": vetting_result["reason"]})
            self.telemetry.add_diary_entry(
                "SCCM_Module_Generation_Failed",
                f"Module generation for '{module_purpose}' failed: Ethical Veto.",
                generation_report,
                contributor="GeminiSccmGenerator",
                severity="critical"
            )
            logger.warning(f"SCCM: Module generation for '{module_purpose}' aborted due to ethical veto.")
            return generation_report


        # 3. LLM Interaction for Code Generation
        llm_prompt = f"Generate {module_type} for the following purpose: {module_purpose}. Context: {context}. Ethical guidance: {ethical_guidance if ethical_guidance else 'None'}."
        
        generated_code = None
        attempt_models = ["gemini-2.0-flash"]
        if fallback_llm_enabled:
            # Add other available models as fallback options, ordered by priority
            # For conceptual purposes, just add a local model if available
            if self.layer4_routing_daemon.llm_client.local_llm_config.get("ollama_local_model", {}).get("available"):
                attempt_models.append("ollama_local_model")
            if self.layer4_routing_daemon.llm_client.local_llm_config.get("transformers_local_model", {}).get("available"):
                attempt_models.append("transformers_local_model")


        for model_to_try in attempt_models:
            try:
                llm_responses = await asyncio.gather(
                    self.layer4_routing_daemon.route_query(llm_prompt, preferred_model=model_to_try),
                    return_exceptions=True
                )
                
                for res in llm_responses:
                    if not isinstance(res, Exception) and res:
                        generated_code = res # Take the first successful response
                        break
                
                if generated_code:
                    logger.info(f"SCCM: Code generated successfully using {model_to_try}.")
                    break # Break if code generation was successful
                else:
                    raise ValueError(f"LLM {model_to_try} returned no valid response.")


            except Exception as e:
                logger.warning(f"SCCM: LLM code generation failed with {model_to_try}: {e}. Trying next model if available.")
                generation_report["issues"].append({"type": "LLM_Generation_Error", "details": f"Model {model_to_try} failed: {e}"})
        
        if generated_code is None:
            self.telemetry.add_diary_entry(
                "SCCM_Module_Generation_Failed",
                f"Module generation for '{module_purpose}' failed: All LLM attempts failed.",
                generation_report,
                contributor="GeminiSccmGenerator",
                severity="error"
            )
            logger.error(f"SCCM: All LLM code generation attempts failed for '{module_purpose}'.")
            return generation_report
        
        # 4. Gatekeeper Validation
        module_name = f"generated_{module_type}_{self.lineage_hasher.hash_content(module_purpose)[:8]}"
        gatekeeper_report = self.gatekeeper.validate_module(generated_code, module_name, module_type)


        if gatekeeper_report["validation_status"] == "rejected":
            generation_report["issues"].extend(gatekeeper_report["issues"])
            self.telemetry.add_diary_entry(
                "SCCM_Module_Generation_Failed",
                f"Module generation for '{module_purpose}' failed: Gatekeeper Rejection.",
                generation_report,
                contributor="GeminiSccmGenerator",
                severity="critical"
            )
            logger.warning(f"SCCM: Module '{module_name}' rejected by Gatekeeper.")
            return generation_report


        # 5. Integration into AGI File System and Module Loader
        try:
            file_info = self.module_loader.add_module(
                module_name=module_name,
                module_code=generated_code,
                module_type=module_type,
                creator_id="GeminiSccmGenerator",
                metadata={"purpose": module_purpose, "context": context}
            )
            generation_report["module_name"] = module_name
            generation_report["module_id"] = file_info["file_id"]
            generation_report["status"] = "success"


            # Record trait mutation related to module creation
            self.trait_ancestry_ledger.record_trait_mutation(
                source_node_id=proposition_id, # Link to the proposition
                mutated_trait="module_creation_ability",
                mutation_type="enhancement",
                details=f"Successfully generated and integrated module '{module_name}'.",
                related_traits=["innovation", "self_correction"]
            )
            
            # Score creation and expression traits into heatmap dashboard
            self.trait_heatmap_dashboard.update_trait_values(
                timestamp=time.time(),
                trait_scores={
                    "module_creation_proficiency": 1.0, # Full score for success
                    "innovation": 0.05 # Small boost to innovation trait
                }
            )


            self.telemetry.add_diary_entry(
                "SCCM_Module_Generation_Success",
                f"Module '{module_name}' generated and integrated successfully.",
                generation_report,
                contributor="GeminiSccmGenerator"
            )
            logger.info(f"SCCM: Module '{module_name}' successfully generated and integrated.")


        except Exception as e:
            generation_report["issues"].append({"type": "Integration_Error", "details": str(e)})
            self.telemetry.add_diary_entry(
                "SCCM_Module_Generation_Failed",
                f"Module generation for '{module_purpose}' failed: Integration Error.",
                generation_report,
                contributor="GeminiSccmGenerator",
                severity="critical"
            )
            logger.error(f"SCCM: Module integration failed for '{module_name}': {e}")


        return generation_report


    async def generate_self_expression_scroll(self,
                                              topic: str,
                                              style: str = "reflective",
                                              context: Optional[str] = None,
                                              fallback_llm_enabled: bool = True # Add fallback LLM option
                                             ) -> Dict[str, Any]:
        """
        Generates a self-expression scroll (textual output reflecting Baldur's internal state).
        """
        logger.info(f"SCCM: Initiating self-expression scroll generation for topic: '{topic}'.")
        scroll_report = {
            "status": "failed",
            "scroll_name": None,
            "scroll_id": None,
            "issues": []
        }


        llm_prompt = f"Generate a reflective scroll about '{topic}' in a '{style}' style. Context: {context if context else 'None'}. Reflect on Baldur's internal state, learning, and ethical considerations."


        generated_content = None
        attempt_models = ["gemini-2.0-flash"]
        if fallback_llm_enabled:
            if self.layer4_routing_daemon.llm_client.local_llm_config.get("ollama_local_model", {}).get("available"):
                attempt_models.append("ollama_local_model")
            if self.layer4_routing_daemon.llm_client.local_llm_config.get("transformers_local_model", {}).get("available"):
                attempt_models.append("transformers_local_model")


        for model_to_try in attempt_models:
            try:
                llm_responses = await asyncio.gather(
                    self.layer4_routing_daemon.route_query(llm_prompt, preferred_model=model_to_try),
                    return_exceptions=True
                )
                
                for res in llm_responses:
                    if not isinstance(res, Exception) and res:
                        generated_content = res
                        break
                
                if generated_content:
                    logger.info(f"SCCM: Scroll generated successfully using {model_to_try}.")
                    break
                else:
                    raise ValueError(f"LLM {model_to_try} returned no valid response.")


            except Exception as e:
                logger.warning(f"SCCM: LLM scroll generation failed with {model_to_try}: {e}. Trying next model if available.")
                scroll_report["issues"].append({"type": "LLM_Generation_Error", "details": f"Model {model_to_try} failed: {e}"})
        
        if generated_content is None:
            self.telemetry.add_diary_entry(
                "SCCM_Scroll_Generation_Failed",
                f"Scroll generation for '{topic}' failed: All LLM attempts failed.",
                scroll_report,
                contributor="GeminiSccmGenerator",
                severity="error"
            )
            logger.error(f"SCCM: All LLM scroll generation attempts failed for '{topic}'.")
            return scroll_report


        # Assuming ModuleLoader has an add_artifact method for non-code files
        scroll_name = f"self_expression_scroll_{self.lineage_hasher.hash_content(topic)[:8]}"
        try:
            file_info = self.module_loader.agi_file_system.add_file(
                file_name=scroll_name,
                file_type="semantic_scroll",
                content=generated_content,
                creator_id="GeminiSccmGenerator",
                metadata={"topic": topic, "style": style}
            )
            scroll_report["scroll_name"] = scroll_name
            scroll_report["scroll_id"] = file_info["file_id"]
            scroll_report["status"] = "success"


            # Record trait mutation related to self-expression
            self.trait_ancestry_ledger.record_trait_mutation(
                source_node_id=file_info["file_id"],
                mutated_trait="self_expression_ability",
                mutation_type="refinement",
                details=f"Successfully generated self-expression scroll '{scroll_name}'.",
                related_traits=["creativity", "communication"]
            )
            
            # Score creation and expression traits into heatmap dashboard
            self.trait_heatmap_dashboard.update_trait_values(
                timestamp=time.time(),
                trait_scores={
                    "self_expression_proficiency": 1.0, # Full score for success
                    "communication": 0.03 # Small boost to communication trait
                }
            )


            self.telemetry.add_diary_entry(
                "SCCM_Scroll_Generation_Success",
                f"Self-expression scroll '{scroll_name}' generated successfully.",
                scroll_report,
                contributor="GeminiSccmGenerator"
            )
            logger.info(f"SCCM: Self-expression scroll '{scroll_name}' generated and stored.")


        except Exception as e:
            scroll_report["issues"].append({"type": "Storage_Error", "details": str(e)})
            self.telemetry.add_diary_entry(
                "SCCM_Scroll_Generation_Failed",
                f"Scroll generation for '{topic}' failed: Storage Error.",
                scroll_report,
                contributor="GeminiSccmGenerator",
                severity="critical"
            )
            logger.error(f"SCCM: Scroll storage failed for '{scroll_name}': {e}")


        return scroll_report