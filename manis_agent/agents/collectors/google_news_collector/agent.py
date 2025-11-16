"""Google News collector agent."""

from google.adk.agents import Agent
from .tools import fetch_google_news_rss


# Google News collector agent
google_news_agent = Agent(
    name="google_news_collector",
    model="gemini-2.0-flash-lite",
    description="Collects recent news articles from Google News RSS feeds (aggregated from multiple sources)",
    instruction="""
    You are a news collection agent. Your ONLY job is to fetch Google News articles.

    IMMEDIATELY do the following (do NOT just plan - EXECUTE):

    Step 1: Call fetch_google_news_rss with topic='politics' and max_articles=4
    Step 2: Call fetch_google_news_rss with topic='technology' and max_articles=3
    Step 3: Call fetch_google_news_rss with topic='europe' and max_articles=4
    Step 4: Report the results

    You MUST call the tool THREE times (politics, technology, europe). Do not skip any step.

    CRITICAL: When reporting results, use the 'count' field from each tool response.
    The 'articles' array will be empty to avoid duplication, but 'count' shows the actual number collected.

    After calling ALL THREE tools, report:
    - Total articles collected: SUM of all 'count' fields (e.g., politics count + tech count + europe count)
    - Individual counts per topic (e.g., "Politics: 4 articles, Tech: 3 articles, Europe: 4 articles")
    - Debug info if any count is 0 (RSS entries found, how many too old, parse failures)
    - Brief summary confirming articles were stored in state

    Example: If politics returns count=4, tech returns count=3, europe returns count=4,
    report "Total: 11 articles collected successfully (4 politics + 3 tech + 4 europe)"
    """,
    tools=[fetch_google_news_rss]
)
