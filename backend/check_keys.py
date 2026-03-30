import os
import sys
import asyncio
from app.config import settings

def mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "Not found or too short"
    return f"{key[:6]}...{key[-2:]}"

async def test_openrouter():
    print("\n--- 1. KIỂM TRA BIẾN MÔI TRƯỜNG ---")
    
    # Path info
    current_dir = os.getcwd()
    print(f"Thư mục hiện tại (CWD): {current_dir}")
    
    # Check Settings object
    print(f"OpenRouter API Key: {mask_key(settings.openrouter_api_key)}")
    print(f"LLM Model: {settings.llm_model}")
    print(f"Pinecone Index: {settings.pinecone_index_name}")

    print("\n--- 2. THỬ KẾT NỐI OPENROUTER (Gửi câu hỏi 'Hi') ---")
    import httpx
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "RAG Chatbot Debug",
        "Content-Type": "application/json"
    }
    data = {
        "model": settings.llm_model,
        "messages": [{"role": "user", "content": "Hi"}]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, timeout=10.0)
            
            if response.status_code == 200:
                print("✅ KẾT QUỐI THÀNH CÔNG!")
                result = response.json()
                print(f"AI Phản hồi: {result['choices'][0]['message']['content']}")
            else:
                print(f"❌ KẾT NỐI THẤT BẠI (Mã lỗi: {response.status_code})")
                print(f"Chi tiết lỗi từ OpenRouter: {response.text}")
    except Exception as e:
        print(f"⚠️ LỖI KỸ THUẬT KHI CALL API: {str(e)}")

async def test_embeddings():
    print("\n--- 3. THỬ EMBEDDINGS (OpenRouter) ---")
    from app.vectorstore import get_embeddings
    embeddings = get_embeddings()
    try:
        # Test synchronous embedding (since langchain-openai uses it)
        # We wrap in run_in_executor if needed, but here we just call it
        vector = await asyncio.to_thread(embeddings.embed_query, "test")
        print(f"✅ EMBEDDING THÀNH CÔNG! Độ dài vector: {len(vector)}")
    except Exception as e:
        print(f"❌ EMBEDDING THẤT BẠI: {str(e)}")

async def test_pinecone():
    print("\n--- 4. THỬ KẾT NỐI PINECONE ---")
    from app.vectorstore import get_pinecone_client
    from app.config import settings
    try:
        pc = get_pinecone_client()
        index = pc.Index(settings.pinecone_index_name)
        stats = index.describe_index_stats()
        print(f"✅ PINECONE KẾT NỐI THÀNH CÔNG!")
        print(f"Thống kê Index: {stats}")
    except Exception as e:
        print(f"❌ PINECONE THẤT BẠI: {str(e)}")

async def run_all():
    await test_openrouter()
    await test_embeddings()
    await test_pinecone()

if __name__ == "__main__":
    asyncio.run(run_all())
