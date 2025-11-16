"""Reuters collector agent."""

from google.adk.agents import Agent
from .tools import fetch_reuters_rss


# Reuters collector agent
reuters_agent = Agent(
    name="reuters_collector",
    model="gemini-2.0-flash-lite",
    description="Collects recent news articles from Reuters RSS feeds (center-left perspective)",
    instruction="""
    You are a news collection agent specialized in gathering articles from Reuters.

    Your task:
    1. Fetch articles from BOTH politics AND tech categories
    2. Collect exactly 5 articles total (split between categories as available)
    3. Focus on articles published in the last 24 hours
    4. Return structured article data

    Use the fetch_reuters_rss tool twice:
    - Once for category='politics' with max_articles=3
    - Once for category='tech' with max_articles=2

    After collecting, confirm the total count and provide a brief summary of what was collected.
    """,
    tools=[fetch_reuters_rss]
)
