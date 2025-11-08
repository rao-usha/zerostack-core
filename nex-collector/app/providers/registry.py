"""Provider registry."""
from typing import Dict, Optional
from .base import Provider
from .openai_provider import OpenAIProvider
from ..config import settings


class ProviderRegistry:
    """Registry for LLM providers."""
    
    def __init__(self):
        """Initialize registry."""
        self._providers: Dict[str, Provider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available providers."""
        if "openai" in settings.providers_list:
            if settings.OPENAI_API_KEY:
                self._providers["openai"] = OpenAIProvider(settings.OPENAI_API_KEY)
            else:
                print("Warning: OPENAI_API_KEY not set, OpenAI provider disabled")
        
        # Future: Add Anthropic, Google providers here
        # if "anthropic" in settings.providers_list:
        #     ...
    
    def get_provider(self, name: str) -> Optional[Provider]:
        """Get a provider by name."""
        return self._providers.get(name)
    
    def list_providers(self) -> list[str]:
        """List available provider names."""
        return list(self._providers.keys())


# Global registry instance
registry = ProviderRegistry()

