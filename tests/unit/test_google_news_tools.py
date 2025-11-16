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
            # Setup mock feed data
            mock_feed = MagicMock()
            mock_feed.entries = mock_rss_feed_data['entries']
            mock_parse.return_value = mock_feed

            # Execute
            result = fetch_google_news_rss('politics', 5, mock_tool_context)

            # Assert
            assert result['success'] is True
            assert 'articles' in result
            assert isinstance(result['articles'], list)
            assert len(result['articles']) > 0

            # Check article structure
            article = result['articles'][0]
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
            assert len(result['articles']) <= 5

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
