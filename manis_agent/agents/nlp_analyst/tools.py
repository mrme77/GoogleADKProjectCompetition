"""NLP analysis tools for sentiment and bias detection."""

from typing import Dict, List
from google.adk.tools.tool_context import ToolContext
from textblob import TextBlob
import re
from collections import Counter


def analyze_sentiment(tool_context: ToolContext) -> Dict:
    """
    Analyze sentiment for all fact-checked articles using TextBlob.

    Sentiment scores:
    - Polarity: -1 (negative) to +1 (positive)
    - Subjectivity: 0 (objective) to 1 (subjective)

    Args:
        tool_context: ADK tool context with fact-checked articles

    Returns:
        Dictionary with sentiment analysis results
    """
    # Get fact-checked articles
    articles = tool_context.state.get('fact_checked_articles', [])

    if not articles:
        return {
            'success': False,
            'error': 'No fact-checked articles found. Run fact checker first.',
            'analyzed_count': 0
        }

    analyzed_articles = []
    sentiment_stats = {
        'positive': 0,
        'negative': 0,
        'neutral': 0
    }

    total_polarity = 0
    total_subjectivity = 0

    for article in articles:
        # Skip if article is not a dictionary
        if not isinstance(article, dict):
            continue

        text = article.get('clean_text', article.get('text', ''))

        # Analyze with TextBlob
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        # Classify sentiment
        if polarity > 0.1:
            sentiment_category = 'positive'
            sentiment_stats['positive'] += 1
        elif polarity < -0.1:
            sentiment_category = 'negative'
            sentiment_stats['negative'] += 1
        else:
            sentiment_category = 'neutral'
            sentiment_stats['neutral'] += 1

        # Add sentiment data to article
        analyzed_article = article.copy()
        analyzed_article['sentiment_polarity'] = round(polarity, 3)
        analyzed_article['sentiment_subjectivity'] = round(subjectivity, 3)
        analyzed_article['sentiment_category'] = sentiment_category

        total_polarity += polarity
        total_subjectivity += subjectivity

        analyzed_articles.append(analyzed_article)

    # Check if any articles were successfully analyzed
    if not analyzed_articles:
        return {
            'success': False,
            'error': 'No valid articles found to analyze. All articles were invalid or skipped.',
            'analyzed_count': 0
        }

    # Store analyzed articles
    tool_context.state['nlp_analyzed_articles'] = analyzed_articles
    tool_context.state['sentiment_stats'] = {
        **sentiment_stats,
        'avg_polarity': round(total_polarity / len(analyzed_articles), 3),
        'avg_subjectivity': round(total_subjectivity / len(analyzed_articles), 3)
    }

    return {
        'success': True,
        'analyzed_count': len(analyzed_articles),
        'sentiment_distribution': sentiment_stats,
        'avg_polarity': round(total_polarity / len(articles), 3),
        'avg_subjectivity': round(total_subjectivity / len(articles), 3)
    }


