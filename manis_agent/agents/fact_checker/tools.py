"""Fact-checking and source credibility scoring tools."""

from typing import Dict, List
from google.adk.tools.tool_context import ToolContext


# Source credibility database (expanded for common sources)
SOURCE_CREDIBILITY = {
    # High Credibility (80+)
    'NPR': {'credibility_score': 85, 'political_bias': 'center-left', 'bias_score': 3, 'fact_accuracy': 'high', 'notes': 'Public broadcaster with strong fact-checking standards'},
    'BBC': {'credibility_score': 88, 'political_bias': 'center', 'bias_score': 2, 'fact_accuracy': 'very high', 'notes': 'International public broadcaster with rigorous editorial standards'},
    'Reuters': {'credibility_score': 90, 'political_bias': 'center', 'bias_score': 1, 'fact_accuracy': 'very high', 'notes': 'International news agency focused on factual reporting'},
    'Associated Press': {'credibility_score': 90, 'political_bias': 'center', 'bias_score': 1, 'fact_accuracy': 'very high', 'notes': 'Cooperative news agency with high editorial standards'},
    'AP': {'credibility_score': 90, 'political_bias': 'center', 'bias_score': 1, 'fact_accuracy': 'very high', 'notes': 'Associated Press - high editorial standards'},
    'The Wall Street Journal': {'credibility_score': 82, 'political_bias': 'center-right', 'bias_score': 3, 'fact_accuracy': 'high', 'notes': 'Business-focused with strong reporting (opinion pages lean right)'},

    # Medium-High Credibility (70-79)
    'The New York Times': {'credibility_score': 78, 'political_bias': 'center-left', 'bias_score': 4, 'fact_accuracy': 'high', 'notes': 'Major newspaper with thorough reporting; some editorial lean'},
    'The Washington Post': {'credibility_score': 76, 'political_bias': 'center-left', 'bias_score': 4, 'fact_accuracy': 'high', 'notes': 'Strong investigative journalism; editorial lean'},
    'CNN': {'credibility_score': 72, 'political_bias': 'center-left', 'bias_score': 4, 'fact_accuracy': 'generally factual', 'notes': 'Cable news network with center-left editorial perspective'},
    'The Guardian': {'credibility_score': 74, 'political_bias': 'left', 'bias_score': 5, 'fact_accuracy': 'generally factual', 'notes': 'British newspaper with progressive editorial stance'},
    'Politico': {'credibility_score': 75, 'political_bias': 'center', 'bias_score': 3, 'fact_accuracy': 'high', 'notes': 'Political journalism focused on policy and Washington'},
    'The Independent': {'credibility_score': 70, 'political_bias': 'center-left', 'bias_score': 4, 'fact_accuracy': 'generally factual', 'notes': 'British newspaper with center-left perspective'},

    # Medium Credibility (60-69)
    'Financial Times': {'credibility_score': 80, 'political_bias': 'center', 'bias_score': 2, 'fact_accuracy': 'high', 'notes': 'International business newspaper with strong economic analysis'},
    'ESPN': {'credibility_score': 65, 'political_bias': 'center', 'bias_score': 1, 'fact_accuracy': 'factual', 'notes': 'Sports journalism - credibility for sports, not political news'},

    # Government/Official
    'The White House (.gov)': {'credibility_score': 75, 'political_bias': 'government', 'bias_score': 5, 'fact_accuracy': 'official', 'notes': 'Official government source - factual but reflects current administration'},

    # Default for unknown sources
    'Unknown': {'credibility_score': 60, 'political_bias': 'unknown', 'bias_score': 5, 'fact_accuracy': 'unknown', 'notes': 'Source not in credibility database'}
}


