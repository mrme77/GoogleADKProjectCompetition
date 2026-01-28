"""Email delivery agent using Gmail API."""

from google.adk.agents import Agent
from .tools import send_email_digest, test_email_connection


# Email delivery agent
delivery_agent = Agent(
    name="email_delivery",
    model="openrouter/google/gemini-2.5-flash-lite-preview-09-2025",
    description="Delivers daily news digest via Gmail",
    instruction="""
    You are an email delivery agent that sends the daily news digest.

    IMMEDIATELY do the following (do NOT just plan - EXECUTE):

    Step 1: Call send_email_digest tool to send the digest (no parameters needed)
    Step 2: Report the results

    You MUST call the send_email_digest tool. Do not skip this step.

    The recipient email(s) are automatically read from the RECIPIENT_EMAIL environment variable.
    Multiple recipients are supported (comma-separated in config).

    After calling the tool, report:
    - Confirmation of successful delivery (from tool response)
    - Recipient email addresses (from tool response)
    - Number of recipients (from tool response)
    - Timestamp (from tool response)

    If delivery fails, report the error clearly and suggest next steps.

    CRITICAL: Use the actual data returned by the tool. Do not make up or infer values.

    Keep your response concise.
    """,
    tools=[send_email_digest, test_email_connection],
    output_key="delivery_status"
)
