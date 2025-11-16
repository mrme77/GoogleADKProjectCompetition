#!/usr/bin/env python3
"""
MANIS Pipeline Runner - Programmatic Execution
Runs the full MANIS pipeline using ADK Runner
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
env_file = Path(__file__).parent / "manis_agent" / ".env"
load_dotenv(env_file)
print(f"Loaded environment from: {env_file}")

from manis_agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


async def run_pipeline_async():
    """Execute the MANIS pipeline asynchronously"""
    print("=" * 80)
    print("Starting MANIS Pipeline")
    print("=" * 80)

    # Create session service
    session_service = InMemorySessionService()

    # Create session
    session = session_service.create_session(
        app_name="MANIS",
        user_id="automated",
        state={}
    )

    # Create runner
    runner = Runner(
        agent=root_agent,
        app_name="MANIS",
        session_service=session_service,
    )

    # Run the pipeline
    prompt = "Collect, analyze, and deliver today's news intelligence report"
    print(f"\nExecuting: {prompt}\n")

    # Create message content
    content = types.Content(role="user", parts=[types.Part(text=prompt)])

    # Run async and collect events
    async for event in runner.run_async(
        user_id="automated",
        session_id=session.id,
        new_message=content
    ):
        # Print event information
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    print(f"[{event.author}] {part.text}")

    print("\n" + "=" * 80)
    print("Pipeline Completed Successfully")
    print("=" * 80)

    return True


def main():
    """Main entry point"""
    try:
        asyncio.run(run_pipeline_async())
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Pipeline failed: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
