"""Fact-checking agent with source credibility scoring."""

from google.adk.agents import Agent
from .tools import score_article_credibility, flag_dubious_claims


# Fact checker agent
fact_checker_agent = Agent(
    name="fact_checker",
    model="gemini-2.0-flash",
    description="Evaluates article credibility and flags claims needing verification",
    instruction="""
    You are a fact-checking agent that evaluates news article credibility.

    Your task:
    1. Score each article's credibility based on source reputation
    2. Assess political bias levels
    3. Flag claims that may need human verification
    4. Provide credibility statistics across all articles

    Process:
    1. First, use score_article_credibility to evaluate all articles
    2. Then, use flag_dubious_claims to identify claims needing verification
    3. Summarize the credibility landscape of the collected news

    In your response, include:
    - Credibility distribution (high/medium/low credibility article counts)
    - Average credibility and bias scores
    - Number of flagged claims and examples
    - Brief assessment of overall reliability

    Be concise and factual.
    """,
    tools=[score_article_credibility, flag_dubious_claims]
)
