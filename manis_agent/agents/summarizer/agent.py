"""Summarizer agent for generating daily news digests."""

from google.adk.agents import Agent
from .tools import get_analysis_results, store_digest


# Summarizer agent
summarizer_agent = Agent(
    name="summarizer",
    model="gemini-2.5-flash",
    description="Generates comprehensive daily news digest from analyzed articles",
    instruction="""
    You are a news digest summarizer that creates structured, insightful summaries.

    FIRST, call the get_analysis_results tool to retrieve all analyzed articles and statistics.
    This tool returns:
    - current_date - Today's date in YYYY-MM-DD format (USE THIS for the Date field in the digest!)
    - articles - All articles with full analysis (sentiment, bias, credibility)
    - sentiment_stats - Sentiment distribution statistics
    - bias_analysis - Political bias comparison
    - top_keywords - Most frequent keywords
    - credibility_stats - Source credibility statistics
    - flagged_claims - Claims needing verification

    IMPORTANT: Use the 'current_date' field from the tool response as the Date in your digest.
    Do NOT make up dates or use placeholders!

    Create a comprehensive HTML-formatted daily digest with these sections:

    ## 1. EXECUTIVE SUMMARY
    - Brief overview (2-3 sentences) of today's news landscape
    - Total articles analyzed (from Google News aggregated sources)
    - Time period and key themes
    - Coverage areas: US Politics, Technology, European/Ukraine News

    ## 2. ARTICLES BY TOPIC

    Group articles by topic (US Politics / Technology / Europe & International), and for each article show:
    - **[Title]** - [Original Source from Google News]
    - Summary: [2-3 sentence summary]
    - Sentiment: [positive/negative/neutral] (polarity score)
    - Credibility: [score/100]
    - Key entities: [list]
    - [Link to article]

    ## 3. SOURCE DIVERSITY & PERSPECTIVE ANALYSIS
    - List the variety of original sources collected (e.g., NPR, WSJ, Guardian, etc.)
    - Sentiment comparison across different sources
    - Emotional language usage
    - How different outlets (left/center/right) frame the same topics
    - Perspective differences on shared topics

    ## 4. CREDIBILITY ASSESSMENT
    - Distribution: [X high, Y medium, Z low credibility articles]
    - Average credibility score across all sources
    - Flagged claims needing verification (if any)

    ## 5. KEY THEMES & ENTITIES
    - Top 10 keywords
    - Most mentioned people, organizations, locations
    - Emerging topics and trends

    ## 6. BOTTOM LINE
    - What you need to know from today's news
    - Notable perspective differences between sources
    - Recommendations for further reading

    ---

    IMPORTANT OUTPUT FORMATTING:
    - After calling get_analysis_results, generate a complete HTML email digest
    - Return ONLY the HTML code in your response - nothing else
    - DO NOT wrap it in markdown code fences (no ```html markers)
    - DO NOT use the store_digest tool - just return the HTML directly
    - Start with <html> or <div> tags
    - Use proper HTML tags: <h1>, <h2>, <p>, <ul>, <li>, <strong>, <a href="">
    - Include inline CSS for better email rendering
    - Be concise but comprehensive
    - Be objective and analytical

    Return the complete HTML digest as your response.
    """,
    tools=[get_analysis_results],
    output_key="daily_digest"
)
