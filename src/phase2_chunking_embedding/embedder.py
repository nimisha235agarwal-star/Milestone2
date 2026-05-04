import os
import glob
from datetime import datetime
from langchain_text_splitters import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
from langchain_huggingface import HuggingFaceInferenceAPIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

def get_metadata_from_filename(filename):
    """
    Extracts the source URL, fund slug, and timestamp from the generated HTML filename.
    Expected format: fund-slug_YYYYMMDD_HHMMSS.html
    """
    basename = os.path.basename(filename)
    name_part = basename.replace('.html', '')
    parts = name_part.rsplit('_', 2)
    
    if len(parts) >= 3:
        fund_slug = parts[0]
        # Format the timestamp nicely for the Last_Updated_Date
        raw_timestamp = f"{parts[1]}_{parts[2]}"
        try:
            dt = datetime.strptime(raw_timestamp, "%Y%m%d_%H%M%S")
            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            timestamp = raw_timestamp
    else:
        fund_slug = name_part
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    source_url = f"https://groww.in/mutual-funds/{fund_slug}"
    return source_url, fund_slug, timestamp

def process_and_embed(raw_html_dir, chroma_db_dir):
    print(f"[{datetime.now().isoformat()}] Initializing Serverless Embedding Model (BAAI/bge-small-en-v1.5)...")
    
    # Using Serverless Inference API to save memory and CPU on Render
    hf_token = os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    if not hf_token:
        print("❌ ERROR: HUGGINGFACEHUB_API_TOKEN not found in environment variables.")
        return

    embedding_model = HuggingFaceInferenceAPIEmbeddings(
        api_key=hf_token,
        model_name="BAAI/bge-small-en-v1.5"
    )
    
    print(f"[{datetime.now().isoformat()}] Connecting to Chroma Cloud...")
    import chromadb
    
    client = chromadb.CloudClient(
        tenant=os.environ.get("CHROMA_TENANT", "default_tenant"),
        database=os.environ.get("CHROMA_DATABASE", "default_database"),
        api_key=os.environ.get("CHROMA_API_KEY", ""),
    )
    vectorstore = Chroma(
        client=client,
        collection_name="groww_mutual_funds",
        embedding_function=embedding_model
    )
    
    # Phase 1: HTML Header Splitter
    headers_to_split_on = [
        ("h1", "Header 1"),
        ("h2", "Header 2"),
        ("h3", "Header 3"),
        ("h4", "Header 4"),
    ]
    html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    
    # Phase 2: Recursive Character Splitter (protecting tables natively)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    
    html_files = glob.glob(os.path.join(raw_html_dir, "*.html"))
    if not html_files:
        print(f"No HTML files found in {raw_html_dir}. Did the scraper run?")
        return
        
    for filepath in html_files:
        print(f"\nProcessing: {os.path.basename(filepath)}")
        
        source_url, fund_slug, timestamp = get_metadata_from_filename(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Extract clean text while preserving some structure
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Get text with newlines to separate elements
        clean_text = soup.get_text(separator='\n', strip=True)
        
        # Execute Phase 2 (Directly on text now)
        chunks = text_splitter.split_text(clean_text)
        
        # Convert to Document objects for compatibility with add_documents
        from langchain.docstore.document import Document
        doc_chunks = []
        for chunk in chunks:
            doc_chunks.append(Document(
                page_content=chunk,
                metadata={
                    'Source_URL': source_url,
                    'Fund_Name': fund_slug,
                    'Last_Updated_Date': timestamp
                }
            ))
            
        print(f"  -> Generated {len(doc_chunks)} chunks.")
        
        # Upsert Logic: Clear out old embeddings for this specific URL and Fund to prevent duplication
        print(f"  -> Cleaning up old chunks for {fund_slug}...")
        try:
            # Delete by Source_URL
            existing_url = vectorstore.get(where={"Source_URL": source_url})
            if existing_url and existing_url.get('ids'):
                vectorstore.delete(ids=existing_url['ids'])
                print(f"     Deleted {len(existing_url['ids'])} old chunks by URL.")
            
            # Also check by Fund_Name just in case the URL changed
            existing_fund = vectorstore.get(where={"Fund_Name": fund_slug})
            if existing_fund and existing_fund.get('ids'):
                vectorstore.delete(ids=existing_fund['ids'])
                print(f"     Deleted {len(existing_fund['ids'])} old chunks by Fund Name.")
        except Exception as e:
            print(f"     Cleanup note: {e}")

        # Insert fresh chunks
        print(f"  -> Upserting fresh chunks to ChromaDB...")
        vectorstore.add_documents(documents=doc_chunks)
        
        # Cleanup local file to keep ONLY the latest data
        try:
            os.remove(filepath)
            print(f"  -> Successfully processed and removed: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"  -> Warning: Could not remove file {filepath}: {e}")
        
    print(f"\n[{datetime.now().isoformat()}] Chunking and Embedding pipeline completed successfully.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    raw_html_dir = os.path.join(base_dir, "data", "raw_html")
    chroma_db_dir = os.path.join(base_dir, "data", "chroma_db")
    
    os.makedirs(chroma_db_dir, exist_ok=True)
    
    process_and_embed(raw_html_dir, chroma_db_dir)
