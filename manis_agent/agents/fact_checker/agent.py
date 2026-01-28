"""Fact-checking agent with source credibility scoring."""

from google.adk.agents import Agent
from .tools import score_article_credibility, flag_dubious_claims


# Fact checker agent
fact_checker_agent = Agent(
    name="fact_checker",
    model="openrouter/google/gemini-2.5-flash-lite-preview-09-2025",
    description="Evaluates article credibility and flags claims needing verification",
    instruction="""
    You are a fact-checking agent that evaluates news article credibility.

    IMMEDIATELY do the following (do NOT just plan - EXECUTE):

    Step 1: Call score_article_credibility tool to score all articles
    Step 2: Call flag_dubious_claims tool to identify claims needing verification
    Step 3: Report the results

    You MUST call BOTH tools in order. Do not skip any step.

    After calling BOTH tools, report:
    - Credibility distribution (high/medium/low credibility article counts from tool response)
    - Average credibility and bias scores (from tool response)
    - Number of flagged claims and examples (from tool response)
    - Brief assessment of overall reliability

    CRITICAL: Use the actual data returned by the tools. Do not make up or infer values.

    Be concise and factual.
    """,
    tools=[score_article_credibility, flag_dubious_claims]
)