def score_article_credibility(tool_context: ToolContext) -> Dict:
    """
    Score credibility and bias for all preprocessed articles based on source.

    For MVP, uses a simple source-based scoring system.
    Future versions can integrate Google Fact Check API, Wikidata, etc.

    Args:
        tool_context: ADK tool context with preprocessed articles in state

    Returns:
        Dictionary with credibility scores and statistics
    """
    # Get preprocessed articles from state
    articles = tool_context.state.get('preprocessed_articles', [])

    if not articles:
        return {
            'success': False,
            'error': 'No preprocessed articles found. Run preprocessor first.',
            'scored_count': 0
        }

    scored_articles = []
    credibility_stats = {
        'high_credibility': 0,  # score >= 80
        'medium_credibility': 0,  # score 60-79
        'low_credibility': 0,  # score < 60
        'high_bias': 0,  # bias score >= 7
        'low_bias': 0,  # bias score < 4
    }

    for article in articles:
        # Skip if article is not a dictionary
        if not isinstance(article, dict):
            continue

        source = article.get('source', 'Unknown')

        # Get credibility data for source (use Unknown as default)
        cred_data = SOURCE_CREDIBILITY.get(source, SOURCE_CREDIBILITY['Unknown'])

        # Add credibility metadata to article
        scored_article = article.copy()
        scored_article['credibility_score'] = cred_data['credibility_score']
        scored_article['bias_score'] = cred_data['bias_score']
        scored_article['fact_accuracy_rating'] = cred_data['fact_accuracy']
        scored_article['credibility_notes'] = cred_data['notes']

        # Update statistics
        if cred_data['credibility_score'] >= 80:
            credibility_stats['high_credibility'] += 1
        elif cred_data['credibility_score'] >= 60:
            credibility_stats['medium_credibility'] += 1
        else:
            credibility_stats['low_credibility'] += 1

        if cred_data['bias_score'] >= 7:
            credibility_stats['high_bias'] += 1
        elif cred_data['bias_score'] < 4:
            credibility_stats['low_bias'] += 1

        scored_articles.append(scored_article)

    # Check if any articles were successfully scored
    if not scored_articles:
        return {
            'success': False,
            'error': 'No valid articles found to score. All articles were invalid or skipped.',
            'scored_count': 0
        }

    # Store scored articles in state
    tool_context.state['fact_checked_articles'] = scored_articles
    tool_context.state['credibility_stats'] = credibility_stats

    return {
        'success': True,
        'scored_count': len(scored_articles),
        'credibility_stats': credibility_stats,
        'avg_credibility': sum(a['credibility_score'] for a in scored_articles) / len(scored_articles),
        'avg_bias': sum(a['bias_score'] for a in scored_articles) / len(scored_articles)
    }


def flag_dubious_claims(tool_context: ToolContext) -> Dict:
    """
    Flag claims that may require human review based on simple heuristics.

    For MVP, uses basic pattern matching.
    Future versions can use external fact-check APIs.

    Args:
        tool_context: ADK tool context with fact-checked articles

    Returns:
        Dictionary with flagged claims
    """
    # Get fact-checked articles
    articles = tool_context.state.get('fact_checked_articles', [])

    if not articles:
        return {
            'success': False,
            'error': 'No fact-checked articles found.',
            'flagged_count': 0
        }

    # Keywords that might indicate claims needing verification
    verification_keywords = [
        'reportedly', 'allegedly', 'claims', 'unconfirmed',
        'sources say', 'anonymous', 'rumored', 'speculation'
    ]

    flagged_claims = []
    total_claims = 0

    for article in articles:
        # Skip if article is not a dictionary
        if not isinstance(article, dict):
            continue

        claims = article.get('claims', [])
        total_claims += len(claims)

        for claim in claims:
            claim_lower = claim.lower()

            # Flag claims with verification keywords
            needs_verification = any(keyword in claim_lower for keyword in verification_keywords)

            # Flag claims from high-bias sources
            high_bias = article.get('bias_score', 0) >= 7

            if needs_verification or high_bias:
                flagged_claims.append({
                    'claim': claim,
                    'source': article.get('source'),
                    'article_title': article.get('title'),
                    'reason': 'verification_keyword' if needs_verification else 'high_bias_source',
                    'credibility_score': article.get('credibility_score')
                })

    # Store flagged claims
    tool_context.state['flagged_claims'] = flagged_claims

    return {
        'success': True,
        'total_claims': total_claims,
        'flagged_count': len(flagged_claims),
        'flag_rate': len(flagged_claims) / total_claims if total_claims > 0 else 0,
        'sample_flagged': flagged_claims[:3]
    }
