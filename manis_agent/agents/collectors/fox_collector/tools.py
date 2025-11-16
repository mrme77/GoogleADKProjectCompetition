"""RSS feed collection tool for Fox News."""

import feedparser
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List
from bs4 import BeautifulSoup
from google.adk.tools.tool_context import ToolContext


def fetch_fox_news_rss(
    category: str,
    max_articles: int,
    tool_context: ToolContext
) -> Dict:
    """
    Fetch recent articles from Fox News RSS feeds.

    Args:
        category: News category ('politics' or 'tech')
        max_articles: Maximum number of articles to fetch (default 5)
        tool_context: ADK tool context for state management

    Returns:
        Dictionary containing list of articles with metadata
    """
    # Fox News RSS feed URLs
    feed_urls = {
        'politics': 'https://moxie.foxnews.com/google-publisher/politics.xml',
        'tech': 'https://moxie.foxnews.com/google-publisher/tech.xml'
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
                'error': f'No entries found in Fox News {category} RSS feed',
                'articles': [],
                'debug_info': f'Feed status: {getattr(feed, "status", "unknown")}'
            }

        articles = []
        cutoff_time = datetime.utcnow() - timedelta(hours=48)  # Use UTC to match RSS feed timestamps

        # Debugging counters
        total_entries = len(feed.entries)
        entries_checked = 0
        entries_too_old = 0
        entries_parse_failed = 0

        print(f"[FOX DEBUG] Starting loop through first {max_articles * 2} entries (out of {total_entries} total)")
        print(f"[FOX DEBUG] Cutoff time: {cutoff_time.isoformat()}")

        for entry in feed.entries[:max_articles * 2]:  # Fetch extra in case some are old
            entries_checked += 1
            entry_title = getattr(entry, 'title', 'NO TITLE')[:50]
            print(f"[FOX DEBUG] Entry #{entries_checked}: {entry_title}")

            # Parse publication date with better error handling
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                    print(f"[FOX DEBUG]   Date: {pub_date.isoformat()} (from published_parsed)")
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                    print(f"[FOX DEBUG]   Date: {pub_date.isoformat()} (from updated_parsed)")
                else:
                    # If no date available, skip this article
                    print(f"[FOX DEBUG]   ❌ SKIP: No date fields found")
                    entries_parse_failed += 1
                    continue
            except Exception as e:
                # Log the error but skip this article instead of using now()
                print(f"[FOX DEBUG]   ❌ SKIP: Date parse error: {e}")
                entries_parse_failed += 1
                continue

            # Only include articles from last 48 hours
            if pub_date < cutoff_time:
                print(f"[FOX DEBUG]   ❌ SKIP: Too old ({pub_date.isoformat()} < {cutoff_time.isoformat()})")
                entries_too_old += 1
                continue

            # Extract clean text from description
            description = str(entry.get('summary', ''))
            soup = BeautifulSoup(description, 'html.parser')
            clean_description = str(soup.get_text().strip())

            article = {
                'title': str(entry.title) if hasattr(entry, 'title') else 'No title',
                'url': str(entry.link) if hasattr(entry, 'link') else '',
                'source': 'Fox News',
                'political_leaning': 'right',
                'region': 'US',
                'category': category,
                'timestamp': pub_date.isoformat(),
                'description': str(clean_description),
                'text': str(clean_description)  # For MVP, using description as text
            }

            # Final check passed - add article
            articles.append(article)

            # Debug: print when article is successfully added
            print(f"[FOX DEBUG] Added article #{len(articles)}: {title[:50]}...")

            if len(articles) >= max_articles:
                print(f"[FOX DEBUG] Reached max_articles limit ({max_articles}), breaking loop")
                break

        # Debug summary before JSON check
        print(f"[FOX DEBUG] Loop complete. Collected {len(articles)} articles before JSON validation")

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
            'source': 'Fox News',
            'category': category,
            'count': len(articles),
            'articles': [],  # Don't return articles in response to avoid duplication in state
            'debug_info': {
                'total_rss_entries': total_entries,
                'entries_checked': entries_checked,
                'entries_too_old': entries_too_old,
                'entries_parse_failed': entries_parse_failed,
                'cutoff_time': cutoff_time.isoformat()
            }
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to fetch Fox News RSS: {str(e)}',
            'articles': []
        }
