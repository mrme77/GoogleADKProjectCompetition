"""RSS feed collection tool for Google News."""

import feedparser
import json
from datetime import datetime, timedelta
from typing import Dict, List
from bs4 import BeautifulSoup
from google.adk.tools.tool_context import ToolContext


def fetch_google_news_rss(
    topic: str,
    max_articles: int,
    tool_context: ToolContext
) -> Dict:
    """
    Fetch recent articles from Google News RSS feeds.

    Args:
        topic: News topic ('politics', 'technology', or 'europe')
        max_articles: Maximum number of articles to fetch
        tool_context: ADK tool context for state management

    Returns:
        Dictionary containing list of articles with metadata
    """
    # Clear collected_articles on first topic (politics) to ensure fresh collection
    if topic == 'politics':
        print("[GOOGLE NEWS DEBUG] Clearing collected_articles state for fresh collection")
        tool_context.state['collected_articles'] = []

    # Google News RSS search URLs
    # Format: https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en

    topic_queries = {
        'politics': 'US+politics+OR+election+OR+congress+OR+senate+OR+white+house',
        'technology': 'technology+OR+tech+OR+AI+OR+cybersecurity+OR+software',
        'europe': 'Europe+OR+European+Union+OR+Ukraine+war+OR+Russia+Ukraine+OR+NATO+OR+EU+OR+tragedy+Europe'
    }

    if topic not in topic_queries:
        return {
            'success': False,
            'error': f'Invalid topic: {topic}. Use "politics" or "technology".',
            'articles': []
        }

    try:
        # Build Google News RSS URL
        query = topic_queries[topic]
        feed_url = f'https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en'

        # Fetch RSS feed
        feed = feedparser.parse(feed_url)

        if not hasattr(feed, 'entries') or not feed.entries:
            return {
                'success': False,
                'error': f'No entries found in Google News {topic} RSS feed',
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
        entries_missing_title = 0

        print(f"[GOOGLE NEWS DEBUG] Starting loop for topic '{topic}' - checking up to {max_articles * 3} entries (out of {total_entries} total)")
        print(f"[GOOGLE NEWS DEBUG] Cutoff time (UTC): {cutoff_time.isoformat()}")
        print(f"[GOOGLE NEWS DEBUG] Current time (UTC): {datetime.utcnow().isoformat()}")

        for entry in feed.entries[:max_articles * 3]:  # Fetch extra in case some are old
            entries_checked += 1
            entry_title = getattr(entry, 'title', 'NO TITLE')[:60]
            print(f"[GOOGLE NEWS DEBUG] Entry #{entries_checked}: {entry_title}")

            # Parse publication date with better error handling
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                    print(f"[GOOGLE NEWS DEBUG]   Date: {pub_date.isoformat()} (from published_parsed)")
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                    print(f"[GOOGLE NEWS DEBUG]   Date: {pub_date.isoformat()} (from updated_parsed)")
                else:
                    # If no date available, skip this article
                    print(f"[GOOGLE NEWS DEBUG]   ❌ SKIP: No date fields found")
                    entries_parse_failed += 1
                    continue
            except Exception as e:
                # Log the error but skip this article instead of using now()
                print(f"[GOOGLE NEWS DEBUG]   ❌ SKIP: Date parse error: {e}")
                entries_parse_failed += 1
                continue

            # Only include articles from last 48 hours
            if pub_date < cutoff_time:
                print(f"[GOOGLE NEWS DEBUG]   ❌ SKIP: Too old ({pub_date.isoformat()} < {cutoff_time.isoformat()})")
                entries_too_old += 1
                continue

            # Extract title with better handling for empty/None values
            title = None
            if hasattr(entry, 'title') and entry.title:
                title = str(entry.title).strip()

            # Skip articles without titles
            if not title:
                print(f"[GOOGLE NEWS DEBUG]   ❌ SKIP: No title found")
                entries_missing_title += 1
                continue

            print(f"[GOOGLE NEWS DEBUG]   ✅ Title OK: {title[:50]}")

            # Extract source from title (Google News format: "Title - Source")
            source = 'Google News'
            if ' - ' in title:
                title_parts = title.rsplit(' - ', 1)
                if len(title_parts) == 2:
                    title = title_parts[0].strip()
                    source = title_parts[1].strip()

            # Extract clean text from description/summary
            description = str(entry.get('summary', entry.get('description', '')))
            soup = BeautifulSoup(description, 'html.parser')
            clean_description = str(soup.get_text().strip())

            article = {
                'title': title,
                'url': str(entry.link) if hasattr(entry, 'link') else '',
                'source': source,  # Use original source name directly
                'aggregator': 'Google News',
                'political_leaning': 'aggregated',  # Google News aggregates from multiple sources
                'region': 'US',
                'category': topic,
                'timestamp': pub_date.isoformat(),
                'description': str(clean_description),
                'text': str(clean_description)  # For MVP, using description as text
            }

            # Article passed all filters - add it
            articles.append(article)
            print(f"[GOOGLE NEWS DEBUG]   ✅ COLLECTED article #{len(articles)}: {title[:50]}")

            if len(articles) >= max_articles:
                print(f"[GOOGLE NEWS DEBUG] Reached max_articles ({max_articles}), breaking loop")
                break

        # Debug summary
        print(f"[GOOGLE NEWS DEBUG] Loop complete for '{topic}'. Collected {len(articles)} articles before JSON validation")

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
            'source': 'Google News',
            'topic': topic,
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
            'error': f'Failed to fetch Google News RSS: {str(e)}',
            'articles': []
        }
