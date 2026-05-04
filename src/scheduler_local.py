import os
import sys
import subprocess
from datetime import datetime

# Define base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "data", "ingestion_logs.txt")

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

def run_phase(name, script_path):
    log(f"--- Starting Phase: {name} ---")
    try:
        # Use the current python executable (venv)
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        log(f"PHASE SUCCESS: {name}")
        log(f"STDOUT:\n{result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        log(f"PHASE FAILED: {name}")
        log(f"STDERR:\n{e.stderr}")
        return False

def main():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    log("==========================================")
    log("TRIGGERING LOCAL INGESTION SCHEDULER")
    log("==========================================")

    # Phase 1: Scraping
    scraper_path = os.path.join(BASE_DIR, "src", "phase4_scheduler_scraping", "scraper.py")
    if not run_phase("Data Scraping", scraper_path):
        log("Ingestion aborted due to Phase 1 failure.")
        return

    # Phase 2: Chunking & Embedding
    embedder_path = os.path.join(BASE_DIR, "src", "phase2_chunking_embedding", "embedder.py")
    if not run_phase("Chunking & Embedding", embedder_path):
        log("Ingestion aborted due to Phase 2 failure.")
        return

    log("==========================================")
    log("ALL INGESTION PHASES COMPLETED SUCCESSFULLY")
    log("==========================================")

if __name__ == "__main__":
    main()
