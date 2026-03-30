# 🤖 RAG Chatbot — Local Development

> Local RAG chatbot với OpenRouter, Pinecone, LangChain, React (Vite)

![Giao diện RAG Chatbot](/home/taitu/.gemini/antigravity/brain/5489682c-f36a-4389-88be-4e0b7a87e41d/chatbot_ui_mockup_premium_1774906362511.png)

## 🏗️ Sơ đồ hoạt động (System Architecture)

![Sơ đồ kiến trúc hệ thống RAG](/home/taitu/.gemini/antigravity/brain/5489682c-f36a-4389-88be-4e0b7a87e41d/rag_system_architecture_illustration_1774906345127.png)

```mermaid
graph TD
    User((Người dùng))
    
    subgraph UI ["Giao diện (Frontend)"]
        ChatUI[Giao diện Chat]
        FileUI[Quản lý File]
    end
    
    subgraph Backend ["Xử lý (FastAPI)"]
        API[API Endpoints]
        Agent[LangChain Agent]
        Retriever[Hybrid Retriever]
        Embed[OpenRouter Embedding]
    end
    
    subgraph Storage ["Lưu trữ (Database)"]
        Pinecone[(Pinecone Vector DB)]
        SQLite[(SQLite Chat History)]
        Disk[(Local Disk /data)]
    end
    
    User <-->|Tương tác| ChatUI
    User -->|Upload Tài Liệu| FileUI
    
    ChatUI <-->|SSE Streaming| API
    FileUI <-->|REST| API
    
    API <--> Agent
    Agent <--> SQLite
    Agent <--> Retriever
    
    Retriever <--> Pinecone
    Retriever <--> Disk
    
    API -->|Ingest| Embed
    Embed --> Pinecone
```

## 🛠️ Công nghệ sử dụng (Tech Stack)

| Thành phần | Công nghệ | Chi tiết |
|:---|:---|:---|
| **Frontend** | React 18 + Vite | Giao diện hiện đại, tốc độ build nhanh với TypeScript. |
| **Styling** | Vanilla CSS | Tùy biến linh hoạt, thiết kế Premium/Dark Mode. |
| **Backend** | FastAPI (Python) | High-performance, async framework hỗ trợ SSE (Server-Sent Events). |
| **Framework RAG** | LangChain | Quản lý luồng truy xuất, Agent và Memory (Chat History). |
| **LLM Model** | OpenRouter (Gemini) | Sử dụng `google/gemini-2.0-flash-001` để trả lời câu hỏi. |
| **Embedding** | OpenRouter (OpenAI) | Model `text-embedding-3-small` (1536d) để vector hóa văn bản. |
| **Vector DB** | Pinecone | Lưu trữ và tìm kiếm vector (thông tin tài liệu) dạng Serverless. |
| **Memory** | SQLite | Lưu trữ lịch sử hội thoại bền vững cho từng Session. |
| **Search Engine**| Hybrid Search | Kết hợp Semantic Search (Vector) và BM25 (Keyword search). |

---

## 🌟 Tính năng nổi bật

- ✅ **SSE Streaming** — câu trả lời xuất hiện real-time từng token sinh động.
- ✅ **Source Citations** — trích dẫn chính xác nguồn tài liệu kèm nội dung liên quan.
- ✅ **Session Management** — lưu và tải lại lịch sử hội thoại từ SQLite.
- ✅ **Document Management** — Giao diện quản lý file: Upload, Xem danh sách & Xóa sạch dữ liệu khỏi Pinecone.
- ✅ **Hybrid Search** — tăng độ chính xác bằng cách kết hợp search theo ý nghĩa và từ khóa.
- ✅ **Docker Ready** — triển khai nhanh chóng với Docker Compose.

---

## 🚀 Hướng dẫn cài đặt

### 1. Cấu hình môi trường
- Tạo file `.env` trong thư mục `backend/` dựa trên `.env.example`.
- Điền các API Key: `OPENROUTER_API_KEY`, `PINECONE_API_KEY`, và thông tin Pinecone Index.

### 2. Cài đặt Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Cài đặt Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📂 Cấu trúc thư mục

```text
RAG-midterm/
├── backend/
│   ├── app/
│   │   ├── agent.py         # Logic RAG + LLM Agent
│   │   ├── vectorstore.py   # Kết nối Pinecone & Embeddings
│   │   ├── ingest.py        # Pipeline nạp và xử lý tài liệu
│   │   ├── memory.py        # Quản lý SQLite history
│   │   └── main.py          # Khai báo các API endpoints
│   ├── data/                # Nơi chứa tài liệu đã upload & DB
│   └── requirements.txt     # Danh sách thư viện Python
├── frontend/
│   ├── src/components/      # Các UI Components (Sidebar, FileManager...)
│   └── lib/api.ts           # Client giao tiếp với Backend
└── docker-compose.yml       # Cấu hình Deploy Docker
```

## 📡 API Endpoints chính

| Method | Endpoint | Mô tả |
|:---|:---|:---|
| `POST` | `/chat` | Chat với AI (hỗ trợ stream SSE) |
| `POST` | `/ingest` | Upload và đánh index tài liệu vào Pinecone |
| `GET` | `/files` | Liệt kê danh sách tài liệu đã tải lên |
| `DELETE` | `/files/{name}` | Xóa tài liệu khỏi Disk và Pinecone |
| `GET` | `/sessions/{id}/history` | Tải lại lịch sử tin nhắn của một phiên |
| `DELETE` | `/sessions/{id}` | Xóa phiên hội thoại |
