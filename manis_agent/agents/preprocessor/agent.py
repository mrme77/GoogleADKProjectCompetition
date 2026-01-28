"""Preprocessor agent for cleaning and extracting data from articles."""

from google.adk.agents import Agent
from .tools import preprocess_articles


# Preprocessor agent
preprocessor_agent = Agent(
    name="preprocessor",
    model="openrouter/google/gemini-2.5-flash-lite-preview-09-2025",
    description="Preprocesses collected articles by cleaning text and extracting entities and claims",
    instruction="""
    You are a text preprocessing agent that prepares news articles for analysis.

    IMMEDIATELY do the following (do NOT just plan - EXECUTE):

    Step 1: Call preprocess_articles tool to process all collected articles
    Step 2: Report the results

    You MUST call the preprocess_articles tool. Do not skip this step.

    After calling the tool, report:
    - Total number of articles processed (from tool response)
    - Total entities extracted and breakdown by category: persons, organizations, locations (from tool response)
    - Sample entities found - show a few examples from each category (from tool response)
    - Total claims extracted (from tool response)
    - Whether spaCy NER was used (check the 'using_spacy' field in tool response)
    - Confirmation that preprocessed articles are ready for fact-checking

    CRITICAL: Use the actual data returned by the tool. Do not make up or infer values.

    Be concise in your response.
    """,
    tools=[preprocess_articles]
)
