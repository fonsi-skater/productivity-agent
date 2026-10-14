
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler
from tools.agent_tools import PRODUCTIVITY_TOOLS

load_dotenv(override=True)


class DiagnosticHandler(BaseCallbackHandler):
    def on_chat_model_start(self, serialized, messages, **kwargs):
        print("\n[DIAGNOSTIC] Model call started.")

    def on_llm_error(self, error, **kwargs):
        print("\n[DIAGNOSTIC] Model error:", str(error)[:500])

    def on_tool_start(self, serialized, input_str, **kwargs):
        print("\n[DIAGNOSTIC] Tool started:", serialized.get("name", "unknown"))
        print("[DIAGNOSTIC] Tool input:", input_str)

    def on_tool_end(self, output, **kwargs):
        print("\n[DIAGNOSTIC] Tool finished.")
        print("[DIAGNOSTIC] Tool output:", str(output)[:500])

    def on_tool_error(self, error, **kwargs):
        print("\n[DIAGNOSTIC] Tool error:", str(error)[:500])

    def on_chain_error(self, error, **kwargs):
        print("\n[DIAGNOSTIC] Agent workflow error:", str(error)[:500])


model = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL"),
    api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
    base_url="https://openrouter.ai/api/v1",
    timeout=45,
    max_retries=0,
)

agent = create_agent(
    model=model,
    tools=PRODUCTIVITY_TOOLS,
    system_prompt=(
        "You are a personal productivity agent. "
        "Use the list_productivity_tasks tool when asked to list tasks. "
        "Report the tool result accurately."
    ),
)

try:
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Show me all my tasks."}]},
        config={"callbacks": [DiagnosticHandler()]},
    )

    print("\n[DIAGNOSTIC] Agent completed successfully.")
    print("Final response:", result["messages"][-1].content)

except Exception as error:
    print("\n[DIAGNOSTIC] Final exception:", type(error).__name__)
    print("[DIAGNOSTIC] Details:", str(error)[:1000])
