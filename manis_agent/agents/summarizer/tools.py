"""Tools for accessing analysis results for digest generation."""

from typing import Dict
from google.adk.tools.tool_context import ToolContext
from datetime import datetime


def get_analysis_results(tool_context: ToolContext) -> Dict:
    """
    Retrieve all analyzed articles and statistics from state for digest generation.

    Returns all the data needed to create a comprehensive daily news digest:
    - Fully analyzed articles with sentiment, bias, and credibility scores
    - Statistical summaries and comparisons
    - Keywords and themes

    Args:
        tool_context: ADK tool context with all analysis results in state

    Returns:
        Dictionary containing all analysis data for digest creation
    """
    # Get all analysis results from state
    bias_analyzed_articles = tool_context.state.get('bias_analyzed_articles', [])
    sentiment_stats = tool_context.state.get('sentiment_stats', {})
    bias_analysis = tool_context.state.get('bias_analysis', {})
    top_keywords = tool_context.state.get('top_keywords', [])
    credibility_stats = tool_context.state.get('credibility_stats', {})
    flagged_claims = tool_context.state.get('flagged_claims', [])

    # Also check earlier stages if final analysis is missing
    if not bias_analyzed_articles:
        bias_analyzed_articles = tool_context.state.get('nlp_analyzed_articles', [])
    if not bias_analyzed_articles:
        bias_analyzed_articles = tool_context.state.get('fact_checked_articles', [])
    if not bias_analyzed_articles:
        bias_analyzed_articles = tool_context.state.get('preprocessed_articles', [])
    if not bias_analyzed_articles:
        bias_analyzed_articles = tool_context.state.get('collected_articles', [])

    # Count articles by aggregator
    google_news_articles = [
        a for a in bias_analyzed_articles
        if isinstance(a, dict) and a.get('aggregator') == 'Google News'
    ]

    # Extract unique original sources for diversity analysis
    original_sources = set()
    for article in google_news_articles:
        if isinstance(article, dict):
            original_source = article.get('original_source', 'Unknown')
            if original_source and original_source != 'Unknown':
                original_sources.add(original_source)

    # Get current date for digest header
    current_date = datetime.now().strftime('%Y-%m-%d')

    return {
        'success': True,
        'current_date': current_date,
        'total_articles': len(bias_analyzed_articles),
        'google_news_count': len(google_news_articles),
        'original_sources': sorted(list(original_sources)),
        'source_diversity': len(original_sources),
        'articles': bias_analyzed_articles,
        'sentiment_stats': sentiment_stats,
        'bias_analysis': bias_analysis,
        'top_keywords': top_keywords,
        'credibility_stats': credibility_stats,
        'flagged_claims': flagged_claims
    }
