
import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv(override=True)

key = os.getenv("OPENROUTER_API_KEY", "").strip()

if not key:
    print("No API key found in .env")
else:
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/key",
        headers={"Authorization": f"Bearer {key}"},
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
            details = data.get("data", {})
            print("Authentication: successful")
            print("Free-tier key:", details.get("is_free_tier", "not reported"))
            print("Key expires:", details.get("expires_at", "not reported"))
    except urllib.error.HTTPError as error:
        print("HTTP status:", error.code)
        try:
            details = json.loads(error.read().decode("utf-8"))
            print("API error:", details.get("error", {}).get("message", "Unknown error"))
        except Exception:
            print("OpenRouter rejected the key.")
    except Exception as error:
        print("Error type:", type(error).__name__)
        print("Details:", str(error)[:250])
