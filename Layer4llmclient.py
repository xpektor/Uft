# layer4_llm_client.py
import logging
import os
import torch # Required by transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed # Import necessary classes
import requests
import json


# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Layer4LLMClient:
    """
    Baldur's Layer 4 Operational LLM Gateway.
    This client provides an interface to query various open-source Large Language Models (OSS LLMs).
    It acts as a conceptual bridge to external generative and reasoning capabilities.
    Supports different backends like Hugging Face transformers (local) or Ollama API.
    """
    def __init__(self, model_identifier: str, backend: str = "transformers_local", api_url: str = None, temperature: float = 0.7, max_new_tokens: int = 100):
        """
        Initializes the Layer4LLMClient by configuring the specified backend and model.


        Args:
            model_identifier (str): The model ID (e.g., "gpt2", "mistral", "phi3").
            backend (str): The type of backend to use ("transformers_local", "ollama_api", "custom_api").
            api_url (str, optional): The API endpoint for the LLM if it's an API backend.
            temperature (float): Controls the randomness of the output. Higher values mean more random. (0.0 to 1.0+)
            max_new_tokens (int): The maximum number of new tokens to generate in the response.
        """
        self.model_identifier = model_identifier
        self.backend = backend
        self.api_url = api_url
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.headers = {'Content-Type': 'application/json'} # Default for API calls


        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"


        logger.info(f"Layer4LLMClient: Initializing for model '{model_identifier}' with backend '{backend}' on device: {self.device}")


        if self.backend == "transformers_local":
            try:
                # Load tokenizer and model for local Hugging Face inference
                self.tokenizer = AutoTokenizer.from_pretrained(model_identifier)
                self.model = AutoModelForCausalLM.from_pretrained(model_identifier)
                self.model.to(self.device) # Move model to the selected device
                self.model.eval() # Set model to evaluation mode


                # Set pad_token_id for generation if not already set (common for GPT-like models)
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                if self.model.config.pad_token_id is None:
                    self.model.config.pad_token_id = self.model.config.eos_token_id


                logger.info(f"Layer4LLMClient: Successfully loaded local transformers model '{model_identifier}'.")
                set_seed(42) # For reproducibility, though temperature will still add randomness


            except Exception as e:
                logger.error(f"Layer4LLMClient: Failed to load local transformers model '{model_identifier}': {e}")
                self.model = None
                self.tokenizer = None
                raise RuntimeError(f"Failed to load LLM model '{model_identifier}': {e}")
        elif self.backend == "ollama_api":
            if not self.api_url:
                self.api_url = "http://localhost:11434/api/generate" # Default Ollama API URL
                logger.warning(f"Ollama API URL not provided, defaulting to {self.api_url}")
            logger.info(f"Layer4LLMClient: Configured for Ollama API model '{model_identifier}' at {self.api_url}")
        elif self.backend == "custom_api":
            if not self.api_url:
                raise ValueError("API URL must be provided for 'custom_api' backend.")
            logger.info(f"Layer4LLMClient: Configured for custom API model '{model_identifier}' at {self.api_url}")
        else:
            raise ValueError(f"Unsupported backend type: {backend}")


    def query(self, prompt: str) -> str:
        """
        Sends a prompt to the configured OSS LLM and returns its response.


        Args:
            prompt (str): The input prompt for the LLM.


        Returns:
            str: The generated response from the OSS LLM, or an error message.
        """
        logger.info(f"Layer4LLMClient: Querying '{self.model_identifier}' with prompt: {prompt[:100]}...")


        if self.backend == "transformers_local":
            if self.model is None or self.tokenizer is None:
                return "ERROR: Local transformers model not loaded. Please check initialization logs."
            try:
                input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
                with torch.no_grad():
                    output = self.model.generate(
                        input_ids,
                        max_new_tokens=self.max_new_tokens,
                        temperature=self.temperature,
                        do_sample=True if self.temperature > 0 else False,
                        pad_token_id=self.tokenizer.pad_token_id,
                        eos_token_id=self.tokenizer.eos_token_id
                    )
                response_text = self.tokenizer.decode(output[0][input_ids.shape[1]:], skip_special_tokens=True)
                logger.info(f"Layer4LLMClient: Response from local transformers model '{self.model_identifier}' generated.")
                return response_text
            except Exception as e:
                logger.error(f"Layer4LLMClient: Error during local transformers inference with '{self.model_identifier}': {e}")
                return f"ERROR: Local inference failed with LLM: {e}"


        elif self.backend == "ollama_api":
            payload = {
                "model": self.model_identifier,
                "prompt": prompt,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_new_tokens,
                }
            }
            try:
                response = requests.post(self.api_url, headers=self.headers, data=json.dumps(payload))
                response.raise_for_status()
                # Ollama streams responses, so we need to concatenate
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            json_response = json.loads(line.decode('utf-8'))
                            full_response += json_response.get('response', '')
                            if json_response.get('done'):
                                break
                        except json.JSONDecodeError:
                            logger.warning(f"Layer4LLMClient: Could not decode JSON line from Ollama: {line}")
                logger.info(f"Layer4LLMClient: Response from Ollama API model '{self.model_identifier}' generated.")
                return full_response.strip()
            except requests.exceptions.RequestException as e:
                logger.error(f"Layer4LLMClient: Error querying Ollama API at {self.api_url}: {e}")
                return f"ERROR: Failed to query Ollama API: {e}"
            except Exception as e:
                logger.error(f"Layer4LLMClient: An unexpected error occurred with Ollama API: {e}")
                return f"ERROR: An unexpected error occurred with Ollama API: {e}"


        elif self.backend == "custom_api":
            payload = {
                "prompt": prompt,
                "temperature": self.temperature,
                "max_new_tokens": self.max_new_tokens,
                # Add other model-specific parameters as needed for your custom API
            }
            try:
                response = requests.post(self.api_url, headers=self.headers, data=json.dumps(payload))
                response.raise_for_status()
                result = response.json()
                # Assuming the response structure has a 'generated_text' or similar key
                return result.get('generated_text', json.dumps(result))
            except requests.exceptions.RequestException as e:
                logger.error(f"Layer4LLMClient: Error querying custom API at {self.api_url}: {e}")
                return f"ERROR: Failed to query custom API: {e}"
            except json.JSONDecodeError as e:
                logger.error(f"Layer4LLMClient: Failed to decode JSON from custom API: {e}")
                return f"ERROR: Invalid JSON response from custom API: {e}"
            except Exception as e:
                logger.error(f"Layer4LLMClient: An unexpected error occurred with custom API: {e}")
                return f"ERROR: An unexpected error occurred with custom API: {e}"
        else:
            return "ERROR: Unsupported backend type configured for Layer4LLMClient."