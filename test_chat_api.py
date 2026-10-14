
import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv(override=True)

key = os.getenv("OPENROUTER_API_KEY", "").strip()
model = os.getenv("OPENROUTER_MODEL", "openrouter/free")

payload = {
    "model": model,
    "messages": [
        {"role": "user", "content": "Reply with: Chat API works!"}
    ],
    "max_tokens": 50,
}

request = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=45) as response:
        data = json.loads(response.read().decode("utf-8"))
        print("HTTP status:", response.status)
        print("Model used:", data.get("model"))
        print("AI response:", data["choices"][0]["message"]["content"])
except urllib.error.HTTPError as error:
    print("HTTP status:", error.code)
    try:
        data = json.loads(error.read().decode("utf-8"))
        print("API error:", data.get("error", {}).get("message", "Unknown error"))
        print("Error code:", data.get("error", {}).get("code", "Not provided"))
    except Exception:
        print("OpenRouter returned an error response.")
except Exception as error:
    print("Error type:", type(error).__name__)
    print("Details:", str(error)[:250])
