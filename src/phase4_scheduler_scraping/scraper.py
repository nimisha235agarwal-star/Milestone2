import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# The 5 curated HDFC mutual fund URLs from Groww
URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
]

def clean_html(html_content):
    """
    Strips boilerplate and unnecessary tags from the HTML.
    Keeps the structural tags needed for HTML-aware chunking.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted noise
    for tag in soup(['nav', 'footer', 'header', 'script', 'style', 'aside', 'svg', 'button']):
        tag.decompose()

    # Remove sections that typically contain lists of other funds (noise for RAG)
    for div in list(soup.find_all('div')):
        if div is None: continue
        try:
            classes = div.get('class', [])
            if not classes: classes = []
            class_str = ' '.join(classes).lower() if isinstance(classes, list) else str(classes).lower()
            if any(keyword in class_str for keyword in ['related', 'footer', 'header', 'nav', 'similar', 'otherlink', 'recommendation']):
                div.decompose()
        except Exception:
            continue
            
    # Attempt to extract the main content container if available
    # On Groww, the primary details are often in a specific container
    main_content = soup.find('main')
    if main_content:
        return str(main_content)
    
    return str(soup)

def scrape_and_store(output_dir):
    """
    Navigates to the URLs, extracts HTML, cleans it, and saves it locally.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Standard headers to prevent getting immediately blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    print(f"[{datetime.now().isoformat()}] Starting scraping service...")
    
    for url in URLS:
        fund_slug = url.split('/')[-1]
        print(f"Scraping {fund_slug}...")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            cleaned_html = clean_html(response.text)
            
            # Edge Case: Check for minimum content length to avoid indexing broken pages
            from bs4 import BeautifulSoup
            soup_check = BeautifulSoup(cleaned_html, 'html.parser')
            text_len = len(soup_check.get_text(strip=True))
            if text_len < 300:
                print(f"  -> Skipping {fund_slug}: Content too short ({text_len} chars), likely a failed load.")
                continue

            # Save the file with a timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{fund_slug}_{timestamp}.html"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_html)
                
            print(f"  -> Saved to {filepath}")
            
        except requests.exceptions.RequestException as e:
            print(f"  -> Error scraping {url}: {e}")

if __name__ == "__main__":
    # Define the output directory (Groww/data/raw_html/)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    raw_html_dir = os.path.join(base_dir, "data", "raw_html")
    
    scrape_and_store(raw_html_dir)
    print(f"[{datetime.now().isoformat()}] Scraping completed.")
