"""Provider abstraction interface."""
from typing import Protocol, Dict, Any, List, Optional


class Provider(Protocol):
    """Provider interface for LLM APIs."""
    
    name: str
    
    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call the chat API.
        
        Returns:
            {
                "text": str,
                "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int},
                "logprobs": Optional[Dict[str, Any]]  # If available
            }
        """
        ...

