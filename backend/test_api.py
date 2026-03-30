import os
import sys

try:
    from dotenv import load_dotenv
    from langchain_openai import ChatOpenAI
except ImportError:
    print("❌ Missing dependencies. Please run: pip install python-dotenv langchain-openai")
    sys.exit(1)

load_dotenv()

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

if not openrouter_api_key or "your_" in openrouter_api_key:
    print("❌ OPENROUTER_API_KEY is not set correctly in .env")
    sys.exit(1)

print(f"Checking OpenRouter API for key: {openrouter_api_key[:10]}...")

try:
    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "google/gemini-2.0-flash-001"),
        api_key=openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    # Perform a quick completion to verify the key works
    response = llm.invoke("Hi")
    print("✅ Successfully connected to OpenRouter API and generated a response!")
    print(f"Response snippet: {response.content[:50]}")
except Exception as e:
    print(f"❌ Error connecting to OpenRouter API: {e}")

# Check Pinecone
pinecone_api_key = os.getenv("PINECONE_API_KEY")
if pinecone_api_key and "your_" not in pinecone_api_key:
    print(f"\n✅ Pinecone API key is set.")
    print(f"Target index: {os.getenv('PINECONE_INDEX_NAME', 'rag-chatbot-openrouter')}")
else:
    print("\n⚠️ PINECONE_API_KEY is NOT set correctly.")
