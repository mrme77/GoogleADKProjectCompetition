"""
Deep debug of Fox News RSS to see why 0 articles are being collected.
"""

import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

def deep_debug_fox():
    print("=" * 80)
    print("DEEP DEBUG: Fox News RSS")
    print("=" * 80)

    feed_url = 'https://moxie.foxnews.com/google-publisher/politics.xml'

    print(f"\nFetching: {feed_url}")
    feed = feedparser.parse(feed_url)

    print(f"Total entries in feed: {len(feed.entries)}")
    print(f"Feed status: {getattr(feed, 'status', 'unknown')}")

    cutoff_time = datetime.now() - timedelta(hours=48)
    print(f"Cutoff time (48hrs ago): {cutoff_time.isoformat()}")
    print(f"Current time: {datetime.now().isoformat()}")

    print("\n" + "=" * 80)
    print("EXAMINING FIRST 5 ENTRIES IN DETAIL")
    print("=" * 80)

    for i, entry in enumerate(feed.entries[:5], 1):
        print(f"\n{'─' * 40}")
        print(f"ENTRY #{i}")
        print(f"{'─' * 40}")

        # Title
        title = getattr(entry, 'title', None)
        print(f"Title: {title if title else '❌ NO TITLE'}")

        # Date parsing
        print("\nDate Analysis:")
        pub_date = None

        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                pub_date = datetime(*entry.published_parsed[:6])
                print(f"  ✅ published_parsed: {pub_date.isoformat()}")
                print(f"     Age: {(datetime.now() - pub_date).days} days, {(datetime.now() - pub_date).seconds // 3600} hours")
            except Exception as e:
                print(f"  ❌ published_parsed exists but parse failed: {e}")
        else:
            print(f"  ❌ No published_parsed")

        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                updated = datetime(*entry.updated_parsed[:6])
                print(f"  ✅ updated_parsed: {updated.isoformat()}")
                if not pub_date:
                    pub_date = updated
            except Exception as e:
                print(f"  ❌ updated_parsed exists but parse failed: {e}")

        # Date filter check
        if pub_date:
            is_too_old = pub_date < cutoff_time
            print(f"\n  Date Check:")
            print(f"    Article date: {pub_date.isoformat()}")
            print(f"    Cutoff date:  {cutoff_time.isoformat()}")
            print(f"    Too old? {'❌ YES - WOULD BE FILTERED' if is_too_old else '✅ NO - WOULD PASS'}")
        else:
            print(f"\n  ❌ NO VALID DATE - WOULD BE FILTERED (parse_failed += 1)")

        # Description check
        description = entry.get('summary', '')
        if description:
            soup = BeautifulSoup(description, 'html.parser')
            clean_desc = soup.get_text().strip()
            print(f"\nDescription: {clean_desc[:100]}...")
        else:
            print(f"\nDescription: ❌ NONE")

        # Would this article be collected?
        print(f"\n{'═' * 40}")
        would_collect = title and pub_date and pub_date >= cutoff_time
        if would_collect:
            print(f"RESULT: ✅ WOULD BE COLLECTED")
        else:
            reasons = []
            if not title:
                reasons.append("no title")
            if not pub_date:
                reasons.append("no valid date")
            if pub_date and pub_date < cutoff_time:
                reasons.append(f"too old ({(datetime.now() - pub_date).days}d)")
            print(f"RESULT: ❌ WOULD BE FILTERED ({', '.join(reasons)})")
        print(f"{'═' * 40}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    deep_debug_fox()
