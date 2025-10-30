from google import genai
from google.genai import types
import json
import os
import base64
from dotenv import load_dotenv


def call_gemini_api(prompt: str):
    """
    Call Gemini API with text-only prompt.

    Args:
        prompt: Text prompt for the model

    Returns:
        Parsed JSON response from the model
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

        parsed = json.loads(response.text)
        return parsed

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {str(e)}")
        return {"status": "error", "reason": f"Invalid JSON response: {str(e)}"}
    except Exception as e:
        print(f"❌ API call failed: {str(e)}")
        return {"status": "error", "reason": str(e)}


def call_gemini_api_with_images(prompt: str, images: list):
    """
    Call Gemini API with multimodal input (text + images).

    Args:
        prompt: Text prompt providing context and instructions
        images: List of dictionaries with 'data' (base64), 'mime_type', and 'page' fields

    Returns:
        Parsed JSON response from the model
    """
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API key not found.")

    client = genai.Client(api_key=api_key)

    try:
        # Build multimodal content
        contents = []

        # Add instruction text first
        contents.append(prompt)

        # Add each page image with context
        for img in images:
            page_num = img.get("page", "unknown")
            print(f"📷 Adding page {page_num} image to analysis...")

            # Add page separator text
            contents.append(f"\n--- Page {page_num} ---\n")

            # Add the image as a blob part
            contents.append(
                types.Part.from_bytes(
                    data=base64.b64decode(img["data"]),
                    mime_type=img.get("mime_type", "image/png")
                )
            )

        print(f"🤖 Calling Gemini Vision API with {len(images)} images...")

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",  # Vision-capable model
            contents=contents,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.1  # Lower temperature for more consistent extraction
            }
        )

        parsed = json.loads(response.text)
        print(f"✓ Vision API analysis complete")
        return parsed

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {str(e)}")
        print(
            f"Raw response: {response.text if 'response' in locals() else 'No response'}")
        return {"status": "error", "reason": f"Invalid JSON response: {str(e)}"}
    except Exception as e:
        print(f"❌ Vision API call failed: {str(e)}")
        return {"status": "error", "reason": str(e)}
