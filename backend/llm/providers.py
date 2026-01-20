"""
LLM Provider abstraction layer.

Supports multiple LLM providers with a unified interface:
- OpenAI (GPT-4, GPT-4 Turbo, etc.)
- Anthropic (Claude 3.5 Sonnet, Claude 3 Opus, etc.)
- Google (Gemini Pro, Gemini Ultra, etc.)
- xAI (Grok, etc.)

All providers support:
- Streaming responses
- Tool/function calling
- Async operations
"""

import os
import json
import logging
from typing import AsyncIterator, Dict, Any, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


def get_api_key(key_name: str, fallback_names: List[str] = None) -> Optional[str]:
    """
    Get API key from ConfigProvider (DB -> env -> settings fallback).

    Args:
        key_name: Primary key name (e.g., "OPENAI_API_KEY")
        fallback_names: Alternative key names to try

    Returns:
        API key value or None
    """
    try:
        from domains.settings.config_provider import config

        # Try primary key
        value = config.get(key_name, category="llm")
        if value:
            return value

        # Try fallback keys
        if fallback_names:
            for name in fallback_names:
                value = config.get(name, category="llm")
                if value:
                    return value

        return None
    except Exception as e:
        # Fallback to direct os.getenv if config provider fails
        logger.debug(f"ConfigProvider failed for {key_name}: {e}, falling back to os.getenv")
        value = os.getenv(key_name)
        if value:
            return value
        if fallback_names:
            for name in fallback_names:
                value = os.getenv(name)
                if value:
                    return value
        return None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream chat completion with optional tool calling.
        
        Yields events:
        - {"type": "delta", "content": str} - Text delta
        - {"type": "tool_call", "tool_name": str, "tool_input": dict} - Tool call request
        - {"type": "done", "finish_reason": str} - Completion finished
        - {"type": "error", "error": str} - Error occurred
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider (GPT-4, GPT-4 Turbo, etc.)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo-preview"):
        self.api_key = api_key or get_api_key("OPENAI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured. Set it via Settings UI or .env file.")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream chat using OpenAI API."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
        
        client = AsyncOpenAI(api_key=self.api_key)
        
        # Build request parameters
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
        
        if tools:
            params["tools"] = tools
            if tool_choice:
                params["tool_choice"] = tool_choice
        
        try:
            stream = await client.chat.completions.create(**params)
            
            # Track tool calls as they stream in
            current_tool_calls = {}
            
            async for chunk in stream:
                delta = chunk.choices[0].delta
                
                # Handle content delta
                if delta.content:
                    yield {"type": "delta", "content": delta.content}
                
                # Handle tool calls (they stream in chunks)
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        idx = tool_call_delta.index
                        
                        if idx not in current_tool_calls:
                            current_tool_calls[idx] = {
                                "id": tool_call_delta.id or "",
                                "name": "",
                                "arguments": ""
                            }
                        
                        if tool_call_delta.id:
                            current_tool_calls[idx]["id"] = tool_call_delta.id
                        
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                current_tool_calls[idx]["name"] = tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                current_tool_calls[idx]["arguments"] += tool_call_delta.function.arguments
                
                # Handle finish - emit complete tool calls
                if chunk.choices[0].finish_reason:
                    # Emit any accumulated tool calls
                    for tool_call in current_tool_calls.values():
                        if tool_call["name"] and tool_call["arguments"]:
                            try:
                                yield {
                                    "type": "tool_call",
                                    "tool_call_id": tool_call["id"],
                                    "tool_name": tool_call["name"],
                                    "tool_input": json.loads(tool_call["arguments"])
                                }
                            except json.JSONDecodeError:
                                logger.error(f"Failed to parse tool arguments: {tool_call['arguments']}")
                    
                    yield {
                        "type": "done",
                        "finish_reason": chunk.choices[0].finish_reason
                    }
        
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield {"type": "error", "error": str(e)}


class AnthropicProvider(LLMProvider):
    """Anthropic provider (Claude 3.5 Sonnet, Claude 3 Opus, etc.)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or get_api_key("ANTHROPIC_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured. Set it via Settings UI or .env file.")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream chat using Anthropic API."""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError("anthropic package required. Install with: pip install anthropic")
        
        client = AsyncAnthropic(api_key=self.api_key)
        
        # Convert messages to Anthropic format
        system_messages = [m["content"] for m in messages if m["role"] == "system"]
        non_system_messages = [m for m in messages if m["role"] != "system"]
        
        # Build request parameters
        params = {
            "model": self.model,
            "messages": non_system_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "stream": True
        }
        
        if system_messages:
            params["system"] = "\n\n".join(system_messages)
        
        if tools:
            # Convert to Anthropic tool format
            params["tools"] = [
                {
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": tool["function"]["parameters"]
                }
                for tool in tools
            ]
        
        try:
            async with client.messages.stream(**params) as stream:
                async for event in stream:
                    # Handle text delta
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield {"type": "delta", "content": event.delta.text}
                    
                    # Handle tool use
                    elif event.type == "content_block_start":
                        if hasattr(event.content_block, "type") and event.content_block.type == "tool_use":
                            yield {
                                "type": "tool_call",
                                "tool_call_id": event.content_block.id,
                                "tool_name": event.content_block.name,
                                "tool_input": event.content_block.input
                            }
                    
                    # Handle completion
                    elif event.type == "message_stop":
                        yield {"type": "done", "finish_reason": "stop"}
        
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield {"type": "error", "error": str(e)}


