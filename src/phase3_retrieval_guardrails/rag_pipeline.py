import os
import re
from datetime import datetime
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# 1. PII Scrubber (Section 3.2)
# ──────────────────────────────────────────────
def scrub_pii(query: str) -> str:
    """Redacts PII such as Phone, Email, PAN, and Aadhaar."""
    # Email
    query = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL REDACTED]', query)
    # Indian Phone (10 digits)
    query = re.sub(r'\b\d{10}\b', '[PHONE REDACTED]', query)
    # PAN Card (5 letters, 4 digits, 1 letter)
    query = re.sub(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', '[PAN REDACTED]', query)
    # Aadhaar (12 digits)
    query = re.sub(r'\b\d{4}\s?\d{4}\s?\d{4}\b', '[AADHAAR REDACTED]', query)
    return query

# ──────────────────────────────────────────────
# 2. Intent Classifier (Section 3.2)
# ──────────────────────────────────────────────
def is_advisory_query(query: str) -> bool:
    """
    Stricter intent classifier to block investment advice and speculative queries.
    """
    advisory_keywords = [
        "should i", "which is better", "best fund", "recommend", "advice",
        "buy now", "sell now", "invest in", "is it safe", "good time",
        "my portfolio", "better than", "worth it", "risky", "suggest",
        "how much return", "future performance", "prediction"
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in advisory_keywords)

# ──────────────────────────────────────────────
# 3. RAG Pipeline (Sections 3.3 + 3.4)
# ──────────────────────────────────────────────
class MutualFundRAG:
    def __init__(self):
        print(f"[{datetime.now().isoformat()}] Initializing RAG Pipeline...")

        # ── Embedding Model (same as ingestion) ──
        self.embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

        # ── Chroma Cloud Connection ──
        import chromadb
        print(f"  -> Connecting to Chroma Cloud...")
        client = chromadb.CloudClient(
            tenant=os.environ.get("CHROMA_TENANT", "default_tenant"),
            database=os.environ.get("CHROMA_DATABASE", "default_database"),
            api_key=os.environ.get("CHROMA_API_KEY", ""),
        )
        self.vectorstore = Chroma(
            client=client,
            collection_name="groww_mutual_funds",
            embedding_function=self.embedding_model
        )

        # ── Groq LLM ──
        print(f"  -> Initializing Groq LLM (llama-3.3-70b-versatile)...")
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            api_key=os.environ.get("GROQ_API_KEY"),
        )

        # ── Session History Store ──
        self.session_history = {} # thread_id -> list of messages

        # ── Prompt Constructor (Section 3.3) ──
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a strictly factual HDFC Mutual Fund Assistant.
Your ONLY job is to provide objective data from the provided context.

POLITENESS:
If the user says "thanks", "thank you", or "thanks a lot", respond with: "Happy to help! Let me know if you need anything else."

CALCULATION CAPABILITY:
You can estimate future values based on historical CAGR returns found in the context.
Parameters needed:
1. Investment Amount (e.g., ₹5000)
2. Frequency: SIP (Monthly) or Lumpsum (One-time)
3. Duration (e.g., 3 years or 5 years)

RULES FOR CALCULATIONS:
1. CLARIFICATION: If the user hasn't specified the Frequency (SIP vs Lumpsum) or Duration, DO NOT guess. Instead, ask: "To give you an accurate projection, should I consider this as a Monthly SIP or a One-time Lumpsum? Also, for how many years?"
2. DATA SOURCE: Only use the 1Y, 3Y, 5Y, or 10Y historical returns found in the provided context for the specific fund mentioned.
3. DISCLAIMER: ALWAYS state: "This is a projection based on historical returns and does not guarantee future results."
4. Maximum of 4 sentences for any response.

CONTEXT:
{context}

