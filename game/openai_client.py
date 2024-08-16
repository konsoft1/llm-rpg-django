from openai import OpenAI
import os
from dotenv import load_dotenv

# Initialize OpenAI client
load_dotenv()

api_key = os.environ.get('OPEN_AI_API_KEY')
if not api_key:
    raise RuntimeError("OPEN_AI_API_KEY is not set in the environment variable")
client = OpenAI(api_key=api_key)

# Default model to be used
DEFAULT_MODEL = "gpt-4o-mini"

def create_completion(messages, model=DEFAULT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        raise
