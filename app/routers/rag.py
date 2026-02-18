from fastapi import APIRouter, HTTPException
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
from app.schemas import RAGRequest, RAGResponse, LinkInfo
from app.config import GEMINI_API_KEY, GEMINI_DEFAULT_MODEL, SERPER_API_KEY, SERPER_API_URL
import re

router = APIRouter()


# =========================
# Clean Gemini Response
# =========================
def clean_gemini_response(text: str) -> str:
    if not text:
        return "لم يتم توليد رد"

    text = re.sub(r'```[\w]*\n?.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'(?<!\w)\*(?!\*)(.+?)\*(?!\*)', r'\1', text)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[\*\-]\s+', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +\n', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()


# =========================
# Supported Websites Config
# =========================
WEBSITES = {
    "altibbi": {
        "domain": "altibbi.com",
        "name": "الطبي (Altibbi)",
    },
    "mayoclinic": {
        "domain": "mayoclinic.org/ar",
        "name": "مايو كلينك (Mayo Clinic)",
    },
    "mawdoo3": {
        "domain": "mawdoo3.com",
        "name": "موضوع (Mawdoo3)",
    },
}

# =========================
# Search via Serper API
# =========================
def search_serper(query: str, website: str = "altibbi", num_links: int = 1) -> list[dict]:
    
    site_config = WEBSITES.get(website)
    if not site_config:
        print(f"Unknown website: {website}, falling back to altibbi")
        site_config = WEBSITES["altibbi"]

    domain = site_config["domain"]
    
    url = SERPER_API_URL

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {"q": f"site:{domain} {query}"}

    try:
        print(f"Searching Google via Serper API: site:{domain} {query}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"Serper API response received")
        
        results = []
        for result in data.get("organic", []):
            link = result.get("link")
            if link:
                results.append({
                    "url": link,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                })
                print(f" Found link [{len(results)}]: {link}")
                if len(results) >= num_links:
                    break

        if not results:
            print(f"No links found for {domain}")
        
        return results

    except requests.exceptions.RequestException as e:
        print(f" Serper API request error: {e}")
        return []
    except Exception as e:
        print(f" Serper API error: {e}")
        return []


# =========================
# FIXED: Scrape Altibbi Page with Proper Encoding
# =========================
def scrape_page_content(url: str) -> str:
    

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar-SA,ar;q=0.9,en;q=0.8",
        "Accept-Charset": "utf-8",
    }

    try:
        print(f" Scraping: {url}")
        
        # FIX 1: Get response without manual encoding handling
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        #  FIX 2: Force UTF-8 encoding for Arabic content
        response.encoding = 'utf-8'
        
        print(f"   Status: {response.status_code}")
        print(f"   Encoding: {response.encoding}")
        
        #  FIX 3: Parse with utf-8 explicitly
        soup = BeautifulSoup(response.content, "html.parser", from_encoding='utf-8')
        
        # Remove noise elements
        for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript", "aside", "form", "button"]):
            tag.decompose()
        
        # Remove ads and menus
        for ad_class in [".ads", ".advertisement", ".menu", ".navigation", "[class*='ad-']", "[id*='ad-']"]:
            for elem in soup.select(ad_class):
                elem.decompose()
        
        # FIX 4: Better Altibbi-specific content selectors
        content_selectors = [
            "article",
            "main",
            ".content",
            ".article-content",
            ".post-content",
            ".article-body",
            ".post-body",
            "#content",
            "[class*='content']",
            "[id*='article']",
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content and len(main_content.get_text(strip=True)) > 100:
                print(f"Found content using selector: {selector}")
                break
        
        # Fallback: Find largest text block
        if not main_content or len(main_content.get_text(strip=True)) < 100:
            print("Using fallback: finding largest text block")
            all_divs = soup.find_all(['div', 'section', 'article'])
            if all_divs:
                main_content = max(all_divs, key=lambda x: len(x.get_text(strip=True)))
        
        # Final fallback to body
        if not main_content:
            main_content = soup.body if soup.body else soup
        
        # FIX 5: Extract text properly
        if main_content:
            text = main_content.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)
        
        # FIX 6: Clean Arabic text
        text = re.sub(r'\s+', ' ', text)  # Normalize all whitespace
        text = text.strip()
        
        print(f"    Extracted {len(text)} characters")
        print(f"    First 200 chars: {text[:200]}")
        
        # Check if we got valid Arabic/English text
        if len(text) < 50 or text.count('�') > 10:
            print("WARNING: Content might be corrupted")
        
        return text[:5000]

    except requests.exceptions.RequestException as e:
        print(f"Request error for {url}: {e}")
        return ""
    except Exception as e:
        print(f"Scraping error for {url}: {e}")
        import traceback
        traceback.print_exc()
        return ""


# =========================
# RAG Endpoint
# =========================
@router.post("/query", response_model=RAGResponse)
async def rag_query(request: RAGRequest):
   
    try:
        site_config = WEBSITES.get(request.website, WEBSITES["altibbi"])
        site_name = site_config["name"]
        
        print(f"\n{'='*60}")
        print(f"RAG Query: {request.query}")
        print(f"Website: {site_name}")
        print(f"Requested links: {request.num_links}")
        print(f"{'='*60}\n")
        
        # Step 1: Search the chosen website via Serper API
        search_results = search_serper(request.query, website=request.website, num_links=request.num_links)
        
        if not search_results:
            raise HTTPException(
                status_code=404,
                detail=f"لم يتم العثور على محتوى من {site_name}. حاول استخدام مصطلحات أخرى."
            )
        
        print(f"\nStep 2: Scraping content from {len(search_results)} link(s)\n")
        
        # Step 2: Scrape all pages and collect content per link
        scraped_sources = []
        for i, result in enumerate(search_results, 1):
            print(f"   [{i}/{len(search_results)}] Scraping: {result['url']}")
            content = scrape_page_content(result["url"])
            
            if content and len(content) >= 100 and content.count('�') <= 10:
                scraped_sources.append({
                    "url": result["url"],
                    "title": result["title"],
                    "snippet": result["snippet"],
                    "content": content,
                })
                print(f"   [{i}] OK — {len(content)} chars\n")
            else:
                print(f"   [{i}] Skipped — insufficient or corrupted content\n")
        
        if not scraped_sources:
            raise HTTPException(
                status_code=500,
                detail=f"فشل في استخراج المحتوى الكافي من {site_name}"
            )
        
        used_links = [
            LinkInfo(url=s["url"], title=s["title"], snippet=s["snippet"])
            for s in scraped_sources
        ]
        
        print(f"{'='*60}")
        print(f"Step 3: Sending {len(scraped_sources)} source(s) to Gemini API")
        print(f"{'='*60}\n")
        
        # Configure Gemini with user's API key and model if provided
        api_key = request.api_key or GEMINI_API_KEY
        model_name = request.model or GEMINI_DEFAULT_MODEL
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # Step 3: Build multi-source RAG prompt for Gemini
        context_blocks = []
        for i, source in enumerate(scraped_sources, 1):
            context_blocks.append(f"[مصدر {i}] ({source['url']})\n{source['content']}")
        
        combined_context = "\n\n---\n\n".join(context_blocks)
        
        rag_prompt = f"""أنت مساعد طبي متخصص. أجب على السؤال بناءً فقط على المصادر المقدمة أدناه من {site_name}.

المصادر:
{combined_context}

السؤال: {request.query}

التعليمات:
- أجب بالعربية الفصحى بشكل واضح ومنظم
- استخدم فقط المعلومات من المصادر المقدمة أعلاه، ولا تضيف أي معلومات من خارجها
- في نهاية إجابتك، اذكر أرقام المصادر التي استخدمتها بالشكل التالي: "المصادر المستخدمة: [مصدر 1]، [مصدر 2]، ..."
- إذا لم تحتوي المصادر على إجابة كافية، اذكر ذلك بوضوح
- نظم الإجابة في نقاط إذا كان ذلك مناسباً

الإجابة:"""

        try:
            response = model.generate_content(rag_prompt)
            raw_answer = response.text if response.text else "لم يتم توليد رد"
            cleaned_answer = clean_gemini_response(raw_answer)
            
            print("Gemini response received successfully\n")
            
        except Exception as gemini_error:
            print(f"Gemini API Error: {gemini_error}")
            raise HTTPException(
                status_code=500,
                detail=f"خطأ في Gemini API: {str(gemini_error)}"
            )
        
        print(f"{'='*60}")
        print("RAG Query Completed Successfully!")
        print(f"Used {len(used_links)} link(s): {[l.url for l in used_links]}")
        print(f"{'='*60}\n")
        
        return RAGResponse(
            query=request.query,
            source=f"{site_name} (via Google Serper API)",
            response=cleaned_answer,
            used_links=used_links
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"خطأ غير متوقع: {str(e)}")