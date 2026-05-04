import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.phase3_retrieval_guardrails.rag_pipeline import MutualFundRAG

load_dotenv()

app = FastAPI(title="Groww Mutual Fund FAQ Assistant")

# Enable CORS for frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the RAG Pipeline lazily or with error handling
rag = None
try:
    print("Initializing RAG Pipeline...")
    rag = MutualFundRAG()
    print("RAG Pipeline initialized successfully.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize RAG Pipeline: {e}")
    # We don't raise here so the server can at least start and show logs

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

@app.get("/")
async def serve_index():
    return FileResponse("public/index.html")

# Serve other static files (CSS, JS, Images)
app.mount("/", StaticFiles(directory="public"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
