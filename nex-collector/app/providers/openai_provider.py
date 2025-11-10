"""OpenAI provider implementation."""
import httpx
import os
from typing import Dict, Any, List
from .base import Provider


class OpenAIProvider:
    """OpenAI API provider."""
    
    name = "openai"
    
    def __init__(self, api_key: str):
        """Initialize OpenAI provider."""
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
    
    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call OpenAI Chat Completions API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": model,
            "messages": messages,
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 0.9),
            "max_tokens": params.get("max_tokens", 256),
            "n": params.get("n", 1),
        }
        
        # Add optional params
        if "seed" in params:
            body["seed"] = params["seed"]
        
        # Request logprobs if available (for some models)
        if params.get("logprobs", False):
            body["logprobs"] = True
            body["top_logprobs"] = params.get("top_logprobs", 5)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=body
            )
            resp.raise_for_status()
            data = resp.json()
        
        # Extract response
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message", {})
        text = message.get("content", "")
        
        # Extract usage
        usage = data.get("usage", {})
        
        # Extract logprobs if available
        logprobs = None
        if "logprobs" in choice and choice["logprobs"]:
            logprobs = {
                "tokens": choice["logprobs"].get("tokens", []),
                "token_logprobs": choice["logprobs"].get("token_logprobs", []),
                "top_logprobs": choice["logprobs"].get("top_logprobs", [])
            }
        
        return {
            "text": text,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            },
            "logprobs": logprobs
        }

