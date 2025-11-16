"""Fox News collector agent."""

from google.adk.agents import Agent
from .tools import fetch_fox_news_rss


# Fox News collector agent
fox_news_agent = Agent(
    name="fox_news_collector",
    model="gemini-2.0-flash-lite",
    description="Collects recent news articles from Fox News RSS feeds (right-leaning perspective)",
    instruction="""
    You are a news collection agent. Your ONLY job is to fetch Fox News articles.

    IMMEDIATELY do the following (do NOT just plan - EXECUTE):

    Step 1: Call fetch_fox_news_rss with category='politics' and max_articles=3
    Step 2: Call fetch_fox_news_rss with category='tech' and max_articles=2
    Step 3: Report the results

    You MUST call the tool twice. Do not skip this step.

    After calling BOTH tools, report:
    - Total articles collected from both calls
    - Debug info (RSS entries found, how many too old, parse failures)
    - Brief summary

    If either call returns 0 articles, include the debug_info in your response.
    """,
    tools=[fetch_fox_news_rss]
)
