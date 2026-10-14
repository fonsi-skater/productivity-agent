
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(override=True)

try:
    model = ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL"),
        api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
        base_url="https://openrouter.ai/api/v1",
        timeout=30,
        max_retries=0,
    )

    response = model.invoke("Reply with: Connection successful!")
    print("SUCCESS:", response.content)

except Exception as e:
    print("ERROR TYPE:", type(e).__name__)
    print("ERROR MESSAGE:", str(e))

    cause = e.__cause__
    while cause:
        print("UNDERLYING TYPE:", type(cause).__name__)
        print("UNDERLYING MESSAGE:", str(cause))
        cause = cause.__cause__
