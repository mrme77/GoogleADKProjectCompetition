"""Unit tests for fact checker credibility scoring tools."""

import pytest
from unittest.mock import Mock
from manis_agent.agents.fact_checker.tools import (
    score_article_credibility,
    flag_dubious_claims,
    SOURCE_CREDIBILITY
)


class TestScoreArticleCredibility:
    """Tests for score_article_credibility function."""

    def test_score_known_source_reuters(self, mock_tool_context, preprocessed_article):
        """Test that Reuters gets correct high credibility score."""
        # Setup
        preprocessed_article['source'] = 'Reuters'
        mock_tool_context.state['preprocessed_articles'] = [preprocessed_article]

        # Execute
        result = score_article_credibility(mock_tool_context)

        # Assert
        assert result['success'] is True
        assert result['scored_count'] == 1
        assert 'credibility_stats' in result

        # Check Reuters score
        scored_article = mock_tool_context.state['fact_checked_articles'][0]
        assert scored_article['credibility_score'] == 90
        assert scored_article['bias_score'] == 1
        assert scored_article['fact_accuracy_rating'] == 'very high'

    def test_score_known_source_nyt(self, mock_tool_context, preprocessed_article):
        """Test that NYT gets correct medium-high credibility score."""
        # Setup
        preprocessed_article['source'] = 'The New York Times'
        mock_tool_context.state['preprocessed_articles'] = [preprocessed_article]

        # Execute
        result = score_article_credibility(mock_tool_context)

        # Assert
        scored_article = mock_tool_context.state['fact_checked_articles'][0]
        assert scored_article['credibility_score'] == 78
        assert scored_article['bias_score'] == 4

    def test_score_unknown_source_defaults(self, mock_tool_context, preprocessed_article):
        """Test that unknown sources get default score of 60."""
        # Setup
        preprocessed_article['source'] = 'Random Unknown Blog'
        mock_tool_context.state['preprocessed_articles'] = [preprocessed_article]

        # Execute
        result = score_article_credibility(mock_tool_context)

        # Assert
        scored_article = mock_tool_context.state['fact_checked_articles'][0]
        assert scored_article['credibility_score'] == 60
        assert scored_article['bias_score'] == 5
        assert scored_article['fact_accuracy_rating'] == 'unknown'

    def test_credibility_stats_calculation(self, mock_tool_context, sample_articles):
        """Test that credibility stats are calculated correctly."""
        # Setup - mix of high, medium, and low credibility sources
        articles = [
            {**sample_articles[0], 'source': 'Reuters'},      # High (90)
            {**sample_articles[1], 'source': 'NPR'},          # High (85)
            {**sample_articles[2], 'source': 'CNN'},          # Medium (72)
        ]
        mock_tool_context.state['preprocessed_articles'] = articles

        # Execute
        result = score_article_credibility(mock_tool_context)

        # Assert
        assert result['success'] is True
        assert result['scored_count'] == 3
        assert result['credibility_stats']['high_credibility'] == 2  # Reuters, NPR
        assert result['credibility_stats']['medium_credibility'] == 1  # CNN
        assert result['credibility_stats']['low_credibility'] == 0

    def test_average_scores_calculated(self, mock_tool_context, sample_articles):
        """Test that average credibility and bias scores are calculated."""
        # Setup
        articles = [
            {**sample_articles[0], 'source': 'Reuters'},  # 90, bias 1
            {**sample_articles[1], 'source': 'BBC'},      # 88, bias 2
        ]
        mock_tool_context.state['preprocessed_articles'] = articles

        # Execute
        result = score_article_credibility(mock_tool_context)

        # Assert
        assert 'avg_credibility' in result
        assert 'avg_bias' in result
        assert result['avg_credibility'] == 89.0  # (90 + 88) / 2
        assert result['avg_bias'] == 1.5  # (1 + 2) / 2

    def test_no_preprocessed_articles_error(self, mock_tool_context):
        """Test that missing preprocessed articles returns error."""
        # Setup - empty state
        mock_tool_context.state = {}

        # Execute
        result = score_article_credibility(mock_tool_context)

        # Assert
        assert result['success'] is False
        assert 'error' in result
        assert 'No preprocessed articles' in result['error']

    def test_state_updated_correctly(self, mock_tool_context, preprocessed_article):
        """Test that state is updated with scored articles."""
        # Setup
        mock_tool_context.state['preprocessed_articles'] = [preprocessed_article]

        # Execute
        result = score_article_credibility(mock_tool_context)

        # Assert
        assert 'fact_checked_articles' in mock_tool_context.state
        assert 'credibility_stats' in mock_tool_context.state
        assert len(mock_tool_context.state['fact_checked_articles']) == 1

    def test_all_credibility_database_sources(self, mock_tool_context, preprocessed_article):
        """Test that all sources in credibility database are handled."""
        # Test a few key sources
        test_sources = ['Reuters', 'AP', 'BBC', 'NPR', 'CNN', 'Fox News', 'The Guardian']

        for source in test_sources:
            if source not in SOURCE_CREDIBILITY:
                continue  # Skip if not in database

            preprocessed_article['source'] = source
            mock_tool_context.state['preprocessed_articles'] = [preprocessed_article]

            result = score_article_credibility(mock_tool_context)

            assert result['success'] is True
            scored_article = mock_tool_context.state['fact_checked_articles'][0]
            assert scored_article['credibility_score'] > 0
            assert scored_article['bias_score'] > 0


class TestFlagDubiousClaims:
    """Tests for flag_dubious_claims function."""

    def test_flag_claims_with_verification_keywords(self, mock_tool_context, fact_checked_article):
        """Test that claims with verification keywords are flagged."""
        # Setup
        fact_checked_article['claims'] = [
            'This is allegedly a major development',
            'Sources say the situation is critical'
        ]
        mock_tool_context.state['fact_checked_articles'] = [fact_checked_article]

        # Execute
        result = flag_dubious_claims(mock_tool_context)

        # Assert
        assert result['success'] is True
        assert result['flagged_count'] > 0
        flagged = mock_tool_context.state['flagged_claims']
        assert len(flagged) > 0
        assert any('allegedly' in f['claim'].lower() for f in flagged)

    def test_no_fact_checked_articles_error(self, mock_tool_context):
        """Test that missing fact-checked articles returns error."""
        # Setup
        mock_tool_context.state = {}

        # Execute
        result = flag_dubious_claims(mock_tool_context)

        # Assert
        assert result['success'] is False
        assert 'error' in result

    def test_claims_without_keywords_not_flagged(self, mock_tool_context, fact_checked_article):
        """Test that normal claims without keywords are not flagged unnecessarily."""
        # Setup with high credibility and no verification keywords
        fact_checked_article['claims'] = ['This is a factual statement']
        fact_checked_article['bias_score'] = 1  # Low bias
        mock_tool_context.state['fact_checked_articles'] = [fact_checked_article]

        # Execute
        result = flag_dubious_claims(mock_tool_context)

        # Assert - should have low or zero flagged claims
        assert result['success'] is True
        assert result['flagged_count'] == 0
