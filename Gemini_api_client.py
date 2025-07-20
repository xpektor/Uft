# gemini_api_client.py
import logging
import os
import asyncio
import json
import time # ADDED: For latency calculation
from typing import Dict, List, Any, Optional


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GeminiApiClient:
    """
    Client for interacting with the Google Gemini API.
    Serves as Baldur's primary "window" to advanced external LLM capabilities.
    """
    def __init__(self, api_cost_per_token: float = 0.000002): # Example cost for gemini-2.0-flash
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY environment variable not set. Gemini API client will not function.")
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        
        # Externalize headers/model ID in init or config
        self.api_base_url = "https://generativelanguage.googleapis.com/v1beta/models/"
        self.default_model_id = "gemini-2.0-flash"
        self.headers = {'Content-Type': 'application/json'} # Externalized headers
        self.api_cost_per_token = api_cost_per_token # Store cost per token


        logger.info("GeminiApiClient initialized.")


    async def generate_content(self,
                               prompt: str,
                               chat_history: Optional[List[Dict[str, Any]]] = None,
                               generation_config: Optional[Dict[str, Any]] = None,
                               model_id: str = None # Allow overriding default model
                              ) -> Optional[Dict[str, Any]]: # Return response metadata including token usage and cost
        """
        Generates content using the Gemini API.
        Returns response metadata including token usage and cost estimates.
        """
        if chat_history is None:
            chat_history = []
        
        if model_id is None:
            model_id = self.default_model_id


        chat_history.append({"role": "user", "parts": [{"text": prompt}]})


        payload = {"contents": chat_history}
        if generation_config:
            payload["generationConfig"] = generation_config


        full_api_url = f"{self.api_base_url}{model_id}:generateContent?key={self.api_key}"


        start_time = time.time()
        try:
            # --- Placeholder for async fetch logic (replace with actual async HTTP client) ---
            # In a real Baldur implementation, this would be handled by a robust async HTTP client
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(full_api_url, headers=self.headers, json=payload, timeout=60)
            #     response.raise_for_status() # Raise HTTPStatusError for bad responses
            #     result = response.json()


            logger.warning("GeminiApiClient: Using placeholder for async fetch. Replace with httpx in production.")
            await asyncio.sleep(0.1) # Simulate network delay
            # Mock response for testing
            mock_response_text = "This is a mock response from Gemini API."
            result = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": mock_response_text}
                            ]
                        }
                    }
                ],
                "usageMetadata": { # Conceptual usage metadata
                    "promptTokenCount": len(prompt.split()),
                    "candidatesTokenCount": len(mock_response_text.split()),
                    "totalTokenCount": len(prompt.split()) + len(mock_response_text.split())
                }
            }
            # --- End Placeholder ---


            latency = time.time() - start_time


            if result and result.get("candidates") and result["candidates"][0].get("content") and \
               result["candidates"][0]["content"].get("parts") and result["candidates"][0]["content"]["parts"][0].get("text"):
                text_response = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Return token usage and cost estimates
                usage_metadata = result.get("usageMetadata", {})
                prompt_tokens = usage_metadata.get("promptTokenCount", 0)
                completion_tokens = usage_metadata.get("candidatesTokenCount", 0)
                total_tokens = usage_metadata.get("totalTokenCount", prompt_tokens + completion_tokens)
                
                estimated_cost = total_tokens * self.api_cost_per_token


                response_metadata = {
                    "text": text_response,
                    "latency_seconds": float(latency),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost": float(estimated_cost),
                    "model_id": model_id,
                    "success": True
                }
                logger.info(f"GeminiApiClient: Successfully generated content from Gemini. Tokens: {total_tokens}, Cost: ${estimated_cost:.6f}.")
                return response_metadata
            else:
                logger.warning(f"GeminiApiClient: Unexpected response structure from Gemini API: {result}")
                return {"success": False, "reason": "Unexpected response structure", "raw_result": result}
        except Exception as e:
            # Mask API key in traceback logs (conceptual)
            error_message = str(e).replace(self.api_key, "[API_KEY_MASKED]") if self.api_key else str(e)
            logger.error(f"GeminiApiClient: Error calling Gemini API: {error_message}", exc_info=True) # exc_info=True to log full traceback
            return {"success": False, "reason": f"API call failed: {error_message}"}


    async def generate_structured_content(self,
                                         prompt: str,
                                         response_schema: Dict[str, Any],
                                         chat_history: Optional[List[Dict[str, Any]]] = None,
                                         model_id: str = None
                                        ) -> Optional[Dict[str, Any]]:
        """
        Generates structured content (JSON) using the Gemini API with a response schema.
        """
        generation_config = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
        response_data = await self.generate_content(prompt, chat_history, generation_config, model_id)
        if response_data and response_data["success"]:
            json_string_response = response_data["text"]
            try:
                parsed_json = json.loads(json_string_response)
                logger.info("GeminiApiClient: Successfully parsed structured content.")
                response_data["parsed_json"] = parsed_json
                return response_data
            except json.JSONDecodeError as e:
                logger.error(f"GeminiApiClient: Failed to parse JSON response: {e}. Raw response: {json_string_response}")
                response_data["success"] = False
                response_data["reason"] = f"JSON parsing failed: {e}"
                return response_data
        return response_data # Return original response_data which might indicate failure


    async def generate_image_description(self,
                                        prompt: str,
                                        base64_image_data: str,
                                        mime_type: str = "image/png",
                                        model_id: str = None
                                       ) -> Optional[Dict[str, Any]]:
        """
        Generates a description for an image using the Gemini API.
        """
        if model_id is None:
            model_id = self.default_model_id


        contents = [
            {"role": "user", "parts": [{"text": prompt}]},
            {"role": "user", "parts": [{"inlineData": {"mimeType": mime_type, "data": base64_image_data}}]}
        ]
        payload = {"contents": contents}
        full_api_url = f"{self.api_base_url}{model_id}:generateContent?key={self.api_key}"


        start_time = time.time()
        try:
            # --- Placeholder for async fetch logic (replace with actual async HTTP client) ---
            logger.warning("GeminiApiClient: Using placeholder for async fetch for image. Replace with httpx in production.")
            await asyncio.sleep(0.1) # Simulate network delay
            mock_image_description = "This is a mock description of the image from Gemini API."
            result = {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": mock_image_description}
                            ]
                        }
                    }
                ],
                "usageMetadata": { # Conceptual usage metadata
                    "promptTokenCount": len(prompt.split()),
                    "candidatesTokenCount": len(mock_image_description.split()),
                    "totalTokenCount": len(prompt.split()) + len(mock_image_description.split())
                }
            }
            # --- End Placeholder ---


            latency = time.time() - start_time


            if result and result.get("candidates") and result["candidates"][0].get("content") and \
               result["candidates"][0]["content"].get("parts") and result["candidates"][0]["content"]["parts"][0].get("text"):
                text_response = result["candidates"][0]["content"]["parts"][0]["text"]
                
                usage_metadata = result.get("usageMetadata", {})
                prompt_tokens = usage_metadata.get("promptTokenCount", 0)
                completion_tokens = usage_metadata.get("candidatesTokenCount", 0)
                total_tokens = usage_metadata.get("totalTokenCount", prompt_tokens + completion_tokens)
                
                estimated_cost = total_tokens * self.api_cost_per_token


                response_metadata = {
                    "text": text_response,
                    "latency_seconds": float(latency),
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost": float(estimated_cost),
                    "model_id": model_id,
                    "success": True
                }
                logger.info(f"GeminiApiClient: Successfully generated image description. Tokens: {total_tokens}, Cost: ${estimated_cost:.6f}.")
                return response_metadata
            else:
                logger.warning(f"GeminiApiClient: Unexpected response structure for image description: {result}")
                return {"success": False, "reason": "Unexpected response structure", "raw_result": result}
        except Exception as e:
            error_message = str(e).replace(self.api_key, "[API_KEY_MASKED]") if self.api_key else str(e)
            logger.error(f"GeminiApiClient: Error calling Gemini API for image description: {error_message}", exc_info=True)
            return {"success": False, "reason": f"API call failed: {error_message}"}