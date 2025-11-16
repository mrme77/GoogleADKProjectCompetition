#!/usr/bin/env python3
"""Quick test to see what's in session state after pipeline runs"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

# Load env
env_file = Path(__file__).parent / "manis_agent" / ".env"
load_dotenv(env_file)

from manis_agent.agent import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


async def main():
    session_service = InMemorySessionService()

    session = session_service.create_session(
        app_name="MANIS",
        user_id="automated",
        state={}
    )

    runner = Runner(
        agent=root_agent,
        app_name="MANIS",
        session_service=session_service,
    )

    prompt = "Collect, analyze, and deliver today's news intelligence report"
    content = types.Content(role="user", parts=[types.Part(text=prompt)])

    async for event in runner.run_async(
        user_id="automated",
        session_id=session.id,
        new_message=content
    ):
        pass  # Just consume events

    # Now check state
    final_session = session_service.get_session(
        app_name="MANIS",
        user_id="automated",
        session_id=session.id
    )

    print("\n" + "="*80)
    print("FINAL SESSION STATE KEYS:")
    print("="*80)
    for key in final_session.state.keys():
        value = final_session.state[key]
        if isinstance(value, str) and len(value) > 200:
            print(f"{key}: {value[:200]}... (truncated, total length: {len(value)})")
        else:
            print(f"{key}: {value}")

    print("\n" + "="*80)
    print("CHECKING FOR DAILY_DIGEST:")
    print("="*80)
    digest = final_session.state.get('daily_digest')
    if digest:
        print(f"✓ Found digest! Length: {len(digest)} characters")
        print(f"First 500 chars:\n{digest[:500]}")
    else:
        print("✗ No digest found in state!")


if __name__ == "__main__":
    asyncio.run(main())
