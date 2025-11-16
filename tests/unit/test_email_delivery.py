"""Unit tests for email delivery tools."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from manis_agent.agents.delivery.tools import send_email_digest, send_via_smtp


class TestSendEmailDigest:
    """Tests for send_email_digest function."""

    def test_send_email_missing_recipient(self, mock_tool_context):
        """Test that missing RECIPIENT_EMAIL returns error."""
        # Setup
        mock_tool_context.state['daily_digest'] = '<html><body>Test digest</body></html>'

        with patch.dict(os.environ, {}, clear=True):
            # Execute
            result = send_email_digest(mock_tool_context)

            # Assert
            assert result['success'] is False
            assert 'error' in result
            assert 'RECIPIENT_EMAIL' in result['error']

    def test_send_email_missing_digest(self, mock_tool_context):
        """Test that missing daily_digest returns error."""
        # Setup - no digest in state
        mock_tool_context.state = {}

        with patch.dict(os.environ, {'RECIPIENT_EMAIL': 'test@example.com'}):
            # Execute
            result = send_email_digest(mock_tool_context)

            # Assert
            assert result['success'] is False
            assert 'error' in result
            assert 'No daily digest' in result['error']

    def test_send_email_success_via_smtp(self, mock_tool_context):
        """Test successful email send via SMTP."""
        # Setup
        mock_tool_context.state['daily_digest'] = '<html><body>Test digest</body></html>'

        env_vars = {
            'RECIPIENT_EMAIL': 'recipient@example.com',
            'GMAIL_ADDRESS': 'sender@gmail.com',
            'GMAIL_APP_PASSWORD': 'test password'
        }

        with patch.dict(os.environ, env_vars):
            with patch('manis_agent.agents.delivery.tools.send_via_smtp') as mock_smtp:
                # Mock successful send
                mock_smtp.return_value = {
                    'success': True,
                    'method': 'smtp',
                    'recipient': 'recipient@example.com'
                }

                # Execute
                result = send_email_digest(mock_tool_context)

                # Assert
                assert result['success'] is True
                assert result['method'] == 'smtp'
                mock_smtp.assert_called_once()

    def test_send_email_cleans_markdown_fences(self, mock_tool_context):
        """Test that markdown code fences are removed from digest."""
        # Setup - digest with markdown fences
        mock_tool_context.state['daily_digest'] = '```html\n<html><body>Test</body></html>\n```'

        env_vars = {
            'RECIPIENT_EMAIL': 'recipient@example.com',
            'GMAIL_ADDRESS': 'sender@gmail.com',
            'GMAIL_APP_PASSWORD': 'test password'
        }

        with patch.dict(os.environ, env_vars):
            with patch('manis_agent.agents.delivery.tools.send_via_smtp') as mock_smtp:
                mock_smtp.return_value = {'success': True}

                # Execute
                send_email_digest(mock_tool_context)

                # Assert - check that cleaned HTML was passed
                call_args = mock_smtp.call_args
                digest_arg = call_args.kwargs['digest_html']
                assert '```' not in digest_arg
                assert '<html>' in digest_arg

    def test_send_email_fallback_to_api(self, mock_tool_context):
        """Test fallback to Gmail API when SMTP credentials missing."""
        # Setup
        mock_tool_context.state['daily_digest'] = '<html><body>Test digest</body></html>'

        # Only RECIPIENT_EMAIL, no SMTP credentials
        with patch.dict(os.environ, {'RECIPIENT_EMAIL': 'test@example.com'}, clear=True):
            with patch('manis_agent.agents.delivery.tools.send_via_gmail_api') as mock_api:
                mock_api.return_value = {'success': True, 'method': 'gmail_api'}

                # Execute
                result = send_email_digest(mock_tool_context)

                # Assert - should use Gmail API
                mock_api.assert_called_once()


class TestSendViaSMTP:
    """Tests for send_via_smtp function."""

    def test_smtp_send_success(self, mock_tool_context):
        """Test successful SMTP email send."""
        # Setup
        digest_html = '<html><body>Test digest</body></html>'

        with patch('manis_agent.agents.delivery.tools.smtplib.SMTP_SSL') as mock_smtp:
            # Mock SMTP server
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Execute
            result = send_via_smtp(
                gmail_address='sender@gmail.com',
                gmail_password='test_password',
                recipient_email='recipient@example.com',
                digest_html=digest_html,
                tool_context=mock_tool_context
            )

            # Assert
            assert result['success'] is True
            assert result['method'] == 'smtp'
            assert 'recipient' in result

            # Verify SMTP methods called
            mock_server.login.assert_called_once_with('sender@gmail.com', 'test_password')
            mock_server.send_message.assert_called_once()

    def test_smtp_send_handles_authentication_error(self, mock_tool_context):
        """Test SMTP authentication error handling."""
        # Setup
        digest_html = '<html><body>Test digest</body></html>'

        with patch('manis_agent.agents.delivery.tools.smtplib.SMTP_SSL') as mock_smtp:
            # Mock authentication error
            mock_server = MagicMock()
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Execute
            result = send_via_smtp(
                gmail_address='sender@gmail.com',
                gmail_password='wrong_password',
                recipient_email='recipient@example.com',
                digest_html=digest_html,
                tool_context=mock_tool_context
            )

            # Assert
            assert result['success'] is False
            assert 'error' in result
            assert 'Authentication' in result['error'] or 'SMTP' in result['error']

    def test_smtp_send_updates_state(self, mock_tool_context):
        """Test that state is updated after successful send."""
        # Setup
        digest_html = '<html><body>Test digest</body></html>'

        with patch('manis_agent.agents.delivery.tools.smtplib.SMTP_SSL') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Execute
            result = send_via_smtp(
                gmail_address='sender@gmail.com',
                gmail_password='test_password',
                recipient_email='recipient@example.com',
                digest_html=digest_html,
                tool_context=mock_tool_context
            )

            # Assert - state should be updated
            assert mock_tool_context.state.get('email_sent') is True
            assert 'delivery_status' in mock_tool_context.state

    def test_smtp_message_structure(self, mock_tool_context):
        """Test that email message is properly structured."""
        # Setup
        digest_html = '<html><body>Test digest</body></html>'

        with patch('manis_agent.agents.delivery.tools.smtplib.SMTP_SSL') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            # Execute
            send_via_smtp(
                gmail_address='sender@gmail.com',
                gmail_password='test_password',
                recipient_email='recipient@example.com',
                digest_html=digest_html,
                tool_context=mock_tool_context
            )

            # Assert - verify message was sent
            assert mock_server.send_message.called
            sent_message = mock_server.send_message.call_args[0][0]

            # Check message headers
            assert sent_message['From'] == 'sender@gmail.com'
            assert sent_message['To'] == 'recipient@example.com'
            assert 'Subject' in sent_message
            assert 'MANIS' in sent_message['Subject']
