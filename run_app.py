import os
from dotenv import load_dotenv
import uvicorn

# Load API keys from .env
load_dotenv()

if __name__ == "__main__":
    print("Starting Groww Mutual Fund FAQ Assistant...")
    print("UI will be available at: http://localhost:8000")
    
    # Run the FastAPI app
    uvicorn.run("src.phase5_api_ui.app:app", host="0.0.0.0", port=8000, reload=True)
