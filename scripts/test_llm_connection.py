"""
scripts/test_llm_connection.py — one-time smoke test.

Run this AFTER you've created a .env file (from .env.example) with your real
GEMINI_API_KEY filled in. It sends one tiny message to Gemini and prints the
reply. If this works, RAG-03's real answer_query() function will work too —
this script exists purely to catch key/setup problems in isolation, before
they're buried inside the bigger RAG pipeline.

Usage (from repo root):
    python scripts/test_llm_connection.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root regardless of where this script is run from.
load_dotenv(Path(__file__).parent.parent / ".env")

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key or api_key == "your-key-here":
    print("ERROR: GEMINI_API_KEY is not set.")
    print("Did you copy .env.example to .env and paste your real key in?")
    sys.exit(1)

try:
    from google import genai
except ImportError:
    print("ERROR: the 'google-genai' package isn't installed.")
    print("Run: pip install -r requirements.txt  (with your venv active)")
    sys.exit(1)

client = genai.Client(api_key=api_key)

print("Sending a test message to Gemini...")
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Reply with exactly: 'Connection successful.'",
)

reply_text = response.text

print(f"\nGemini replied: {reply_text}")

if "successful" in reply_text.lower():
    print("\n✅ Connection works. You're ready to move on to RAG-03.")
else:
    print("\n⚠️  Got a reply, but it wasn't the expected one. Connection technically works though.")