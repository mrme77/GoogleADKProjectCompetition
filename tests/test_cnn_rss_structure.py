"""
Test script to examine CNN RSS feed structure and date formats.
"""

import feedparser
from datetime import datetime

def inspect_cnn_rss():
    print("=" * 80)
    print("CNN RSS FEED STRUCTURE INSPECTION")
    print("=" * 80)
    print()

    feeds = {
        'Politics': 'http://rss.cnn.com/rss/cnn_allpolitics.rss',
        'Tech': 'http://rss.cnn.com/rss/cnn_tech.rss'
    }

    for name, url in feeds.items():
        print("-" * 80)
        print(f"FEED: CNN {name}")
        print(f"URL: {url}")
        print("-" * 80)

        feed = feedparser.parse(url)

        if not hasattr(feed, 'entries') or not feed.entries:
            print(f"⚠️  No entries found!")
            continue

        print(f"Total entries: {len(feed.entries)}")
        print()

        # Examine first 3 entries
        for i, entry in enumerate(feed.entries[:3], 1):
            print(f"\n{'─' * 40}")
            print(f"ENTRY #{i}")
            print(f"{'─' * 40}")

            # Title
            if hasattr(entry, 'title'):
                print(f"Title: {entry.title}")
            else:
                print("Title: ❌ NOT FOUND")

            # Link
            if hasattr(entry, 'link'):
                print(f"Link: {entry.link[:60]}...")

            # Check all possible date fields
            date_fields = [
                'published', 'published_parsed',
                'updated', 'updated_parsed',
                'created', 'created_parsed',
                'pubDate', 'pubdate'
            ]

            print("\nDate Fields:")
            found_date = False
            for field in date_fields:
                if hasattr(entry, field):
                    value = getattr(entry, field)
                    if value:
                        found_date = True
                        if '_parsed' in field and value:
                            try:
                                dt = datetime(*value[:6])
                                print(f"  ✅ {field}: {value} → {dt.isoformat()}")
                            except:
                                print(f"  ⚠️  {field}: {value} (parse failed)")
                        else:
                            print(f"  ✅ {field}: {value}")

            if not found_date:
                print("  ❌ NO DATE FIELDS FOUND!")

            # Show all available attributes
            print("\nAll attributes:")
            attrs = [attr for attr in dir(entry) if not attr.startswith('_')]
            print(f"  {', '.join(attrs[:20])}")
            if len(attrs) > 20:
                print(f"  ... and {len(attrs) - 20} more")

        print()

    print("=" * 80)

if __name__ == "__main__":
    inspect_cnn_rss()
