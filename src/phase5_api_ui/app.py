import os
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.phase3_retrieval_guardrails.rag_pipeline import MutualFundRAG

app = FastAPI(title="Groww Mutual Fund FAQ Assistant")

# Enable CORS for frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the RAG Pipeline
# Ensure GROQ_API_KEY and Chroma Cloud keys are in .env
rag = MutualFundRAG()

from typing import Optional

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    thread_id: str

import anyio

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Isolation: thread_id is used to distinguish sessions. 
    # Currently, the RAG pipeline is stateless (no memory), 
    # so every request is naturally isolated.
    thread_id = request.thread_id or str(uuid.uuid4())
    
    try:
        # Run the synchronous RAG pipeline in a separate thread to avoid blocking the event loop.
        # Pass the thread_id to enable conversational memory for that specific session.
        answer = await anyio.to_thread.run_sync(rag.answer_query, request.message, thread_id)
        return ChatResponse(reply=answer, thread_id=thread_id)
    except Exception as e:
        print(f"Error in chat [Thread {thread_id}]: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open("public/index.html", "r") as f:
        return f.read()

# Serve static files (CSS/JS)
app.mount("/static", StaticFiles(directory="public"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
