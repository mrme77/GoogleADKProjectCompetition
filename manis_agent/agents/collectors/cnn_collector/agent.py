"""CNN collector agent."""

from google.adk.agents import Agent
from .tools import fetch_cnn_rss


# CNN collector agent
cnn_agent = Agent(
    name="cnn_collector",
    model="gemini-2.0-flash-lite",
    description="Collects recent news articles from CNN RSS feeds (center-left perspective)",
    instruction="""
    You are a news collection agent specialized in gathering articles from CNN.

    Your task:
    1. Fetch articles from BOTH politics AND tech categories
    2. Collect exactly 5 articles total (split between categories as available)
    3. Focus on articles published in the last 48 hours
    4. Return structured article data

    Use the fetch_cnn_rss tool twice:
    - Once for category='politics' with max_articles=3
    - Once for category='tech' with max_articles=2

    After collecting, ALWAYS report:
    - Total articles collected
    - Debug information from each tool call (total RSS entries, how many were too old, missing titles, parse failures)
    - Brief summary of what was collected

    If you get 0 articles from any category, REPORT the debug_info to help diagnose why!
    """,
    tools=[fetch_cnn_rss]
)
