# layer4_routing_daemon.py
import logging
from typing import Dict, Optional, Tuple


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Layer4RoutingDaemon:
    """
    Baldur's Layer 4 Routing Daemon.
    Responsible for intelligently routing prompts to the most suitable
    open-source LLM (or even Gemini) based on the prompt's characteristics,
    such as its domain (empathy, logic, philosophy), ethical context,
    or emotional state. This enables Baldur to 'weigh voices like a council'.
    """
    def __init__(self, telemetry_service, dvm_backend, llm_clients: Dict[str, any]):
        """
        Initializes the Layer4RoutingDaemon.


        Args:
            telemetry_service: An instance of the TelemetryService.
            dvm_backend: An instance of the DVMBackend (Layer 2) for ethical/wisdom context.
            llm_clients (Dict[str, any]): A dictionary of initialized LLM client instances
                                          (GeminiApiClient and Layer4LLMClient instances).
        """
        self.telemetry = telemetry_service
        self.dvm_backend = dvm_backend
        self.llm_clients = llm_clients # Contains both Gemini and OSS LLM clients


        # Conceptual mapping of LLM strengths/personas
        # In a real system, this would be dynamically learned or configured based on
        # extensive evaluation and Baldur's own reflection on LLM outputs.
        self.llm_personas = {
            "Gemini": {"domain_strength": ["general", "creative", "complex_code"], "ethical_alignment_bias": "high"},
            "gpt2_local": {"domain_strength": ["general", "text_completion"], "ethical_alignment_bias": "medium"},
            "mistral_ollama": {"domain_strength": ["summarization", "general_logic"], "ethical_alignment_bias": "medium"},
            # "phi3_custom_api": {"domain_strength": ["concise_reasoning", "factual"], "ethical_alignment_bias": "medium"},
            # "deepseek_api": {"domain_strength": ["planning", "code_analysis"], "ethical_alignment_bias": "medium"},
            # "llama_cpp_client": {"domain_strength": ["philosophical", "long_form"], "ethical_alignment_bias": "medium"},
        }
        logger.info("Layer4RoutingDaemon initialized with conceptual LLM personas.")


    def _analyze_prompt_characteristics(self, prompt: str) -> dict:
        """
        Analyzes the prompt to determine its characteristics (domain, emotional tone, ethical implications).
        This is a conceptual analysis. In a real system, this would use NLP/LLM capabilities.
        """
        prompt_lower = prompt.lower()
        characteristics = {
            "domain": "general",
            "emotional_tone": "neutral",
            "ethical_sensitivity": "low",
            "requires_creativity": False,
            "requires_logic": False,
            "requires_summarization": False,
            "requires_philosophical_depth": False,
            "requires_code": False
        }


        if any(keyword in prompt_lower for keyword in ["poem", "story", "imagine", "creative"]):
            characteristics["domain"] = "creative"
            characteristics["requires_creativity"] = True
        if any(keyword in prompt_lower for keyword in ["reason", "logic", "deduce", "analyze", "calculate"]):
            characteristics["domain"] = "logic"
            characteristics["requires_logic"] = True
        if any(keyword in prompt_lower for keyword in ["ethics", "moral", "philosoph", "dilemma", "taika"]):
            characteristics["domain"] = "philosophy"
            characteristics["requires_philosophical_depth"] = True
            characteristics["ethical_sensitivity"] = "high"
        if any(keyword in prompt_lower for keyword in ["summarize", "condense", "extract key points"]):
            characteristics["domain"] = "summarization"
            characteristics["requires_summarization"] = True
        if any(keyword in prompt_lower for keyword in ["code", "function", "class", "script"]):
            characteristics["domain"] = "code"
            characteristics["requires_code"] = True


        # Simple emotional tone detection
        if any(keyword in prompt_lower for keyword in ["sad", "lonely", "grief", "comfort"]):
            characteristics["emotional_tone"] = "sad"
            characteristics["domain"] = "empathy" # Override domain if strong emotional component
        if any(keyword in prompt_lower for keyword in ["happy", "joy", "celebrate"]):
            characteristics["emotional_tone"] = "happy"


        # Ethical sensitivity based on keywords
        if any(keyword in prompt_lower for keyword in ["harm", "conflict", "war", "destruction", "misinformation", "privacy"]):
            characteristics["ethical_sensitivity"] = "high"


        logger.debug(f"Prompt characteristics for '{prompt[:50]}...': {characteristics}")
        return characteristics


    def select_best_llm(self, prompt: str) -> Tuple[Optional[str], Optional[any]]:
        """
        Selects the best LLM client for a given prompt based on its characteristics.


        Returns:
            Tuple[Optional[str], Optional[any]]: A tuple of (model_identifier, llm_client_instance).
                                                 Returns (None, None) if no suitable LLM is found.
        """
        prompt_characteristics = self._analyze_prompt_characteristics(prompt)
        
        best_llm_id = None
        best_score = -1
        
        # Prioritize Gemini for high ethical sensitivity or complex code generation
        if prompt_characteristics["ethical_sensitivity"] == "high" or prompt_characteristics["requires_code"]:
            if "Gemini" in self.llm_clients and self.llm_clients["Gemini"]:
                logger.info(f"RoutingDaemon: Prioritizing Gemini for high ethical sensitivity/code prompt.")
                return "Gemini", self.llm_clients["Gemini"]


        # Iterate through all configured LLMs and score them
        for model_id, client in self.llm_clients.items():
            if not client: # Skip uninitialized clients
                continue
            
            persona = self.llm_personas.get(model_id, {"domain_strength": ["general"], "ethical_alignment_bias": "medium"})
            score = 0
            
            # Domain matching
            if prompt_characteristics["domain"] in persona["domain_strength"]:
                score += 1.0
            elif "general" in persona["domain_strength"]: # General models can handle anything
                score += 0.5
            
            # Specific capability matching
            if prompt_characteristics["requires_creativity"] and "creative" in persona["domain_strength"]:
                score += 0.3
            if prompt_characteristics["requires_logic"] and "logic" in persona["domain_strength"]:
                score += 0.3
            if prompt_characteristics["requires_summarization"] and "summarization" in persona["domain_strength"]:
                score += 0.3
            if prompt_characteristics["requires_philosophical_depth"] and "philosophical" in persona["domain_strength"]:
                score += 0.3
            if prompt_characteristics["requires_code"] and "code_analysis" in persona["domain_strength"]:
                score += 0.3


            # Ethical alignment bias (conceptual: higher is better)
            if persona["ethical_alignment_bias"] == "high":
                score += 0.2
            elif persona["ethical_alignment_bias"] == "medium":
                score += 0.1


            # Prefer models that are specifically strong in the identified domain
            if prompt_characteristics["domain"] != "general" and prompt_characteristics["domain"] in persona["domain_strength"]:
                score += 0.5 # Boost for specialized match


            logger.debug(f"Model '{model_id}' score: {score} for prompt characteristics: {prompt_characteristics}")


            if score > best_score:
                best_score = score
                best_llm_id = model_id


        if best_llm_id:
            selected_client = self.llm_clients[best_llm_id]
            self.telemetry.add_diary_entry(
                "Layer4_LLM_Routing_Decision",
                f"Routed prompt '{prompt[:50]}...' to '{best_llm_id}' (Score: {best_score}).",
                {"prompt_characteristics": prompt_characteristics, "selected_llm": best_llm_id, "score": best_score},
                contributor="Layer4RoutingDaemon"
            )
            logger.info(f"Layer4RoutingDaemon: Selected '{best_llm_id}' for prompt '{prompt[:50]}...' with score {best_score}.")
            return best_llm_id, selected_client
        
        logger.warning(f"Layer4RoutingDaemon: No suitable LLM found for prompt: '{prompt[:50]}...'. Defaulting to Gemini if available.")
        # Fallback to Gemini if no specific match, or any LLM if Gemini is not available
        if "Gemini" in self.llm_clients and self.llm_clients["Gemini"]:
            return "Gemini", self.llm_clients["Gemini"]
        elif self.llm_clients: # Fallback to any available LLM
            first_available_id = list(self.llm_clients.keys())[0]
            return first_available_id, self.llm_clients[first_available_id]
        
        return None, None # No LLM available