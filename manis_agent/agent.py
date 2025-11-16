"""
MANIS (Multi-Agent News Intelligence System) - Root Agent

Orchestrates the full news collection, analysis, and delivery pipeline.
"""

from google.adk.agents import SequentialAgent
from .agents.collectors.google_news_collector.agent import google_news_agent
from .agents.preprocessor.agent import preprocessor_agent
from .agents.fact_checker.agent import fact_checker_agent
from .agents.nlp_analyst.agent import nlp_analyst_agent
from .agents.summarizer.agent import summarizer_agent
from .agents.delivery.agent import delivery_agent


# Root agent - orchestrates the entire MANIS pipeline
root_agent = SequentialAgent(
    name="manis_root",
    description="Multi-Agent News Intelligence System - Automated news collection, analysis, and delivery",
    sub_agents=[
        # Stage 1: Collect news from Google News (aggregates multiple sources)
        google_news_agent,
        preprocessor_agent,      # Stage 2: Clean text and extract entities
        fact_checker_agent,      # Stage 3: Score credibility and flag claims
        nlp_analyst_agent,       # Stage 4: Sentiment and bias analysis
        summarizer_agent,        # Stage 5: Generate daily digest
        delivery_agent           # Stage 6: Email delivery via Gmail
    ]
)