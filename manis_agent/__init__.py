"""
MANIS (Multi-Agent News Intelligence System)

Automated multi-agent pipeline for collecting, analyzing, and delivering news intelligence.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in the package directory
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Register LiteLLM for OpenRouter support (must be imported before agents)
from . import llm_config

from . import agent
