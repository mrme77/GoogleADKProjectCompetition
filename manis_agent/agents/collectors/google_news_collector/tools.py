"""RSS feed collection tool for Google News."""

import feedparser
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List
from bs4 import BeautifulSoup
from google.adk.tools.tool_context import ToolContext


def resolve_google_news_url(google_url: str, timeout: int = 5) -> str:
    """
    Resolve Google News redirect URL to get the actual article URL.

    Google News RSS feeds return URLs like:
    https://news.google.com/rss/articles/CBMi...

    This function follows the redirect to get the actual article URL.

    Args:
        google_url: Google News redirect URL
        timeout: Request timeout in seconds (default: 5)

    Returns:
        Actual article URL, or original URL if resolution fails
    """
    # If URL doesn't look like a Google News redirect, return as-is
    if not google_url or 'news.google.com' not in google_url:
        return google_url

    try:
        # Follow redirects with a short timeout
        response = requests.head(
            google_url,
            allow_redirects=True,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; MANIS/1.0; +https://github.com/yourusername/manis)'
            }
        )

        # Return the final URL after all redirects
        final_url = response.url

        # If we still have a google.com URL, try GET request (some redirects need it)
        if 'google.com' in final_url and final_url != google_url:
            response = requests.get(
                google_url,
                allow_redirects=True,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; MANIS/1.0; +https://github.com/yourusername/manis)'
                }
            )
            final_url = response.url

        return final_url

    except (requests.RequestException, Exception) as e:
        # If redirect resolution fails, return original URL
        print(f"[URL RESOLVE] Failed to resolve {google_url[:60]}... - {str(e)}")
        return google_url


def fetch_google_news_rss(
    topic: str,
    max_articles: int,
    tool_context: ToolContext
) -> Dict:
    """
    Fetch recent articles from Google News RSS feeds with URL resolution.

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
    topic_queries = {
        'politics': 'US+politics+OR+election+OR+congress+OR+senate+OR+white+house',
        'technology': 'technology+OR+tech+OR+AI+OR+cybersecurity+OR+software+-football+-basketball+-sports+-athletics',
        'europe': 'Europe+OR+European+Union+OR+Ukraine+war+OR+Russia+Ukraine+OR+NATO+OR+EU'
    }

    if topic not in topic_queries:
        return {
            'success': False,
            'error': f'Invalid topic: {topic}. Use "politics", "technology", or "europe".',
            'articles': []
        }
    
    # Filter keywords to exclude sports content from technology results
    # This prevents matches like "Georgia Tech Football" or "Virginia Tech Basketball"
    sports_filter_keywords = [
        'football', 'basketball', 'baseball', 'soccer', 'athletics', 
        'touchdown', 'quarterback', 'tournament', 'championship', 
        'varsity', 'recruit', 'roster', 'score', 'game', 'season'
    ]

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
        cutoff_time = datetime.utcnow() - timedelta(hours=48)

        print(f"[GOOGLE NEWS DEBUG] Starting loop for topic '{topic}' - checking up to {max_articles * 3} entries")

        for entry in feed.entries[:max_articles * 3]:
            # Parse publication date
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                else:
                    continue
            except Exception:
                continue

            # Only include articles from last 48 hours
            if pub_date < cutoff_time:
                continue

            # Extract title
            title = None
            if hasattr(entry, 'title') and entry.title:
                title = str(entry.title).strip()

            if not title:
                continue

            # Extract clean description
            description = str(entry.get('summary', entry.get('description', '')))
            soup = BeautifulSoup(description, 'html.parser')
            clean_description = str(soup.get_text().strip())

            # Filter out sports articles from technology category
            if topic == 'technology':
                text_to_check = (title + " " + clean_description).lower()
                is_sports = False
                
                # Check for "Tech" university names combined with sports terms
                # (e.g., "Georgia Tech", "Virginia Tech", "Texas Tech")
                university_tech_indicators = ['georgia tech', 'virginia tech', 'texas tech', 'louisiana tech']
                has_university_tech = any(u in text_to_check for u in university_tech_indicators)
                
                # If it mentions a "Tech" university, be very aggressive with sports filtering
                if has_university_tech:
                    if any(sport in text_to_check for sport in sports_filter_keywords):
                        is_sports = True
                else:
                    # Otherwise just check for strong sports indicators
                    sports_hits = sum(1 for sport in sports_filter_keywords if f" {sport} " in f" {text_to_check} ")
                    if sports_hits >= 2:  # Require at least 2 keywords to be safe
                        is_sports = True
                
                if is_sports:
                    print(f"[GOOGLE NEWS DEBUG]   Skipping sports article: {title[:50]}...")
                    continue

            # Extract source from title (Google News format: "Title - Source")
            source = 'Google News'
            if ' - ' in title:
                title_parts = title.rsplit(' - ', 1)
                if len(title_parts) == 2:
                    title = title_parts[0].strip()
                    source = title_parts[1].strip()

            # Get URL and resolve redirects to actual article URLs
            raw_url = str(entry.link) if hasattr(entry, 'link') else ''
            actual_url = resolve_google_news_url(raw_url)

            print(f"[GOOGLE NEWS DEBUG]   ✅ {title[:50]} - {source}")
            print(f"[GOOGLE NEWS DEBUG]   URL: {actual_url[:70]}")

            article = {
                'title': title,
                'url': actual_url,  # Resolved direct URL
                'source': source,
                'aggregator': 'Google News',
                'original_source': source,
                'region': 'EU/International' if topic == 'europe' else 'US',
                'category': topic,
                'timestamp': pub_date.isoformat(),
                'description': str(clean_description),
                'text': str(clean_description)
            }

            articles.append(article)

            if len(articles) >= max_articles:
                break

        print(f"[GOOGLE NEWS DEBUG] Collected {len(articles)} articles for '{topic}'")

        # Verify JSON serializable
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
            'source': 'Google News RSS',
            'topic': topic,
            'count': len(articles),
            'articles': []
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to fetch Google News RSS: {str(e)}',
            'articles': []
        }
