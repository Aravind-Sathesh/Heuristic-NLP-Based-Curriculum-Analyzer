# list_models.py
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


def list_available_models():
    """
    Lists all the models available to the configured API key and prints their details.
    """
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file.")

    try:
        print("Connecting to Google AI...\n")
        client = genai.Client(api_key=api_key)

        print("--- Available Models ---")
        # The list() method returns a pager, which can be iterated over
        for model in client.models.list():
            # The 'supported_actions' tells you what the model can do
            if 'generateContent' in model.supported_actions:
                print(f"Model Name: {model.name}")
                print(f"  Display Name: {model.display_name}")
                print(f"  Description: {model.description}")
                print(f"  Supported Actions: {model.supported_actions}")
                print("-" * 25)

    except Exception as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    list_available_models()
