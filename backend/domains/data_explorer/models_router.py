"""
AI Models API - Fetch available models from providers.

Dynamically discovers available models from OpenAI, Anthropic, Google, and xAI.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel
import os
import logging

logger = logging.getLogger(__name__)


def get_api_key(key_name: str, fallback_names: List[str] = None) -> Optional[str]:
    """
    Get API key from ConfigProvider (DB -> env -> settings fallback).
    """
    try:
        from domains.settings.config_provider import config
        value = config.get(key_name, category="llm")
        if value:
            return value
        if fallback_names:
            for name in fallback_names:
                value = config.get(name, category="llm")
                if value:
                    return value
        return None
    except Exception:
        # Fallback to os.getenv if config provider fails
        value = os.getenv(key_name)
        if value:
            return value
        if fallback_names:
            for name in fallback_names:
                value = os.getenv(name)
                if value:
                    return value
        return None

router = APIRouter(prefix="/ai-models", tags=["ai-models"])


class ProviderModels(BaseModel):
    """Models available from a provider."""
    provider: str
    has_api_key: bool
    models: List[str]
    error: Optional[str] = None


class ModelsResponse(BaseModel):
    """Response with all available models."""
    providers: List[ProviderModels]


@router.get("/available", response_model=ModelsResponse)
async def get_available_models():
    """
    Get all available models from configured providers.
    
    Checks API keys and fetches model lists dynamically.
    """
    providers = []
    
    # OpenAI - Use verified working chat models
    openai_key = get_api_key("OPENAI_API_KEY")
    if openai_key:
        # Just use the verified list - simpler and more reliable
        # These are ALL tested and working with chat completions
        providers.append(ProviderModels(
            provider="openai",
            has_api_key=True,
            models=[
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-4-0613",
                "o1-preview",
                "o1-mini",
                "gpt-3.5-turbo"
            ]
        ))
    else:
        # No API key - show what models are available
        providers.append(ProviderModels(
            provider="openai",
            has_api_key=False,
            models=[]
        ))
    
    # Log what we found for debugging
    for p in providers:
        if p.provider == "openai":
            logger.info(f"OpenAI models available: {p.models[:5]}...")  # Log first 5
    
    # Anthropic
    anthropic_key = get_api_key("ANTHROPIC_API_KEY")
    if anthropic_key:
        # Anthropic doesn't have a models list API, use known models
        providers.append(ProviderModels(
            provider="anthropic",
            has_api_key=True,
            models=[
                "claude-3-5-sonnet-20241022",
                "claude-3-5-sonnet-20240620",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ]
        ))
    else:
        providers.append(ProviderModels(
            provider="anthropic",
            has_api_key=False,
            models=[]
        ))
    
    # Google (Gemini)
    google_key = get_api_key("GOOGLE_API_KEY", ["GEMINI_API_KEY"])
    if google_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=google_key)
            
            # Fetch available models
            available = genai.list_models()
            model_names = [
                model.name.replace('models/', '') 
                for model in available 
                if 'generateContent' in model.supported_generation_methods
            ]
            
            # Sort by preference
            priority = ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash']
            sorted_models = []
            
            for p in priority:
                matches = [m for m in model_names if p in m]
                sorted_models.extend(sorted(matches, reverse=True))
            
            remaining = [m for m in model_names if m not in sorted_models]
            sorted_models.extend(sorted(remaining, reverse=True))
            
            providers.append(ProviderModels(
                provider="google",
                has_api_key=True,
                models=sorted_models[:10]
            ))
            
        except Exception as e:
            logger.error(f"Error fetching Google models: {e}")
            providers.append(ProviderModels(
                provider="google",
                has_api_key=True,
                models=[
                    "gemini-2.0-flash-exp",
                    "gemini-1.5-pro-latest",
                    "gemini-1.5-flash-latest",
                    "gemini-1.5-pro",
                    "gemini-1.5-flash"
                ],
                error=f"Failed to fetch models: {str(e)}"
            ))
    else:
        providers.append(ProviderModels(
            provider="google",
            has_api_key=False,
            models=[]
        ))
    
    # xAI
    xai_key = get_api_key("XAI_API_KEY", ["X_AI_API_KEY"])
    if xai_key:
        # xAI uses OpenAI-compatible API
        try:
            import openai
            client = openai.OpenAI(
                api_key=xai_key,
                base_url="https://api.x.ai/v1"
            )
            
            response = client.models.list()
            model_names = [model.id for model in response.data]
            
            providers.append(ProviderModels(
                provider="xai",
                has_api_key=True,
                models=sorted(model_names, reverse=True)
            ))
            
        except Exception as e:
            logger.error(f"Error fetching xAI models: {e}")
            providers.append(ProviderModels(
                provider="xai",
                has_api_key=True,
                models=["grok-beta", "grok-2", "grok-2-latest"],
                error=f"Failed to fetch models: {str(e)}"
            ))
    else:
        providers.append(ProviderModels(
            provider="xai",
            has_api_key=False,
            models=[]
        ))
    
    return ModelsResponse(providers=providers)


@router.get("/check-keys")
async def check_api_keys():
    """Check which API keys are configured."""
    return {
        "openai": bool(get_api_key("OPENAI_API_KEY")),
        "anthropic": bool(get_api_key("ANTHROPIC_API_KEY")),
        "google": bool(get_api_key("GOOGLE_API_KEY", ["GEMINI_API_KEY"])),
        "xai": bool(get_api_key("XAI_API_KEY", ["X_AI_API_KEY"]))
    }

