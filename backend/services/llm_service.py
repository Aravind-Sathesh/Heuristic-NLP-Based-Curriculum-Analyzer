from google import genai
import json
import os
from dotenv import load_dotenv


def call_gemini_api(prompt: str):
    """
    Calls the Gemini API with a given prompt and returns the parsed JSON response.
    Uses the new google-genai SDK (not the deprecated google.generativeai).
    """
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

        try:
            parsed = json.loads(response.text)
            return {"status": "success", "data": parsed}
        except json.JSONDecodeError as json_error:
            print(f"JSON parsing error: {json_error}")
            print(f"Raw response text for debugging: {response.text}")
            return {
                "status": "error",
                "reason": f"JSON parsing failed: {str(json_error)}",
                "raw_response": response.text
            }

    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return {"status": "error", "reason": str(e)}
