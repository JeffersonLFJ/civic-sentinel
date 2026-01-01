import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import base64
from src.config import settings
from src.core.settings_manager import settings_manager
import logging

logger = logging.getLogger(__name__)

class GemmaClient:
    """
    Unified client for Gemma (Text + Vision) via Ollama.
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_URL
        # Dynamic model binding
        self.timeout = settings.LLM_TIMEOUT
        
    @property
    def model(self):
        return settings_manager.llm_model
        

    # generate_stream handles streaming responses
    async def generate_stream(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        top_k: int = 40,
        num_ctx: int = 8192
    ):
        """
        Generates completion from Ollama as a stream of tokens.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        user_msg = {"role": "user", "content": prompt}
        
        if images:
            processed_images = []
            for img in images:
                if not img.startswith("data:"): 
                    try:
                        with open(img, "rb") as f:
                            encoded = base64.b64encode(f.read()).decode("utf-8")
                            processed_images.append(encoded)
                    except Exception:
                        processed_images.append(img)
                else:
                    processed_images.append(img)
            user_msg["images"] = processed_images
            
        messages.append(user_msg)
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_k": top_k,
                "num_ctx": num_ctx
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk = json.loads(line)
                        if "message" in chunk:
                            yield {
                                "content": chunk["message"]["content"],
                                "done": chunk.get("done", False)
                            }
            except httpx.ConnectError:
                logger.error(f"Could not connect to Ollama at {self.base_url}")
                raise ConnectionError("Ollama service unreachable. Ensure it is running.")
            except Exception as e:
                logger.error(f"LLM streaming failed: {str(e)}")
                raise

    async def generate(
        self,
        prompt: str,
        images: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        top_k: int = 40,
        num_ctx: int = 8192,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Generates completion from Ollama.
        """
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        user_msg = {"role": "user", "content": prompt}
        
        # Handle images
        if images:
            processed_images = []
            for img in images:
                if not img.startswith("data:"): 
                    try:
                        with open(img, "rb") as f:
                            encoded = base64.b64encode(f.read()).decode("utf-8")
                            processed_images.append(encoded)
                    except Exception:
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
                "top_k": top_k,
                "num_ctx": num_ctx
            }
        }
        
        if json_mode:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Debug logging for URL and Model validation
                logger.info(f"📤 Calling Ollama: {self.base_url}/api/chat | Model: {payload.get('model')}")
                # logger.debug(f"Payload: {json.dumps(payload)[:200]}...") # Partial log for safety

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
                logger.error(f"LLM generation failed: {repr(e)}")
                raise

llm_client = GemmaClient()
