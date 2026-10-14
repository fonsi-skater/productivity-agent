
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load settings from the .env file
load_dotenv()

# Configure the AI model through OpenRouter
model = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# Send a test message to the AI
response = model.invoke("Reply with: Connection successful!")

# Display the AI's response
print("AI response:", response.content)