def detect_political_bias(tool_context: ToolContext) -> Dict:
    """
    Detect political bias indicators in article language.

    Uses keyword analysis and framing patterns to identify bias signals.
    Aggregates bias signals by source across collected articles.

    Args:
        tool_context: ADK tool context with NLP analyzed articles

    Returns:
        Dictionary with bias analysis results
    """
    # Get NLP analyzed articles
    articles = tool_context.state.get('nlp_analyzed_articles', [])

    if not articles:
        return {
            'success': False,
            'error': 'No NLP analyzed articles found. Run sentiment analysis first.',
            'analyzed_count': 0
        }

    # Political bias keyword indicators
    left_keywords = [
        'progressive', 'reform', 'equality', 'climate', 'healthcare',
        'workers', 'regulation', 'discrimination', 'rights', 'justice'
    ]

    right_keywords = [
        'conservative', 'traditional', 'freedom', 'security', 'border',
        'tax', 'deregulation', 'law and order', 'values', 'patriot'
    ]

    # Emotional language patterns
    emotional_words = [
        'crisis', 'disaster', 'threat', 'dangerous', 'attack', 'destroy',
        'scandal', 'corrupt', 'failing', 'radical', 'extreme'
    ]

    # Track bias by source (dynamically build as we find sources)
    bias_analysis = {}

    for article in articles:
        # Skip if article is not a dictionary
        if not isinstance(article, dict):
            continue

        text_lower = article.get('clean_text', '').lower()
        source = article.get('source', '')

        # Count bias indicators
        left_count = sum(1 for keyword in left_keywords if keyword in text_lower)
        right_count = sum(1 for keyword in right_keywords if keyword in text_lower)
        emotional_count = sum(1 for word in emotional_words if word in text_lower)

        # Determine bias direction
        if left_count > right_count:
            bias_direction = 'left-leaning'
        elif right_count > left_count:
            bias_direction = 'right-leaning'
        else:
            bias_direction = 'neutral'

        # Add bias analysis to article
        article['bias_direction'] = bias_direction
        article['left_keyword_count'] = left_count
        article['right_keyword_count'] = right_count
        article['emotional_language_count'] = emotional_count

        # Aggregate by source (dynamically create entries for each source)
        source_key = source.replace(' ', '_').lower()
        if source_key not in bias_analysis:
            bias_analysis[source_key] = {
                'left_signals': 0,
                'right_signals': 0,
                'emotional_language': 0,
                'articles': 0,
                'display_name': source
            }

        bias_analysis[source_key]['left_signals'] += left_count
        bias_analysis[source_key]['right_signals'] += right_count
        bias_analysis[source_key]['emotional_language'] += emotional_count
        bias_analysis[source_key]['articles'] += 1

    # Store updated articles and bias analysis
    tool_context.state['bias_analyzed_articles'] = articles
    tool_context.state['bias_analysis'] = bias_analysis

    # Build summary for each source
    sources_summary = {}
    for source_key, data in bias_analysis.items():
        sources_summary[source_key] = {
            'display_name': data['display_name'],
            'articles': data['articles'],
            'avg_left_signals': round(data['left_signals'] / max(1, data['articles']), 2),
            'avg_right_signals': round(data['right_signals'] / max(1, data['articles']), 2),
            'avg_emotional': round(data['emotional_language'] / max(1, data['articles']), 2)
        }

    return {
        'success': True,
        'analyzed_count': len(articles),
        'total_sources': len(bias_analysis),
        'sources': sources_summary
    }


def extract_keywords(tool_context: ToolContext) -> Dict:
    """
    Extract top keywords across all articles.

    Args:
        tool_context: ADK tool context with bias analyzed articles

    Returns:
        Dictionary with top keywords
    """
    articles = tool_context.state.get('bias_analyzed_articles', [])

    if not articles:
        return {
            'success': False,
            'error': 'No bias analyzed articles found.',
            'keyword_count': 0
        }

    # Combine all article text
    all_text = ' '.join(article.get('clean_text', '') for article in articles).lower()

    # Simple tokenization and filtering
    words = re.findall(r'\b[a-z]{4,}\b', all_text)  # Words with 4+ letters

    # Common words to exclude (stopwords)
    stopwords = {
        'that', 'this', 'with', 'from', 'have', 'been', 'their', 'said',
        'will', 'were', 'what', 'would', 'there', 'about', 'which', 'when',
        'they', 'more', 'than', 'other', 'some', 'into', 'could', 'only'
    }

    # Filter and count
    filtered_words = [word for word in words if word not in stopwords]
    word_counts = Counter(filtered_words)

    top_keywords = word_counts.most_common(20)

    # Store keywords
    tool_context.state['top_keywords'] = top_keywords

    return {
        'success': True,
        'keyword_count': len(word_counts),
        'top_keywords': [{'word': word, 'count': count} for word, count in top_keywords[:10]]
    }
