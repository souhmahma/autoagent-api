import re
from app.core.config import settings


async def summarize_text(text: str, max_sentences: int = 3) -> str:

    if not text or len(text.strip()) < 50:
        return text.strip()

    # Gemini-powered summarization
    if settings.GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.5-flash-lite")
            prompt = (
                f"Summarize the following text in {max_sentences} clear sentences. "
                f"Be concise and keep only the most important information.\n\n{text}"
            )
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            pass  

    # Extractive fallback: pick first N sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    selected = sentences[:max_sentences]
    return " ".join(selected) if selected else text[:300] + "..."