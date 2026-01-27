"""
LLM Configuration for MANIS
Registers LiteLLM to enable OpenRouter and other providers
"""

from google.adk.models.registry import LLMRegistry
from google.adk.models.lite_llm import LiteLlm

# Register LiteLLM to handle all non-Gemini models
# This enables OpenRouter, Anthropic, OpenAI, and other providers
LLMRegistry._register(r'.*', LiteLlm)

print("[LLM Config] LiteLLM registered for OpenRouter and other providers")
