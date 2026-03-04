from openai import OpenAI
from dotenv import load_dotenv
import os

# Load .env
dotenv_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(dotenv_path)

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"  # required for Groq
)

def call_groq(prompt: str, model: str = "openai/gpt-oss-20b") -> str:
    response = client.responses.create(
        input=prompt,
        model=model,
    )
    return response.output_text