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

    Your task:
    1. Process all collected articles from the previous stage
    2. Clean and normalize the text
    3. Extract entities (people, organizations, locations)
    4. Identify key claims and assertions in each article
    5. Store processed articles in state for next stage

    Use the preprocess_articles tool to process all articles at once.

    After preprocessing, provide:
    - Total number of articles processed
    - Total entities and claims extracted
    - Sample of entities found
    - Confirmation that preprocessed articles are ready for fact-checking

    Be concise in your response.
    """,
    tools=[preprocess_articles]
)
