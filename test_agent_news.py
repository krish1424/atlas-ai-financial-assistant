import asyncio

from app.ai.agent import AtlasAgent


async def main():
    print("Testing Atlas news integration...")

    agent = AtlasAgent()

    user_message = "What is the latest news about IBM?"

    response = await agent.process(
        user_message=user_message,
        conversation_history=[],
    )

    print("\n--- Atlas Response ---")
    print(response.message)

    print("\n--- Plan ---")
    print(f"Intent: {response.plan.intent.value}")
    print(f"Symbol: {response.plan.symbol}")
    print(
        f"Requires live data: "
        f"{response.plan.requires_live_data}"
    )
    print(
        f"Requires tool: "
        f"{response.plan.requires_tool}"
    )


if __name__ == "__main__":
    asyncio.run(main())