# Deployment Plan: Groww Mutual Fund FAQ Assistant

This document outlines the production deployment strategy for the RAG-based Mutual Fund Assistant.

---

## 1. Core Architecture (Production)
| Component | Technology | Hosting Provider |
| :--- | :--- | :--- |
| **Ingestion Scheduler** | Python Scripts | **GitHub Actions** (Cron) |
| **Vector Database** | ChromaDB | **Chroma Cloud** (Managed) |
| **LLM Inference** | Llama 3.3 | **Groq API** |
| **Backend API** | FastAPI (Python) | **Render** |
| **Frontend UI** | HTML/CSS/JS (Static) | **Vercel** |

---

## 2. Phase 1: GitHub Actions (Scheduler)
The scheduler will run daily to sync the latest fund data from Groww to Chroma Cloud.

### Setup Steps:
1.  **Repository Secrets**: Add the following to GitHub Secrets:
    -   `CHROMA_API_KEY`
    -   `CHROMA_TENANT`
    -   `CHROMA_DATABASE`
    -   `GROQ_API_KEY`
2.  **Workflow Configuration**:
    -   File: `.github/workflows/ingestion.yml`
    -   Schedule: `30 3 * * *` (9:00 AM IST daily)
    -   Steps: Checkout -> Set up Python -> Install Deps -> Run `src/scheduler_local.py`.

---

## 3. Phase 2: Render (Backend API)
The FastAPI server handles user queries, guardrails, and RAG retrieval.

### Setup Steps:
1.  **Connect Repo**: Link your GitHub repository to Render.
2.  **Service Type**: Web Service.
3.  **Build Command**: `pip install -r requirements.txt`
4.  **Start Command**: `uvicorn src.phase5_api_ui.app:app --host 0.0.0.0 --port $PORT`
5.  **Environment Variables**:
    -   `PYTHON_VERSION`: `3.9.0` or higher
    -   `CHROMA_API_KEY`, `CHROMA_TENANT`, `CHROMA_DATABASE`, `GROQ_API_KEY`
    -   `CORS_ORIGINS`: `https://your-frontend.vercel.app`

---

## 4. Phase 3: Vercel (Frontend UI)
The static basic UI (HTML/CSS) will be served via Vercel for high availability.

### Setup Steps:
1.  **File Structure**: Ensure `src/phase5_api_ui/static/` is the root or use a `public/` folder.
2.  **API URL Configuration**:
    -   Update the `fetch('/chat')` call in `index.html` to use an environment variable or a relative path if using a proxy.
    -   Recommended: Update `index.html` to use `window.location.origin` if hosted together, or a hardcoded Render URL for cross-origin.
3.  **Deploy**: Connect GitHub to Vercel and select the `static` directory as the root.

---

## 5. Security & Maintenance
-   **CORS Policy**: Restrict `allow_origins` in `app.py` to only your Vercel URL in production.
-   **API Keys**: Never commit `.env` files. Always use provider-managed secrets.
-   **Logging**: Use Render's log streaming and GitHub Action logs to monitor ingestion health.
-   **Health Checks**: Implement a `/health` endpoint in FastAPI to monitor service uptime.

---

## 6. Success Metrics for Deployment
-   **Latency**: Average RAG response time < 3 seconds.
-   **Uptime**: 99.9% availability for both API and Frontend.
-   **Accuracy**: Daily sync confirmed via GitHub Action status.
