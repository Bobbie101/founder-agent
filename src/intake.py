import uuid
import os
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agent import root_agent
from mongo_tools import save_founder_profile, save_market_research

load_dotenv()

async def run_intake():
    print("\n🚀 Welcome to the First-Time Founder Agent\n")
    print("I'm here to help you go from idea to investor-ready.\n")

    # Collect founder info
    idea = input("Describe your business idea: ").strip()
    industry = input("What industry is this? (e.g. SaaS, HealthTech, EdTech): ").strip()
    country = input("What country are you based in? ").strip()

    founder_id = str(uuid.uuid4())[:8]

    # Save intake to MongoDB
    save_founder_profile(founder_id, idea, industry, country)
    print(f"\n✅ Profile saved. Your founder ID: {founder_id}\n")

    # Set up ADK runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="founder_agent",
        session_service=session_service
    )

    session = await session_service.create_session(
        app_name="founder_agent",
        user_id=founder_id
    )

    # Step 1 — Idea clarity
    print("🧠 Analyzing your idea...\n")
    intake_prompt = f"""
A first-time founder just described their idea. 
Idea: {idea}
Industry: {industry}
Country: {country}

Help them clarify:
1. What problem does it solve?
2. Who is the target customer?
3. Why is now the right time?

Be direct and encouraging. Ask one follow-up question if something critical is missing.
"""

    async for event in runner.run_async(
        user_id=founder_id,
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=intake_prompt)])
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                print(event.content.parts[0].text)

    # Step 2 — Market validation
    print("\n🔍 Searching for real market data...\n")
    market_prompt = f"""
Now do a market validation for this idea: {idea} in the {industry} industry.

Search for:
1. Real market size numbers
2. Top 3 existing competitors
3. Key trends for or against this idea

End with an honest verdict: Strong / Needs Adjusting / Crowded Market.
Never make up statistics — search first.
"""

    market_summary = ""
    async for event in runner.run_async(
        user_id=founder_id,
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=market_prompt)])
    ):
        if event.is_final_response():
            market_summary = event.content.parts[0].text if event.content and event.content.parts else ""
            print(market_summary)

    # Save market research to MongoDB
    save_market_research(founder_id, market_summary)
    print("\n✅ Market research saved to MongoDB.")
    print(f"\n📌 Your founder ID is: {founder_id} — save this to resume later.\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_intake())
