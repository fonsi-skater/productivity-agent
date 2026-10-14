
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from tools.agent_tools import PRODUCTIVITY_TOOLS

load_dotenv(override=True)

model = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL"),
    api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
    base_url="https://openrouter.ai/api/v1",
    timeout=45,
    max_retries=0,
)

try:
    model_with_tools = model.bind_tools(PRODUCTIVITY_TOOLS)

    response = model_with_tools.invoke(
        "Use the list_productivity_tasks tool to show all my tasks."
    )

    print("Model response received.")
    print("Content:", response.content)
    print("Tool calls:", response.tool_calls)

except Exception as error:
    print("Error type:", type(error).__name__)
    print("Error details:", str(error)[:1000])
