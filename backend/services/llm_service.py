from google import genai
import json
import os
from dotenv import load_dotenv


def call_gemini_api(prompt: str):
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API key not found.")

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        parsed = json.loads(response.text)
        return parsed

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {str(e)}")
        return {"status": "error", "reason": f"Invalid JSON response: {str(e)}"}
    except Exception as e:
        print(f"❌ API call failed: {str(e)}")
        return {"status": "error", "reason": str(e)}
