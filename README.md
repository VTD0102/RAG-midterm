# 🤖 RAG Chatbot — Local Development

> Local RAG chatbot với Google Gemini, Pinecone, LangChain, Next.js

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Google Gemini 2.0 Flash |
| Embedding | `text-embedding-004` (768d) |
| Vector DB | Pinecone Serverless |
| Agent | LangChain + Hybrid Search (Semantic + BM25) |
| Memory | SQLite (per-session history) |
| Backend | Python FastAPI + SSE streaming |
| Frontend | Next.js 15 (App Router, TypeScript) |
| DevOps | Docker Compose |

## Tính năng

- ✅ **SSE Streaming** — câu trả lời xuất hiện real-time token-by-token
- ✅ **Source Citations** — hiển thị nguồn tài liệu kèm số trang
- ✅ **Session Management** — nhiều phiên hội thoại độc lập, lưu vào SQLite
- ✅ **Hybrid Search** — kết hợp semantic + BM25 keyword search
- ✅ **Document Upload** — kéo thả PDF, TXT, DOCX, MD vào giao diện
- ✅ **Markdown rendering** — syntax highlight, tables, code blocks
- ✅ **Docker Compose** — khởi động toàn bộ stack bằng 1 lệnh

---

## Cài đặt (Local Dev)

### 1. Lấy API Keys

- **Google Gemini**: [aistudio.google.com](https://aistudio.google.com) → Get API Key
- **Pinecone**: [pinecone.io](https://pinecone.io) → tạo account free tier → API Keys

### 2. Cài đặt Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Mở .env và điền GOOGLE_API_KEY, PINECONE_API_KEY
```

### 3. Chạy Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 4. Cài đặt & Chạy Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # đã có sẵn API_URL=http://localhost:8000
npm run dev
```

Mở http://localhost:3000

---

## Chạy với Docker Compose

```bash
# 1. Tạo file .env cho backend
cp backend/.env.example backend/.env
# Điền vào backend/.env:
#   GOOGLE_API_KEY=...
#   PINECONE_API_KEY=...

# 2. Tạo file .env.local cho frontend
cp frontend/.env.local.example frontend/.env.local

# 3. Khởi động
docker compose up --build

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
```

---

## Cách sử dụng

1. **Upload tài liệu** — click "Upload tài liệu" ở sidebar → kéo thả file
2. **Đặt câu hỏi** — gõ câu hỏi vào ô chat → Enter để gửi
3. **Xem nguồn** — nhấn vào "N nguồn tài liệu" bên dưới câu trả lời
4. **Tạo session mới** — nhấn "Cuộc trò chuyện mới"

---

## Cấu trúc dự án

```
RAG-midterm/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI + endpoints
│   │   ├── agent.py         # RAG agent + streaming + hybrid search
│   │   ├── ingest.py        # Document ingestion pipeline
│   │   ├── vectorstore.py   # Pinecone + Gemini embedding setup
│   │   ├── memory.py        # SQLite session memory
│   │   ├── schemas.py       # Pydantic models
│   │   └── config.py        # Settings
│   ├── data/                # Uploaded documents + sessions.db
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/page.tsx     # Main page
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── UploadPanel.tsx
│   │   │   └── SourceCard.tsx
│   │   └── lib/api.ts       # API client (SSE + REST)
│   └── Dockerfile
└── docker-compose.yml
```

## API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `POST` | `/chat` | Chat (stream=true → SSE) |
| `POST` | `/ingest` | Upload & index tài liệu |
| `GET` | `/sessions` | Danh sách sessions |
| `DELETE` | `/sessions/{id}` | Xóa session |
| `GET` | `/health` | Health check |
