"""RSS feed collection tool for Reuters."""

import feedparser
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List
from bs4 import BeautifulSoup
from google.adk.tools.tool_context import ToolContext


def fetch_reuters_rss(
    category: str,
    max_articles: int,
    tool_context: ToolContext
) -> Dict:
    """
    Fetch recent articles from Reuters RSS feeds.

    Args:
        category: News category ('politics' or 'tech')
        max_articles: Maximum number of articles to fetch (default 5)
        tool_context: ADK tool context for state management

    Returns:
        Dictionary containing list of articles with metadata
    """
    # Reuters RSS feed URLs (updated to working feeds)
    feed_urls = {
        'politics': 'https://www.reuters.com/rssfeed/politicsNews',
        'tech': 'https://www.reuters.com/rssfeed/technologyNews'
    }

    if category not in feed_urls:
        return {
            'success': False,
            'error': f'Invalid category: {category}. Use "politics" or "tech".',
            'articles': []
        }

    try:
        # Fetch RSS feed
        feed = feedparser.parse(feed_urls[category])

        articles = []
        cutoff_time = datetime.now() - timedelta(hours=48)  # Extended to 48 hours for better results

        for entry in feed.entries[:max_articles * 2]:  # Fetch extra in case some are old
            # Parse publication date
            try:
                pub_date = datetime(*entry.published_parsed[:6])
            except:
                pub_date = datetime.now()

            # Only include articles from last 24 hours
            if pub_date < cutoff_time:
                continue

            # Extract clean text from description/summary
            description = str(entry.get('summary', entry.get('description', '')))
            soup = BeautifulSoup(description, 'html.parser')
            clean_description = str(soup.get_text().strip())

            article = {
                'title': str(entry.title) if hasattr(entry, 'title') else 'No title',
                'url': str(entry.link) if hasattr(entry, 'link') else '',
                'source': 'Reuters',
                'political_leaning': 'center-left',
                'region': 'US',
                'category': category,
                'timestamp': pub_date.isoformat(),
                'description': str(clean_description),
                'text': str(clean_description)  # For MVP, using description as text
            }

            articles.append(article)

            if len(articles) >= max_articles:
                break

        # Verify all articles are JSON serializable before storing
        try:
            json.dumps(articles)
        except (TypeError, ValueError) as e:
            return {
                'success': False,
                'error': f'Article data contains non-JSON-serializable content: {str(e)}',
                'articles': []
            }

        # Store in session state
        current_articles = tool_context.state.get('collected_articles', [])
        current_articles.extend(articles)
        tool_context.state['collected_articles'] = current_articles

        return {
            'success': True,
            'source': 'Reuters',
            'category': category,
            'count': len(articles),
            'articles': []  # Don't return articles in response to avoid duplication in state
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to fetch Reuters RSS: {str(e)}',
            'articles': []
        }
