"""
Temporary test script to verify Google News collector works.
"""

import sys
from datetime import datetime
from manis_agent.agents.collectors.google_news_collector.tools import fetch_google_news_rss

# Mock ToolContext for testing
class MockToolContext:
    def __init__(self):
        self.state = {}

def test_google_news_collector():
    print("=" * 80)
    print("GOOGLE NEWS COLLECTOR TEST")
    print("=" * 80)
    print(f"Current time: {datetime.now().isoformat()}")
    print()

    # Create mock context
    context = MockToolContext()

    # Test Politics topic
    print("-" * 80)
    print("TESTING: Google News Politics")
    print("-" * 80)
    politics_result = fetch_google_news_rss(
        topic='politics',
        max_articles=3,
        tool_context=context
    )

    print(f"Success: {politics_result.get('success')}")
    print(f"Articles collected: {politics_result.get('count', 0)}")

    if 'error' in politics_result:
        print(f"ERROR: {politics_result['error']}")

    if 'debug_info' in politics_result:
        debug = politics_result['debug_info']
        print("\nDEBUG INFO:")
        print(f"  - Total RSS entries available: {debug.get('total_rss_entries', 'N/A')}")
        print(f"  - Entries checked: {debug.get('entries_checked', 'N/A')}")
        print(f"  - Entries too old (>48hrs): {debug.get('entries_too_old', 'N/A')}")
        print(f"  - Entries with parse failures: {debug.get('entries_parse_failed', 'N/A')}")
        print(f"  - Entries missing titles: {debug.get('entries_missing_title', 'N/A')}")
        print(f"  - Cutoff time: {debug.get('cutoff_time', 'N/A')}")

    print()

    # Test Technology topic
    print("-" * 80)
    print("TESTING: Google News Technology")
    print("-" * 80)
    tech_result = fetch_google_news_rss(
        topic='technology',
        max_articles=2,
        tool_context=context
    )

    print(f"Success: {tech_result.get('success')}")
    print(f"Articles collected: {tech_result.get('count', 0)}")

    if 'error' in tech_result:
        print(f"ERROR: {tech_result['error']}")

    if 'debug_info' in tech_result:
        debug = tech_result['debug_info']
        print("\nDEBUG INFO:")
        print(f"  - Total RSS entries available: {debug.get('total_rss_entries', 'N/A')}")
        print(f"  - Entries checked: {debug.get('entries_checked', 'N/A')}")
        print(f"  - Entries too old (>48hrs): {debug.get('entries_too_old', 'N/A')}")
        print(f"  - Entries with parse failures: {debug.get('entries_parse_failed', 'N/A')}")
        print(f"  - Entries missing titles: {debug.get('entries_missing_title', 'N/A')}")
        print(f"  - Cutoff time: {debug.get('cutoff_time', 'N/A')}")

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Google News articles collected: {len(context.state.get('collected_articles', []))}")
    print()

    # Show article titles if any were collected
    articles = context.state.get('collected_articles', [])
    if articles:
        print("COLLECTED ARTICLES:")
        for i, article in enumerate(articles, 1):
            print(f"\n  {i}. [{article.get('category', 'unknown')}] {article.get('title', 'No title')}")
            print(f"     Source: {article.get('source', 'Unknown')}")
            print(f"     Original Source: {article.get('original_source', 'Unknown')}")
            print(f"     Published: {article.get('timestamp', 'Unknown')}")
            print(f"     URL: {article.get('url', 'No URL')[:80]}...")
    else:
        print("⚠️  NO ARTICLES COLLECTED - See debug info above for reasons")

    print()
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_google_news_collector()
    except Exception as e:
        print(f"ERROR running test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
