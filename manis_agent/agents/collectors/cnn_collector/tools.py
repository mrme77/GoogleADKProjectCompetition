"""RSS feed collection tool for CNN."""

import feedparser
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List
from bs4 import BeautifulSoup
from google.adk.tools.tool_context import ToolContext


def fetch_cnn_rss(
    category: str,
    max_articles: int,
    tool_context: ToolContext
) -> Dict:
    """
    Fetch recent articles from CNN RSS feeds.

    Args:
        category: News category ('politics' or 'tech')
        max_articles: Maximum number of articles to fetch (default 5)
        tool_context: ADK tool context for state management

    Returns:
        Dictionary containing list of articles with metadata
    """
    # CNN RSS feed URLs
    feed_urls = {
        'politics': 'http://rss.cnn.com/rss/cnn_allpolitics.rss',
        'tech': 'http://rss.cnn.com/rss/cnn_tech.rss'
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

        if not hasattr(feed, 'entries') or not feed.entries:
            return {
                'success': False,
                'error': f'No entries found in CNN {category} RSS feed',
                'articles': [],
                'debug_info': f'Feed status: {getattr(feed, "status", "unknown")}'
            }

        articles = []
        cutoff_time = datetime.now() - timedelta(hours=48)  # Extended to 48 hours for better results

        # Debugging counters
        total_entries = len(feed.entries)
        entries_checked = 0
        entries_too_old = 0
        entries_parse_failed = 0
        entries_missing_title = 0

        for entry in feed.entries[:max_articles * 2]:  # Fetch extra in case some are old
            entries_checked += 1

            # Parse publication date with better error handling
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                else:
                    # If no date available, skip this article
                    entries_parse_failed += 1
                    continue
            except Exception as e:
                # Log the error but skip this article instead of using now()
                entries_parse_failed += 1
                continue

            # Only include articles from last 48 hours
            if pub_date < cutoff_time:
                entries_too_old += 1
                continue

            # Extract title with better handling for empty/None values
            title = None
            if hasattr(entry, 'title') and entry.title:
                title = str(entry.title).strip()

            # Skip articles without titles
            if not title:
                entries_missing_title += 1
                continue

            # Extract clean text from description/summary
            description = str(entry.get('summary', entry.get('description', '')))
            soup = BeautifulSoup(description, 'html.parser')
            clean_description = str(soup.get_text().strip())

            article = {
                'title': title,
                'url': str(entry.link) if hasattr(entry, 'link') else '',
                'source': 'CNN',
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
            'source': 'CNN',
            'category': category,
            'count': len(articles),
            'articles': [],  # Don't return articles in response to avoid duplication in state
            'debug_info': {
                'total_rss_entries': total_entries,
                'entries_checked': entries_checked,
                'entries_too_old': entries_too_old,
                'entries_parse_failed': entries_parse_failed,
                'entries_missing_title': entries_missing_title,
                'cutoff_time': cutoff_time.isoformat()
            }
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to fetch CNN RSS: {str(e)}',
            'articles': []
        }
