# layer4_llm_client.py
import logging
import os
import asyncio
import httpx # ADDED: For real async HTTP requests (conceptual use)
import json # For parsing JSON responses
from typing import Dict, List, Any, Optional


# Assuming GeminiApiClient is available
# from gemini_api_client import GeminiApiClient
# from telemetry_service import TelemetryService # For logging prompt preview and response metadata


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Layer4LLMClient:
    """
    Layer 4: Operational LLM Gateway.
    Provides a generic interface to query various LLMs (Gemini, local OSS models).
    """
    def __init__(self, gemini_api_client: Any, telemetry_service: Any): # Added telemetry_service
        self.gemini_client = gemini_api_client
        self.telemetry = telemetry_service # Store telemetry service
        self.local_llm_config: Dict[str, Any] = {} # Configuration for local OSS LLMs
        self._load_local_llm_config()
        self.client = httpx.AsyncClient() # Initialize an async HTTP client (conceptual)
        logger.info("Layer4LLMClient initialized.")


    def _load_local_llm_config(self):
        """
        Loads configuration for local LLMs, sourcing API keys from .env.
        """
        self.local_llm_config = {
            "ollama_local_model": {
                "api_base_url": os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434"),
                "model_name": os.getenv("OLLAMA_MODEL_NAME", "llama2"),
                "available": False # Will be set to True if connection is successful
            },
            "transformers_local_model": {
                "model_path": os.getenv("TRANSFORMERS_MODEL_PATH"),
                "tokenizer_path": os.getenv("TRANSFORMERS_TOKENIZER_PATH"),
                "available": False
            }
        }
        # Check connection for backend availability
        asyncio.create_task(self._check_all_backend_connections()) # Run connection checks in background
        logger.info("Layer4LLMClient: Local LLM configurations loaded (conceptual).")
        if not os.getenv("GEMINI_API_KEY"):
             logger.warning("GEMINI_API_KEY not found in .env. Gemini client might not function.")
        if not os.getenv("OLLAMA_API_BASE_URL"):
             logger.warning("OLLAMA_API_BASE_URL not found in .env. Ollama client might not function.")


    async def _check_all_backend_connections(self):
        """
        Add connection check for backend availability.
        Checks the availability of all configured LLM backends.
        """
        logger.info("Layer4LLMClient: Checking LLM backend connections...")
        # Check Gemini
        try:
            # Conceptual: Ping Gemini API. GeminiApiClient doesn't have a simple ping.
            # A real check would be a very small, cheap query.
            # For now, rely on its internal error handling.
            logger.debug("Gemini connection assumed available if API key is present.")
            self.telemetry.add_diary_entry(
                "LLMClient_Backend_Check",
                "Gemini backend connection status: Assumed OK.",
                {"model": "gemini-2.0-flash", "status": "assumed_ok"},
                contributor="Layer4LLMClient"
            )
        except Exception as e:
            logger.error(f"Gemini backend connection check failed: {e}")
            self.telemetry.add_diary_entry(
                "LLMClient_Backend_Check",
                f"Gemini backend connection status: FAILED - {e}",
                {"model": "gemini-2.0-flash", "status": "failed", "error": str(e)},
                contributor="Layer4LLMClient", severity="error"
            )


        # Check Ollama local model
        ollama_config = self.local_llm_config["ollama_local_model"]
        if ollama_config["api_base_url"]:
            try:
                # Conceptual: Ping Ollama API endpoint
                # async with self.client.get(f"{ollama_config['api_base_url']}/api/tags", timeout=5) as response:
                #     response.raise_for_status()
                #     ollama_config["available"] = True
                #     logger.info(f"Ollama backend at {ollama_config['api_base_url']} is available.")
                # For conceptual demo:
                ollama_config["available"] = True
                logger.info(f"Ollama backend at {ollama_config['api_base_url']} is conceptually available.")
                self.telemetry.add_diary_entry(
                    "LLMClient_Backend_Check",
                    f"Ollama backend connection status: OK.",
                    {"model": "ollama_local_model", "status": "ok", "url": ollama_config['api_base_url']},
                    contributor="Layer4LLMClient"
                )
            except Exception as e:
                ollama_config["available"] = False
                logger.error(f"Ollama backend connection check failed: {e}")
                self.telemetry.add_diary_entry(
                    "LLMClient_Backend_Check",
                    f"Ollama backend connection status: FAILED - {e}",
                    {"model": "ollama_local_model", "status": "failed", "url": ollama_config['api_base_url'], "error": str(e)},
                    contributor="Layer4LLMClient", severity="error"
                )
        
        # Check Transformers local model (conceptual, might just be file existence)
        transformers_config = self.local_llm_config["transformers_local_model"]
        if transformers_config["model_path"] and transformers_config["tokenizer_path"]:
            # Conceptual: Check if model files exist
            # if os.path.exists(transformers_config["model_path"]) and os.path.exists(transformers_config["tokenizer_path"]):
            transformers_config["available"] = True
            logger.info("Transformers local model files are conceptually available.")
            self.telemetry.add_diary_entry(
                "LLMClient_Backend_Check",
                f"Transformers local model status: OK.",
                {"model": "transformers_local_model", "status": "ok", "path": transformers_config['model_path']},
                contributor="Layer4LLMClient"
            )
            # else:
            #     transformers_config["available"] = False
            #     logger.warning("Transformers local model files not found.")
        else:
            transformers_config["available"] = False
            logger.warning("Transformers local model paths not configured.")
            self.telemetry.add_diary_entry(
                "LLMClient_Backend_Check",
                f"Transformers local model status: FAILED - paths not configured.",
                {"model": "transformers_local_model", "status": "failed"},
                contributor="Layer4LLMClient", severity="error"
            )


    async def query(self,
                    model_name: str,
                    prompt: str,
                    chat_history: Optional[List[Dict[str, Any]]] = None,
                    generation_config: Optional[Dict[str, Any]] = None,
                    retries: int = 3, # Include retry logic
                    delay: float = 1.0 # Initial delay for retries
                   ) -> Optional[Dict[str, Any]]: # Return response metadata
        """
        Queries the specified LLM model with retry logic.
        Returns response metadata (e.g., latency, token count, cost estimates).
        """
        logger.info(f"Layer4LLMClient: Querying model '{model_name}'.")
        self.telemetry.add_diary_entry( # Log first 100 characters of prompt in telemetry
            "LLMClient_Prompt_Sent",
            f"Prompt sent to {model_name}: {prompt[:100]}...",
            {"model": model_name, "prompt_preview": prompt[:100]},
            contributor="Layer4LLMClient"
        )


        attempt = 0
        while attempt < retries:
            start_time = time.time()
            try:
                if model_name.startswith("gemini"):
                    response_text = await self.gemini_client.generate_content(prompt, chat_history, generation_config)
                    # For conceptual purposes, simulate token count and cost for Gemini
                    token_count = len(prompt.split()) + len(response_text.split()) if response_text else 0
                    cost_estimate = token_count * self.gemini_client.api_cost_per_token # Assuming GeminiApiClient has this
                elif model_name == "ollama_local_model" and self.local_llm_config["ollama_local_model"]["available"]:
                    # CONCEPTUAL: Call to a local Ollama client
                    await asyncio.sleep(0.05) # Simulate async local LLM inference
                    response_text = f"Conceptual response from local Ollama model '{self.local_llm_config['ollama_local_model']['model_name']}' for: {prompt[:50]}..."
                    token_count = len(prompt.split()) + len(response_text.split())
                    cost_estimate = 0.0 # Local models are free
                elif model_name == "transformers_local_model" and self.local_llm_config["transformers_local_model"]["available"]:
                    # CONCEPTUAL: Call to a local transformers model
                    await asyncio.sleep(0.02) # Simulate async local LLM inference
                    response_text = f"Conceptual response from local Transformers model for: {prompt[:50]}..."
                    token_count = len(prompt.split()) + len(response_text.split())
                    cost_estimate = 0.0 # Local models are free
                else:
                    logger.warning(f"Layer4LLMClient: Model '{model_name}' not recognized or not available.")
                    response_text = None
                    token_count = 0
                    cost_estimate = 0.0


                latency = time.time() - start_time


                if response_text:
                    response_metadata = {
                        "model_name": model_name,
                        "response_text": response_text,
                        "latency_seconds": float(latency),
                        "token_count": token_count,
                        "cost_estimate": float(cost_estimate),
                        "success": True,
                        "attempt": attempt + 1
                    }
                    self.telemetry.add_diary_entry(
                        "LLMClient_Query_Success",
                        f"Query to {model_name} successful. Latency: {latency:.2f}s.",
                        response_metadata,
                        contributor="Layer4LLMClient"
                    )
                    return response_metadata
                else:
                    raise Exception("LLM returned no response text.")


            except Exception as e:
                attempt += 1
                logger.error(f"Layer4LLMClient: Attempt {attempt}/{retries} to query '{model_name}' failed: {e}")
                self.telemetry.add_diary_entry(
                    "LLMClient_Query_Failed_Attempt",
                    f"Attempt {attempt}/{retries} to query {model_name} failed.",
                    {"model": model_name, "prompt_preview": prompt[:100], "error": str(e), "attempt": attempt},
                    contributor="Layer4LLMClient",
                    severity="warning" if attempt < retries else "error"
                )
                if attempt < retries:
                    await asyncio.sleep(delay * (2 ** (attempt - 1))) # Exponential backoff
                else:
                    self.telemetry.add_diary_entry(
                        "LLMClient_Query_Failed_Max_Retries",
                        f"Query to {model_name} failed after {retries} attempts.",
                        {"model": model_name, "prompt_preview": prompt[:100], "error": str(e)},
                        contributor="Layer4LLMClient",
                        severity="critical"
                    )
                    return {"success": False, "reason": f"Failed after {retries} attempts: {e}"}


        return {"success": False, "reason": "Unknown error or no retries left."}