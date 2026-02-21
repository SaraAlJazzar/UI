import re
import logging
import requests
from bs4 import BeautifulSoup
from app.config import SERPER_API_KEY, SERPER_API_URL

logger = logging.getLogger(__name__)

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


def search_serper(query: str, website: str = "altibbi", num_links: int = 1) -> list[dict]:
    site_config = WEBSITES.get(website)
    if not site_config:
        logger.warning("Unknown website: %s, falling back to altibbi", website)
        site_config = WEBSITES["altibbi"]

    domain = site_config["domain"]

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": f"site:{domain} {query}"}

    try:
        logger.info("Searching via Serper: site:%s %s", domain, query)
        response = requests.post(SERPER_API_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for result in data.get("organic", []):
            link = result.get("link")
            if link:
                results.append({
                    "url": link,
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                })
                if len(results) >= num_links:
                    break

        return results

    except requests.exceptions.RequestException as e:
        logger.error("Serper API request error: %s", e)
        return []
    except Exception as e:
        logger.error("Serper API error: %s", e)
        return []


def scrape_page_content(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar-SA,ar;q=0.9,en;q=0.8",
        "Accept-Charset": "utf-8",
    }

    try:
        logger.info("Scraping: %s", url)
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = "utf-8"

        soup = BeautifulSoup(response.content, "html.parser", from_encoding="utf-8")

        for tag in soup(["script", "style", "nav", "footer", "header", "iframe", "noscript", "aside", "form", "button"]):
            tag.decompose()

        for ad_class in [".ads", ".advertisement", ".menu", ".navigation", "[class*='ad-']", "[id*='ad-']"]:
            for elem in soup.select(ad_class):
                elem.decompose()

        content_selectors = [
            "article", "main", ".content", ".article-content",
            ".post-content", ".article-body", ".post-body",
            "#content", "[class*='content']", "[id*='article']",
        ]

        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content and len(main_content.get_text(strip=True)) > 100:
                break

        if not main_content or len(main_content.get_text(strip=True)) < 100:
            all_divs = soup.find_all(["div", "section", "article"])
            if all_divs:
                main_content = max(all_divs, key=lambda x: len(x.get_text(strip=True)))

        if not main_content:
            main_content = soup.body if soup.body else soup

        if main_content:
            text = main_content.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)

        text = re.sub(r"\s+", " ", text).strip()

        if len(text) < 50 or text.count("\ufffd") > 10:
            logger.warning("Content from %s might be corrupted", url)

        return text[:5000]

    except requests.exceptions.RequestException as e:
        logger.error("Request error for %s: %s", url, e)
        return ""
    except Exception as e:
        logger.error("Scraping error for %s: %s", url, e)
        return ""
