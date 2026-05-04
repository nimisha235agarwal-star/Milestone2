# 🚀 Project Summary: GrowwAI HDFC Assistant 


### 🌟 What is this?
We built a **Smart Financial Assistant** specifically for **HDFC Mutual Funds**. It's not just a chatbot; it's a "Brain" that reads real-time data from Groww and answers your questions with 100% factual accuracy—no guessing, no "hallucinations."

---

### 🛠️ How we built it (The "Simple" Tech Stack)

1.  **The "Eyes" (Daily Scraper)**: 
    Every day, a robot (GitHub Actions) goes to the Groww website, reads the latest HDFC fund data (NAV, Returns, Fees), and saves it.
    
2.  **The "Memory" (Vector Database)**: 
    We use **Chroma Cloud**. Think of this as a massive, organized library where the assistant "looks up" facts before it speaks.
    
3.  **The "Voice" (AI Intelligence)**: 
    We use **Llama 3.3 (via Groq)**. It’s a super-fast AI that takes the facts found in the library and turns them into a polite, human-like response.
    
4.  **The "Face" (Premium UI)**: 
    A sleek, professional website designed to look exactly like **Groww**. It features easy-to-use buttons, chat history, and even feedback thumbs.

---

### 🔥 Key Superpowers
*   **Returns Calculator**: You can ask, *"What if I invest ₹10,000 monthly for 5 years?"* and it will do the math based on real historical data.
*   **Fact-Checked**: If the info isn't on Groww, it won't lie. It strictly sticks to the data we scrape.
*   **Conversational Memory**: It remembers your previous questions, so you can have a real conversation (e.g., *"What about Large Cap?"* after asking about Mid-cap).
*   **Auto-Cleanup**: The system automatically deletes old data to keep the database fresh and fast.

---

### 🌐 Where is it living?
*   **Scheduler**: Runs daily on GitHub.
*   **Backend**: Hosted on **Render** (The engine).
*   **Frontend**: Hosted on **Vercel** (The website you see).

**Final Status: [SUCCESS] Fully functional, Branding matched, and Pushed to GitHub.**
