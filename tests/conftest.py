"""Shared pytest fixtures for MANIS tests."""

import pytest
from unittest.mock import Mock
from datetime import datetime, timezone


@pytest.fixture
def mock_tool_context():
    """Create a mock ToolContext with state dictionary."""
    context = Mock()
    context.state = {}
    return context


@pytest.fixture
def sample_article():
    """Sample article data for testing."""
    return {
        'title': 'Test Article: Breaking News',
        'url': 'https://example.com/article/123',
        'source': 'Reuters',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'text': 'This is a test article about important news. It contains multiple sentences for testing.',
        'description': 'Test article description',
        'region': 'US',
        'category': 'politics'
    }


@pytest.fixture
def sample_articles(sample_article):
    """List of sample articles for testing."""
    return [
        sample_article,
        {
            **sample_article,
            'title': 'Second Test Article',
            'url': 'https://example.com/article/456',
            'source': 'NPR'
        },
        {
            **sample_article,
            'title': 'Third Test Article',
            'url': 'https://example.com/article/789',
            'source': 'CNN'
        }
    ]


@pytest.fixture
def preprocessed_article(sample_article):
    """Sample preprocessed article with entities and claims."""
    return {
        **sample_article,
        'clean_text': 'This is a test article about important news.',
        'entities': ['Reuters', 'Breaking News'],
        'claims': ['This is important news'],
        'word_count': 12
    }


@pytest.fixture
def fact_checked_article(preprocessed_article):
    """Sample fact-checked article with credibility scores."""
    return {
        **preprocessed_article,
        'credibility_score': 90,
        'bias_score': 1,
        'fact_accuracy_rating': 'very high',
        'credibility_notes': 'High credibility source'
    }


@pytest.fixture
def mock_rss_feed_data():
    """Mock RSS feed data structure."""
    return {
        'entries': [
            {
                'title': 'RSS Test Article 1',
                'link': 'https://news.example.com/1',
                'summary': 'First test article summary',
                'published_parsed': datetime.now(timezone.utc).timetuple(),
                'source': {'title': 'Test News Source'}
            },
            {
                'title': 'RSS Test Article 2',
                'link': 'https://news.example.com/2',
                'summary': 'Second test article summary',
                'published_parsed': datetime.now(timezone.utc).timetuple(),
                'source': {'title': 'Test News Source'}
            }
        ],
        'feed': {
            'title': 'Test RSS Feed',
            'link': 'https://news.example.com'
        }
    }
