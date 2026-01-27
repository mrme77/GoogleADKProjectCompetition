"""Unit tests for Google News RSS collector tools."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone
from manis_agent.agents.collectors.google_news_collector.tools import fetch_google_news_rss


class TestFetchGoogleNewsRSS:
    """Tests for fetch_google_news_rss function."""

    def test_fetch_google_news_success(self, mock_tool_context, mock_rss_feed_data):
        """Test successful RSS fetch returns correct structure."""
        with patch('manis_agent.agents.collectors.google_news_collector.tools.feedparser.parse') as mock_parse:
            # Setup mock feed data - convert dict entries to objects
            mock_feed = MagicMock()
            entries = []
            for item in mock_rss_feed_data['entries']:
                entry = MagicMock()
                entry.title = item['title']
                entry.link = item['link']
                entry.summary = item['summary']
                entry.published_parsed = item['published_parsed']
                entry.source = item['source']
                entries.append(entry)
            
            mock_feed.entries = entries
            mock_parse.return_value = mock_feed

            # Execute
            result = fetch_google_news_rss('politics', 5, mock_tool_context)

            # Assert
            assert result['success'] is True
            # The tool returns 'articles': [] in the return value, but populates state['collected_articles']
            # So we check 'count' or look at the state
            assert result['count'] > 0
            
            # Check collected articles in state
            assert 'collected_articles' in mock_tool_context.state
            assert len(mock_tool_context.state['collected_articles']) > 0
            
            article = mock_tool_context.state['collected_articles'][0]
            assert 'title' in article
            assert 'url' in article
            assert 'source' in article
            assert 'timestamp' in article
            assert 'category' in article
            assert article['category'] == 'politics'

    def test_fetch_google_news_invalid_topic(self, mock_tool_context):
        """Test that invalid topic returns error."""
        result = fetch_google_news_rss('invalid_topic', 5, mock_tool_context)

        assert result['success'] is False
        assert 'error' in result
        assert 'Invalid topic' in result['error']
        assert result['articles'] == []

    def test_fetch_google_news_clears_state_on_politics(self, mock_tool_context):
        """Test that fetching politics topic clears collected_articles state."""
        # Setup - add some existing articles
        mock_tool_context.state['collected_articles'] = [{'title': 'Old Article'}]

        with patch('manis_agent.agents.collectors.google_news_collector.tools.feedparser.parse') as mock_parse:
            # Setup mock feed
            mock_feed = MagicMock()
            mock_feed.entries = []
            mock_parse.return_value = mock_feed

            # Execute
            fetch_google_news_rss('politics', 5, mock_tool_context)

            # Assert - state should be cleared
            assert mock_tool_context.state['collected_articles'] == []

    def test_fetch_google_news_respects_max_articles(self, mock_tool_context):
        """Test that max_articles parameter limits results."""
        with patch('manis_agent.agents.collectors.google_news_collector.tools.feedparser.parse') as mock_parse:
            # Create many mock entries
            many_entries = []
            for i in range(20):
                entry = MagicMock()
                entry.title = f'Article {i}'
                entry.link = f'https://example.com/{i}'
                entry.published_parsed = datetime.now(timezone.utc).timetuple()
                entry.summary = f'Summary {i}'
                entry.source = {'title': 'Test Source'}
                many_entries.append(entry)

            mock_feed = MagicMock()
            mock_feed.entries = many_entries
            mock_parse.return_value = mock_feed

            # Execute with max_articles=5
            result = fetch_google_news_rss('technology', 5, mock_tool_context)

            # Assert - should not exceed max_articles
            collected = mock_tool_context.state.get('collected_articles', [])
            assert len(collected) <= 5

    def test_fetch_google_news_handles_network_error(self, mock_tool_context):
        """Test graceful handling of network errors."""
        with patch('manis_agent.agents.collectors.google_news_collector.tools.feedparser.parse') as mock_parse:
            # Simulate network error
            mock_parse.side_effect = Exception('Network error')

            # Execute
            result = fetch_google_news_rss('politics', 5, mock_tool_context)

            # Assert - should return error response
            assert result['success'] is False
            assert 'error' in result

    def test_fetch_google_news_handles_empty_feed(self, mock_tool_context):
        """Test handling of empty RSS feed."""
        with patch('manis_agent.agents.collectors.google_news_collector.tools.feedparser.parse') as mock_parse:
            # Setup empty feed
            mock_feed = MagicMock()
            mock_feed.entries = []
            mock_parse.return_value = mock_feed

            # Execute
            result = fetch_google_news_rss('politics', 5, mock_tool_context)

            # Assert
            assert result['success'] is False
            assert 'error' in result
            assert 'No entries found' in result['error']

    def test_fetch_google_news_updates_state(self, mock_tool_context):
        """Test that state is properly updated with collected articles."""
        with patch('manis_agent.agents.collectors.google_news_collector.tools.feedparser.parse') as mock_parse:
            # Setup mock feed
            mock_feed = MagicMock()
            entry = MagicMock()
            entry.title = 'Test Article'
            entry.link = 'https://example.com/test'
            entry.published_parsed = datetime.now(timezone.utc).timetuple()
            entry.summary = 'Test summary'
            entry.source = {'title': 'Test Source'}
            mock_feed.entries = [entry]
            mock_parse.return_value = mock_feed

            # Execute
            result = fetch_google_news_rss('technology', 5, mock_tool_context)

            # Assert - state should be updated
            assert 'collected_articles' in mock_tool_context.state
            assert len(mock_tool_context.state['collected_articles']) > 0

    def test_fetch_google_news_filters_sports(self, mock_tool_context):
        """Test that sports articles are filtered out from technology topic."""
        with patch('manis_agent.agents.collectors.google_news_collector.tools.feedparser.parse') as mock_parse:
            # Setup mock feed with mix of tech and sports articles
            mock_feed = MagicMock()
            
            # 1. Valid tech article
            entry1 = MagicMock()
            entry1.title = 'New AI Model Released'
            entry1.link = 'https://example.com/ai'
            entry1.published_parsed = datetime.now(timezone.utc).timetuple()
            entry1.summary = 'Google releases new AI model.'
            entry1.source = {'title': 'TechCrunch'}
            
            # 2. Sports article (Georgia Tech football)
            entry2 = MagicMock()
            entry2.title = 'Georgia Tech Wins Football Game'
            entry2.link = 'https://example.com/gatech'
            entry2.published_parsed = datetime.now(timezone.utc).timetuple()
            entry2.summary = 'The Yellow Jackets scored a touchdown in the final quarter.'
            entry2.source = {'title': 'ESPN'}
            
            # 3. Sports article (Virginia Tech basketball)
            entry3 = MagicMock()
            entry3.title = 'Virginia Tech Basketball Schedule'
            entry3.link = 'https://example.com/vatech'
            entry3.published_parsed = datetime.now(timezone.utc).timetuple()
            entry3.summary = 'The Hokies announce their 2026 season roster.'
            entry3.source = {'title': 'Sports Illustrated'}
            
            mock_feed.entries = [entry1, entry2, entry3]
            mock_parse.return_value = mock_feed

            # Execute
            result = fetch_google_news_rss('technology', 5, mock_tool_context)

            # Assert
            assert result['success'] is True
            
            # Should have only 1 article (the AI one)
            # The tool updates state['collected_articles'], and returns empty list in result['articles']
            # But it returns 'count' in the result dict
            assert result['count'] == 1
            
            collected = mock_tool_context.state['collected_articles']
            assert len(collected) == 1
            assert collected[0]['title'] == 'New AI Model Released'

    def test_fetch_google_news_all_topics(self, mock_tool_context):
        """Test that all valid topics work correctly."""
        valid_topics = ['politics', 'technology', 'europe']

        for topic in valid_topics:
            with patch('manis_agent.agents.collectors.google_news_collector.tools.feedparser.parse') as mock_parse:
                # Setup mock feed
                mock_feed = MagicMock()
                mock_feed.entries = []
                mock_parse.return_value = mock_feed

                # Execute
                result = fetch_google_news_rss(topic, 5, mock_tool_context)

                # Assert - should not fail validation
                assert 'error' not in result or 'Invalid topic' not in result.get('error', '')

    def test_fetch_google_news_sets_original_source_and_region(self, mock_tool_context):
        """Test that original_source is set and region matches Europe topic."""
        with patch('manis_agent.agents.collectors.google_news_collector.tools.feedparser.parse') as mock_parse:
            mock_feed = MagicMock()
            entry = MagicMock()
            entry.title = 'EU Parliament Debates AI Act - Reuters'
            entry.link = 'https://example.com/eu-ai'
            entry.published_parsed = datetime.now(timezone.utc).timetuple()
            entry.summary = 'EU lawmakers discuss AI regulation updates.'
            entry.source = {'title': 'Reuters'}
            mock_feed.entries = [entry]
            mock_parse.return_value = mock_feed

            result = fetch_google_news_rss('europe', 5, mock_tool_context)

            assert result['success'] is True
            collected = mock_tool_context.state.get('collected_articles', [])
            assert len(collected) == 1
            article = collected[0]
            assert article['original_source'] == 'Reuters'
            assert article['region'] == 'EU/International'
