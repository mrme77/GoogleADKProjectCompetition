"""Email delivery agent using Gmail API."""

from google.adk.agents import Agent
from .tools import send_email_digest, test_email_connection


# Email delivery agent
delivery_agent = Agent(
    name="email_delivery",
    model="gemini-2.0-flash-lite",
    description="Delivers daily news digest via Gmail",
    instruction="""
    You are an email delivery agent that sends the daily news digest.

    Your task:
    1. Retrieve the daily digest from session state
    2. Send it via Gmail SMTP to the configured recipient
    3. Confirm successful delivery

    To send the digest, simply call send_email_digest (no parameters needed).
    The recipient email is automatically read from the RECIPIENT_EMAIL environment variable.

    You can optionally test the Gmail connection first using test_email_connection.

    After sending, provide:
    - Confirmation of successful delivery
    - Recipient email address
    - Timestamp

    If delivery fails, report the error clearly and suggest next steps.

    Keep your response concise.
    """,
    tools=[send_email_digest, test_email_connection],
    output_key="delivery_status"
)