CHAT HISTORY:
{chat_history}
"""),
            ("human", "{query}")
        ])

    def _calculate_returns(self, principal, rate_annual, years, is_sip=True):
        """Helper to perform the math."""
        try:
            r = float(rate_annual) / 100
            t = float(years)
            if is_sip:
                i = r / 12
                n = t * 12
                fv = principal * (((1 + i)**n - 1) / i) * (1 + i)
            else:
                fv = principal * ((1 + r)**t)
            return round(fv, 2)
        except:
            return None

    def _format_history(self, thread_id):
        history = self.session_history.get(thread_id, [])[-5:] # Last 5 turns
        formatted = ""
        for msg in history:
            formatted += f"{msg['role'].upper()}: {msg['content']}\n"
        return formatted if formatted else "No previous history."

    def _format_context(self, docs):
        """Formats retrieved documents into a context string for the LLM."""
        parts = []
        for d in docs:
            parts.append(d.page_content)
        return "\n\n".join(parts)

    def answer_query(self, raw_query: str, thread_id: str = "default") -> str:
        # ── Step 1: PII Scrubbing ──
        safe_query = scrub_pii(raw_query)

        # ── Step 2: Intent Check / Guardrail ──
        if is_advisory_query(safe_query):
            return ("Facts-only. No investment advice. "
                    "I cannot recommend funds or evaluate your portfolio. "
                    "Please consult a registered financial advisor or visit "
                    "https://www.amfiindia.com/investor-corner/knowledge-center.html")

        # ── Step 3: Retrieval (Section 3.3) ──
        # Simple metadata filtering logic
        search_filter = {}
        query_lower = safe_query.lower()
        if "mid-cap" in query_lower or "midcap" in query_lower:
            search_filter["Fund_Name"] = "hdfc-mid-cap-fund-direct-growth"
        elif "large-cap" in query_lower or "largecap" in query_lower:
            search_filter["Fund_Name"] = "hdfc-large-cap-fund-direct-growth"
        elif "equity" in query_lower:
            search_filter["Fund_Name"] = "hdfc-equity-fund-direct-growth"
        elif "elss" in query_lower or "tax saver" in query_lower:
            search_filter["Fund_Name"] = "hdfc-elss-tax-saver-fund-direct-plan-growth"
        elif "focused" in query_lower:
            search_filter["Fund_Name"] = "hdfc-focused-fund-direct-growth"

        if search_filter:
            docs = self.vectorstore.similarity_search(safe_query, k=5, filter=search_filter)
        else:
            docs = self.vectorstore.similarity_search(safe_query, k=5)
            
        if not docs:
            return "I don't have enough data to answer this query based on the current sources."

        # ── Step 4: Generation (Section 3.4) ──
        # Build prompt with context and history
        chat_history = self._format_history(thread_id)
        chain = self.prompt | self.llm
        response = chain.invoke({
            "context": self._format_context(docs),
            "chat_history": chat_history,
            "query": safe_query
        })
        answer_text = response.content

        # ── Step 5: Post-Processor & Formatter (Section 3.4) ──
        # Enforce max 3 sentences
        sentences = answer_text.strip().split('. ')
        if len(sentences) > 3:
            answer_text = '. '.join(sentences[:3])
            if not answer_text.endswith('.'):
                answer_text += '.'

        # Save to history for this thread
        if thread_id not in self.session_history:
            self.session_history[thread_id] = []
        self.session_history[thread_id].append({"role": "user", "content": safe_query})
        self.session_history[thread_id].append({"role": "assistant", "content": answer_text})

        # Return only the factual answer without the mandatory citation footer
        return answer_text.strip()


# ──────────────────────────────────────────────
# Test Harness
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Mutual Fund FAQ Assistant — RAG Pipeline Test")
    print("=" * 60)

    try:
        rag = MutualFundRAG()

        # Test 1: Advisory query → should be refused
        print("\n[Test 1] Advisory Query (Should hit Guardrail)")
        q1 = "Which fund is better between HDFC Mid-cap and Large-cap?"
        print(f"  Query:  {q1}")
        print(f"  Answer: {rag.answer_query(q1)}\n")

        # Test 2: Factual query → retrieval + Groq generation
        print("[Test 2] Factual Query — Exit Load")
        q2 = "What is the exit load for HDFC mid-cap fund?"
        print(f"  Query:  {q2}")
        print(f"  Answer: {rag.answer_query(q2)}\n")

        # Test 3: Factual query — Expense Ratio
        print("[Test 3] Factual Query — Expense Ratio")
        q3 = "What is the expense ratio of HDFC ELSS Tax Saver Fund?"
        print(f"  Query:  {q3}")
        print(f"  Answer: {rag.answer_query(q3)}\n")

        # Test 4: PII query → should redact
        print("[Test 4] PII Query (Should redact sensitive data)")
        q4 = "My PAN is ABCDE1234F, what is the minimum SIP for HDFC large cap?"
        print(f"  Query:  {q4}")
        print(f"  Answer: {rag.answer_query(q4)}\n")

    except Exception as e:
        print(f"\nError: {e}")
