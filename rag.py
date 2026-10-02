"""هسته‌ی RAG: embedding → جست‌وجو در Supabase → پاسخ LLM بر اساس متن‌های پیدا‌شده."""
import os
import re
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

load_dotenv()

CHAT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
TOP_K = int(os.getenv("TOP_K", "5"))
MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.25"))

SYSTEM_PROMPT = """تو دستیار کارگزاری کاریزما هستی. فقط بر اساس «متن‌های مرجع» که در پیام کاربر آمده پاسخ بده.
- اگر پاسخ در متن‌های مرجع نیست، بگو اطلاعاتش را نداری و پیشنهاد کن با پشتیبانی تماس بگیرد. چیزی از خودت نساز.
- فارسی، کوتاه، محترمانه و مرحله‌به‌مرحله جواب بده و در پایان منبع را مثل [1] یا [2] بنویس.
- اگر کاربر می‌گوید «سیستم خطا می‌دهد/پاسخگو نیست»، قطعی نگو سیستم قطع است؛ اول موارد رایج را مرور کن (مثلاً روز تولد، کد ملی، موبایل به نام خودش).
- رمز عبور و کد یکبارمصرف را نخواه. پیشنهاد خرید/فروش سهم یا مشاوره سرمایه‌گذاری نده.
"""


def _need(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"مقدار {name} در فایل .env تنظیم نشده است")
    return value


@lru_cache
def db():
    return create_client(_need("SUPABASE_URL"), _need("SUPABASE_KEY"))


@lru_cache
def llm() -> OpenAI:
    return OpenAI(api_key=_need("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL") or None, timeout=60)


def normalize(text: str) -> str:
    """یکسان‌سازی حروف عربی/فارسی و ارقام."""
    text = text.translate(str.maketrans({"ي": "ی", "ك": "ک", "ۀ": "ه"}))
    text = text.translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))
    return text.strip()


def embed(texts: list[str]) -> list[list[float]]:
    resp = llm().embeddings.create(model=EMBED_MODEL, input=[normalize(t) for t in texts])
    return [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]


def search(question: str, k: int = TOP_K) -> list[dict]:
    vec = embed([question])[0]
    rows = db().rpc("match_chunks", {"query_embedding": vec, "match_count": k}).execute().data or []
    return [r for r in rows if r["similarity"] >= MIN_SIMILARITY]


def ask(question: str, history: list[dict] | None = None) -> tuple[str, list[dict]]:
    """history: لیست {'role','content'}.  خروجی: (پاسخ، منابع)"""
    history = history or []
    query = question
    if history and len(question.split()) < 4:  # پیام کوتاهِ دنباله‌دار مثل «و برای رایان همراه؟»
        last_user = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        query = f"{last_user} {question}"

    rows = search(query)
    if rows:
        context = "\n\n".join(f"[{i}] ({r['heading']})\n{r['content']}" for i, r in enumerate(rows, 1))
    else:
        context = "(هیچ متن مرتبطی پیدا نشد)"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history[-6:],
        {"role": "user", "content": f"متن‌های مرجع:\n{context}\n\nسؤال: {question}"},
    ]
    resp = llm().chat.completions.create(model=CHAT_MODEL, messages=messages, temperature=0)
    return resp.choices[0].message.content or "", rows
