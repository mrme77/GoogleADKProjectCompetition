"""Email delivery tools using Gmail SMTP or Gmail API."""

import os
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from google.adk.tools.tool_context import ToolContext
from datetime import datetime

# Gmail API imports
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def send_email_digest(
    tool_context: ToolContext
) -> Dict:
    """
    Send the daily news digest via Gmail SMTP (app password) or Gmail API.

    Tries SMTP first if GMAIL_APP_PASSWORD is set in environment,
    otherwise falls back to Gmail API OAuth. The recipient email is read
    from the RECIPIENT_EMAIL environment variable.

    Args:
        tool_context: ADK tool context with daily_digest in state

    Returns:
        Dictionary with send status
    """
    # Get recipient email from environment
    recipient_email = os.getenv('RECIPIENT_EMAIL')

    if not recipient_email:
        return {
            'success': False,
            'error': 'RECIPIENT_EMAIL not set in environment.'
        }

    # Get daily digest from state
    digest_html = tool_context.state.get('daily_digest', '')

    if not digest_html:
        return {
            'success': False,
            'error': 'No daily digest found in state. Run summarizer first.'
        }

    # Clean up any markdown code fences that might have slipped through
    digest_html = digest_html.strip()
    if digest_html.startswith('```html'):
        digest_html = digest_html[7:]  # Remove ```html
    if digest_html.startswith('```'):
        digest_html = digest_html[3:]  # Remove ```
    if digest_html.endswith('```'):
        digest_html = digest_html[:-3]  # Remove trailing ```
    digest_html = digest_html.strip()

    # Check if SMTP credentials are available (preferred method)
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    gmail_address = os.getenv('GMAIL_ADDRESS')

    if gmail_password and gmail_address:
        # Use SMTP with app password (simpler)
        return send_via_smtp(
            gmail_address=gmail_address,
            gmail_password=gmail_password,
            recipient_email=recipient_email,
            digest_html=digest_html,
            tool_context=tool_context
        )
    else:
        # Fall back to Gmail API OAuth
        return send_via_gmail_api(
            recipient_email=recipient_email,
            digest_html=digest_html,
            tool_context=tool_context
        )


def send_via_smtp(
    gmail_address: str,
    gmail_password: str,
    recipient_email: str,
    digest_html: str,
    tool_context: ToolContext
) -> Dict:
    """
    Send email via Gmail SMTP using app password.

    Args:
        gmail_address: Gmail sender address
        gmail_password: Gmail app password
        recipient_email: Recipient email address
        digest_html: HTML content for email
        tool_context: ADK tool context

    Returns:
        Dictionary with send status
    """
    try:
        # Create email message
        message = MIMEMultipart('alternative')
        message['From'] = gmail_address
        message['To'] = recipient_email
        message['Subject'] = f"MANIS Daily News Digest - {datetime.now().strftime('%B %d, %Y')}"

        # Add HTML body
        html_part = MIMEText(digest_html, 'html')
        message.attach(html_part)

        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_address, gmail_password)
            server.send_message(message)

        # Store delivery confirmation
        tool_context.state['email_sent'] = True
        tool_context.state['email_method'] = 'smtp'

        return {
            'success': True,
            'method': 'smtp',
            'recipient': recipient_email,
            'sent_at': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to send email via SMTP: {str(e)}'
        }


def send_via_gmail_api(
    recipient_email: str,
    digest_html: str,
    tool_context: ToolContext
) -> Dict:
    """
    Send email via Gmail API with OAuth (fallback method).

    Args:
        recipient_email: Email address to send digest to
        digest_html: HTML content for email
        tool_context: ADK tool context

    Returns:
        Dictionary with send status
    """
    if not GMAIL_AVAILABLE:
        return {
            'success': False,
            'error': 'Gmail API libraries not installed. Use SMTP method instead or install: pip install google-api-python-client google-auth-oauthlib'
        }

    try:
        # Authenticate with Gmail API
        creds = authenticate_gmail()

        if not creds:
            return {
                'success': False,
                'error': 'Gmail authentication failed. Run Gmail OAuth setup first, or use SMTP method with app password.'
            }

        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)

        # Create email message
        message = create_email_message(
            recipient=recipient_email,
            subject=f"MANIS Daily News Digest - {datetime.now().strftime('%B %d, %Y')}",
            html_body=digest_html
        )

        # Send email
        result = service.users().messages().send(
            userId='me',
            body=message
        ).execute()

        # Store delivery confirmation
        tool_context.state['email_sent'] = True
        tool_context.state['email_message_id'] = result.get('id')
        tool_context.state['email_method'] = 'gmail_api'

        return {
            'success': True,
            'method': 'gmail_api',
            'message_id': result.get('id'),
            'recipient': recipient_email,
            'sent_at': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to send email via Gmail API: {str(e)}'
        }


def authenticate_gmail():
    """
    Authenticate with Gmail API using OAuth.

    Looks for token.json for existing credentials.
    If not found, initiates OAuth flow using credentials.json.

    Returns:
        Credentials object or None if authentication fails
    """
    creds = None

    # Token file stores user's access and refresh tokens
    token_path = os.path.join(os.path.dirname(__file__), 'token.json')
    credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')

    # Check if token.json exists
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                print(f"\n⚠️  Gmail credentials.json not found at: {credentials_path}")
                print("Please download OAuth credentials from Google Cloud Console")
                print("See README.md for Gmail API setup instructions\n")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return creds


def create_email_message(recipient: str, subject: str, html_body: str) -> Dict:
    """
    Create a properly formatted email message for Gmail API.

    Args:
        recipient: Recipient email address
        subject: Email subject line
        html_body: HTML content for email body

    Returns:
        Dictionary formatted for Gmail API
    """
    message = MIMEMultipart('alternative')
    message['to'] = recipient
    message['subject'] = subject

    # Add HTML body
    html_part = MIMEText(html_body, 'html')
    message.attach(html_part)

    # Encode message
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    return {'raw': raw_message}


def test_email_connection(tool_context: ToolContext) -> Dict:
    """
    Test email connection (SMTP or Gmail API).

    Args:
        tool_context: ADK tool context

    Returns:
        Dictionary with connection test results
    """
    # Check for SMTP credentials first
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    gmail_address = os.getenv('GMAIL_ADDRESS')

    if gmail_password and gmail_address:
        # Test SMTP connection
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(gmail_address, gmail_password)

            return {
                'success': True,
                'method': 'smtp',
                'email_address': gmail_address,
                'connection_status': 'connected'
            }

        except Exception as e:
            return {
                'success': False,
                'method': 'smtp',
                'error': f'SMTP connection failed: {str(e)}'
            }

    # Fall back to Gmail API test
    if not GMAIL_AVAILABLE:
        return {
            'success': False,
            'error': 'No email configuration found. Set GMAIL_APP_PASSWORD in .env or install Gmail API libraries.'
        }

    try:
        creds = authenticate_gmail()

        if not creds:
            return {
                'success': False,
                'error': 'Authentication failed'
            }

        service = build('gmail', 'v1', credentials=creds)

        # Test API connection by getting user profile
        profile = service.users().getProfile(userId='me').execute()

        return {
            'success': True,
            'method': 'gmail_api',
            'email_address': profile.get('emailAddress'),
            'messages_total': profile.get('messagesTotal'),
            'connection_status': 'connected'
        }

    except Exception as e:
        return {
            'success': False,
            'method': 'gmail_api',
            'error': f'Connection test failed: {str(e)}'
        }
