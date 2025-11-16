"""Parallel news collectors for Fox News and Reuters."""

from google.adk.agents import ParallelAgent
from .fox_collector.agent import fox_news_agent
from .reuters_collector.agent import reuters_agent


# Parallel collector agent that runs Fox News and Reuters collectors concurrently
# NOTE: This is commented out to prevent a Pydantic validation error.
# The root agent now uses the collector agents sequentially.
# parallel_collectors = ParallelAgent(
#     name="news_collectors",
#     description="Collects news articles from Fox News and Reuters in parallel",
#     sub_agents=[fox_news_agent, reuters_agent]
# )