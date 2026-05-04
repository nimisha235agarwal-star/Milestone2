# Groww Mutual Fund FAQ Assistant — Quickstart

This project consists of a **FastAPI Backend** and a **Next.js Dark Theme Frontend**.

### 1. Prerequisites
- Python 3.9+
- Node.js 18+
- Groq API Key & Chroma Cloud Keys in `.env`

### 2. Setup

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd web
npm install
```

### 3. Running the Application

**Step 1: Start Backend (Port 8000)**
```bash
python run_app.py
```

**Step 2: Start Frontend (Port 3000)**
```bash
cd web
npm run dev
```

### 4. Architecture Notes
- **Frontend**: Next.js 14 (App Router) + TailwindCSS + Lucide Icons.
- **Theme**: Premium Dark Theme with Groww Green accents.
- **Components**: Modular architecture (Sidebar, ChatWindow, MessageItem, ChatInput).
- **Backend**: FastAPI with async multi-threading support.
- **RAG**: Chroma Cloud + Groq (Llama 3.3).
