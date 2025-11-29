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
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
    
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
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
    
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
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
    
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
        
        # Convert tools to Gemini format
        gemini_tools = None
        if tools:
            gemini_tools = [
                {
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "parameters": tool["function"]["parameters"]
                }
                for tool in tools
            ]
        
        # Build model
        model = genai.GenerativeModel(
            model_name=self.model,
            tools=gemini_tools
        )
        
        # Convert messages to Gemini format
        history = []
        for msg in messages[:-1]:
            history.append({
                "role": "user" if msg["role"] in ["user", "system"] else "model",
                "parts": [msg["content"]]
            })
        
        # Get last message as prompt
        prompt = messages[-1]["content"] if messages else ""
        
        try:
            # Start chat
            chat = model.start_chat(history=history)
            
            # Stream response
            response = await chat.send_message_async(prompt, stream=True)
            
            async for chunk in response:
                if chunk.text:
                    yield {"type": "delta", "content": chunk.text}
                
                # Handle function calls
                if chunk.parts:
                    for part in chunk.parts:
                        if hasattr(part, "function_call"):
                            yield {
                                "type": "tool_call",
                                "tool_name": part.function_call.name,
                                "tool_input": dict(part.function_call.args)
                            }
            
            yield {"type": "done", "finish_reason": "stop"}
        
        except Exception as e:
            logger.error(f"Google Gemini streaming error: {e}")
            yield {"type": "error", "error": str(e)}


class XAIProvider(LLMProvider):
    """xAI provider (Grok, etc.)."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "grok-beta"):
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("XAI_API_KEY not found in environment")
    
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

