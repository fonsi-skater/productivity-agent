
import os
import asyncio
from contextlib import AsyncExitStack
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.mcp import MCPAdapter
from tools.calendar_tools import create_calendar_event

from tools.agent_tools import PRODUCTIVITY_TOOLS
from tools.event_link_tools import inspect_event_link


# Load environment variables from the project's .env file.
load_dotenv(override=True)


def create_model():
    """Create the ChatOpenAI model using OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is missing. "
            "Check that it is defined in your .env file."
        )

    model_name = os.getenv(
        "OPENROUTER_MODEL",
        "openai/gpt-4o-mini",
    )

    return ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
    )


def get_message_text(content):
    """Convert a model response into printable text."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, dict):
                text_value = item.get("text")
                if text_value:
                    parts.append(text_value)
            else:
                text_value = getattr(item, "text", None)
                if text_value:
                    parts.append(text_value)

        if parts:
            return "\n".join(parts)

    return str(content)


async def main():
    """Load tools and run the interactive productivity agent."""
    project_dir = Path(__file__).resolve().parent

    server_paths = [
        project_dir / "mcp_servers" / "hello_server.py",
        project_dir / "mcp_servers" / "report_server.py",
    ]

    # Fail early with a clear message if an MCP server is missing.
    for server_path in server_paths:
        if not server_path.is_file():
            raise FileNotFoundError(
                f"MCP server file not found: {server_path}"
            )

    print("Starting Personal Productivity Agent...")

    async with AsyncExitStack() as stack:
        # Keep the productivity tools already in your project.
        all_tools = list(PRODUCTIVITY_TOOLS)

       
        # Register additional tools without adding duplicates.
        for extra_tool in (
            inspect_event_link,
            create_calendar_event,
        ):
            if not any(
                getattr(tool, "name", None) == extra_tool.name
                for tool in all_tools
            ):
                all_tools.append(extra_tool)

        # Connect to the existing MCP servers and load their tools.
        for server_path in server_paths:
            adapter = await stack.enter_async_context(
                MCPAdapter(server_path)
            )

            server_tools = await adapter.list_tools()
            all_tools.extend(server_tools)

            print(f"\nMCP tools loaded from {server_path.name}:")
            for tool in server_tools:
                print(f"- {tool.name}")

        print("\nAvailable tools:")
        for tool in all_tools:
            print(f"- {getattr(tool, 'name', str(tool))}")

        # Create the agent with all registered tools.
        agent = create_agent(
            model=create_model(),
            tools=all_tools,
            system_prompt=(
                "You are a personal productivity agent. "
                "Help the user organize tasks, inspect event links, "
                "and create reports using the available tools. "

                "Use list_productivity_tasks when asked to list tasks. "
                "Use inspect_event_link to inspect event URLs rather "
                "than guessing event details. Summarize the event name, "
                "date, time and timezone, attendance mode, and price "
                "when those details are available. "

                "Use the available MCP report tool when the user asks "
                "to create a Markdown report. Preserve factual accuracy "
                "and clearly identify information that is unavailable. "

                "Never claim that an email was sent, an RSVP was completed, "
                "a calendar event was created, or a reminder was scheduled "
                "unless an available tool actually performed and confirmed "
                "that action. Event-page inspection alone does not register "
                "the user for an event. "
            ),
        )

        print("\nAgent is ready.")
        print("Enter a request, or type 'exit' to quit.")

        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting agent.")
                break

            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit", "q"}:
                print("Goodbye!")
                break

            try:
                result = await agent.ainvoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": user_input,
                            }
                        ]
                    }
                )

                messages = result.get("messages", [])
                final_content = None

                # Find the latest assistant/model message.
                for message in reversed(messages):
                    if isinstance(message, dict):
                        message_type = message.get(
                            "role",
                            message.get("type", ""),
                        )
                        content = message.get("content", "")
                    else:
                        message_type = getattr(message, "type", "")
                        content = getattr(message, "content", "")

                    if message_type in {"ai", "assistant"} and content:
                        final_content = content
                        break

                if final_content is not None:
                    print(
                        "\nAgent:\n"
                        + get_message_text(final_content)
                    )
                else:
                    print(
                        "\nThe agent returned no printable response. "
                        "Please try again."
                    )

            except Exception as exc:
                print(
                    "\nRequest failed. Check the error below and try again:"
                )
                print(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAgent stopped.")
    except Exception as exc:
        print(f"\nAgent could not start: {type(exc).__name__}: {exc}")
