import os
import sys

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
except ImportError:
    print("❌ Missing dependencies. Please run: pip install google-generativeai python-dotenv")
    sys.exit(1)

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key or "your_" in api_key:
    print("❌ GOOGLE_API_KEY is not set correctly in .env")
    sys.exit(1)

genai.configure(api_key=api_key)

print(f"Checking models for API key: {api_key[:10]}...")

try:
    available_models = genai.list_models()
    found = False
    for m in available_models:
        if 'embedContent' in m.supported_generation_methods:
            print(f"✅ Found Embedding Model: {m.name}")
            found = True
    if not found:
        print("❌ No embedding models found for this API key.")
except Exception as e:
    print(f"❌ Error listing models: {e}")
