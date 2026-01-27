"""
MANIS (Multi-Agent News Intelligence System)

Automated multi-agent pipeline for collecting, analyzing, and delivering news intelligence.
"""

# Register LiteLLM for OpenRouter support (must be imported before agents)
from . import llm_config

from . import agent