class GoogleProvider(LLMProvider):
    """Google provider (Gemini Pro, Gemini Ultra, etc.)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro"):
        self.api_key = api_key or get_api_key("GOOGLE_API_KEY", ["GEMINI_API_KEY"])
        self.model = model

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not configured. Set it via Settings UI or .env file.")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream chat using Google Gemini API."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai package required. Install with: pip install google-generativeai")
        
        genai.configure(api_key=self.api_key)
        
        # Build model (without tools for simpler streaming)
        model = genai.GenerativeModel(model_name=self.model)
        
        # Convert messages to Gemini format - combine into single prompt for simplicity
        prompt_parts = []
        system_prompt = None
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Build final prompt
        full_prompt = ""
        if system_prompt:
            full_prompt = f"System instructions: {system_prompt}\n\n"
        full_prompt += "\n".join(prompt_parts)
        if prompt_parts:
            full_prompt += "\n\nAssistant:"
        
        try:
            import asyncio
            
            # Use synchronous generate_content with stream=True
            # Run in executor to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens or 4096,
                    ),
                    stream=True
                )
            )
            
            # Process chunks - yield each one with a small delay to allow event loop to flush
            if response is not None:
                for chunk in response:
                    try:
                        if chunk.text:
                            yield {"type": "delta", "content": chunk.text}
                            await asyncio.sleep(0)  # Allow event loop to process
                    except Exception as chunk_err:
                        logger.debug(f"Chunk processing: {chunk_err}")
                        continue
            
            yield {"type": "done", "finish_reason": "stop"}
        
        except Exception as e:
            logger.error(f"Google Gemini streaming error: {e}")
            yield {"type": "error", "error": str(e)}


class XAIProvider(LLMProvider):
    """xAI provider (Grok, etc.)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "grok-beta"):
        self.api_key = api_key or get_api_key("XAI_API_KEY", ["X_AI_API_KEY"])
        self.model = model

        if not self.api_key:
            raise ValueError("XAI_API_KEY not configured. Set it via Settings UI or .env file.")
    
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream chat using xAI API (OpenAI-compatible)."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
        
        # xAI uses OpenAI-compatible API
        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1"
        )
        
        # Build request parameters
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        
        if max_tokens:
            params["max_tokens"] = max_tokens
        
        if tools:
            params["tools"] = tools
            if tool_choice:
                params["tool_choice"] = tool_choice
        
        try:
            stream = await client.chat.completions.create(**params)
            
            # Track tool calls as they stream in
            current_tool_calls = {}
            
            async for chunk in stream:
                delta = chunk.choices[0].delta
                
                # Handle content delta
                if delta.content:
                    yield {"type": "delta", "content": delta.content}
                
                # Handle tool calls (they stream in chunks)
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        idx = tool_call_delta.index
                        
                        if idx not in current_tool_calls:
                            current_tool_calls[idx] = {
                                "id": tool_call_delta.id or "",
                                "name": "",
                                "arguments": ""
                            }
                        
                        if tool_call_delta.id:
                            current_tool_calls[idx]["id"] = tool_call_delta.id
                        
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                current_tool_calls[idx]["name"] = tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                current_tool_calls[idx]["arguments"] += tool_call_delta.function.arguments
                
                # Handle finish - emit complete tool calls
                if chunk.choices[0].finish_reason:
                    # Emit any accumulated tool calls
                    for tool_call in current_tool_calls.values():
                        if tool_call["name"] and tool_call["arguments"]:
                            try:
                                yield {
                                    "type": "tool_call",
                                    "tool_call_id": tool_call["id"],
                                    "tool_name": tool_call["name"],
                                    "tool_input": json.loads(tool_call["arguments"])
                                }
                            except json.JSONDecodeError:
                                logger.error(f"Failed to parse tool arguments: {tool_call['arguments']}")
                    
                    yield {
                        "type": "done",
                        "finish_reason": chunk.choices[0].finish_reason
                    }
        
        except Exception as e:
            logger.error(f"xAI streaming error: {e}")
            yield {"type": "error", "error": str(e)}


# Provider registry
PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "xai": XAIProvider,
}


def get_provider(provider: str, model: str, **kwargs) -> LLMProvider:
    """
    Get LLM provider instance.
    
    Args:
        provider: Provider name (openai, anthropic, google, xai)
        model: Model name
        **kwargs: Additional provider-specific arguments
    
    Returns:
        LLMProvider instance
    
    Raises:
        ValueError: If provider is not supported
    """
    if provider not in PROVIDERS:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: {', '.join(PROVIDERS.keys())}"
        )
    
    provider_class = PROVIDERS[provider]
    return provider_class(model=model, **kwargs)

