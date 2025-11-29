"""Context generator for OTS LLM sampling."""
from typing import Dict, Any, Optional
from ..providers.registry import registry


class ContextGenerator:
    """Generate or mutate contexts using OTS LLMs."""
    
    def generate(
        self,
        prompt: str,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        seed: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate context text from prompt.
        
        Returns:
            Generated body_text
        """
        provider_obj = registry.get_provider(provider)
        if not provider_obj:
            raise ValueError(f"Provider {provider} not available")
        
        messages = [
            {"role": "system", "content": "You are a context document generator. Generate comprehensive, clear, and structured context documents."},
            {"role": "user", "content": prompt}
        ]
        
        params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2000,
            **kwargs
        }
        if seed:
            params["seed"] = seed
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def call_provider():
            return await provider_obj.chat(model, messages, params)
        
        result = loop.run_until_complete(call_provider())
        return result["text"]
    
    def mutate(
        self,
        existing_text: str,
        mutation_prompt: str = "Improve and expand this context while maintaining its core structure:",
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        **kwargs
    ) -> str:
        """Mutate existing context."""
        full_prompt = f"{mutation_prompt}\n\n{existing_text}"
        return self.generate(full_prompt, provider, model, **kwargs)

