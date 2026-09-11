import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

print("Available models:")
for m in client.models.list():
    if "generateContent" in m.supported_actions:
        print(f"- {m.name}")
