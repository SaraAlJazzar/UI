import logging

from fastapi import APIRouter, HTTPException
import google.generativeai as genai

from app.config import GEMINI_API_KEY, GEMINI_DEFAULT_MODEL
from app.schemas import RAGRequest, RAGResponse, LinkInfo
from app.services.scraper import WEBSITES, search_serper, scrape_page_content, clean_gemini_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/query", response_model=RAGResponse)
async def rag_query(request: RAGRequest):
    try:
        site_config = WEBSITES.get(request.website, WEBSITES["altibbi"])
        site_name = site_config["name"]

        search_results = search_serper(request.query, website=request.website, num_links=request.num_links)

        if not search_results:
            raise HTTPException(
                status_code=404,
                detail=f"لم يتم العثور على محتوى من {site_name}. حاول استخدام مصطلحات أخرى.",
            )

        scraped_sources = []
        for result in search_results:
            content = scrape_page_content(result["url"])
            if content and len(content) >= 100 and content.count("\ufffd") <= 10:
                scraped_sources.append({
                    "url": result["url"],
                    "title": result["title"],
                    "snippet": result["snippet"],
                    "content": content,
                })

        if not scraped_sources:
            raise HTTPException(
                status_code=500,
                detail=f"فشل في استخراج المحتوى الكافي من {site_name}",
            )

        used_links = [
            LinkInfo(url=s["url"], title=s["title"], snippet=s["snippet"])
            for s in scraped_sources
        ]

        api_key = request.api_key or GEMINI_API_KEY
        model_name = request.model or GEMINI_DEFAULT_MODEL
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

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
        except Exception as gemini_error:
            logger.error("Gemini API error: %s", gemini_error)
            raise HTTPException(status_code=500, detail=f"خطأ في Gemini API: {str(gemini_error)}")

        return RAGResponse(
            query=request.query,
            source=f"{site_name} (via Google Serper API)",
            response=cleaned_answer,
            used_links=used_links,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected RAG error: %s", e)
        raise HTTPException(status_code=500, detail=f"خطأ غير متوقع: {str(e)}")
