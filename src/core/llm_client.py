import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import base64
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class GemmaClient:
    """
    Unified client for Gemma (Text + Vision) via Ollama.
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_URL
        self.model = settings.LLM_MODEL
        self.timeout = settings.LLM_TIMEOUT
        
    async def generate(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Generates completion from Ollama.
        
        Args:
            prompt: User prompt
            images: List of base64 encoded strings or file paths
            system_prompt: System instruction override
            temperature: Creativity (0.0 to 1.0)
            json_mode: Force JSON output structure
        """
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        user_msg = {"role": "user", "content": prompt}
        
        # Handle images
        if images:
            processed_images = []
            for img in images:
                # If path, load and encode
                if not img.startswith("data:"): 
                    try:
                        with open(img, "rb") as f:
                            encoded = base64.b64encode(f.read()).decode("utf-8")
                            processed_images.append(encoded)
                    except Exception:
                        # Assume already base64 or invalid, pass as is for API to handle error
                        processed_images.append(img)
                else:
                    processed_images.append(img)
            
            user_msg["images"] = processed_images
            
        messages.append(user_msg)
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "content": data["message"]["content"],
                    "model": data["model"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "done": data["done"]
                }
            except httpx.ConnectError:
                logger.error(f"Could not connect to Ollama at {self.base_url}")
                raise ConnectionError("Ollama service unreachable. Ensure it is running.")
            except Exception as e:
                logger.error(f"LLM generation failed: {str(e)}")
                raise

llm_client = GemmaClient()
