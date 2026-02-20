import re
import aiohttp
from bs4 import BeautifulSoup
from collections import Counter

from utils.respond import respond
from db.apikeys import get_key


__plugin__ = {
    "name": "TLDR",
    "category": "utils",
    "description": (
        "Summarize text, files, or web links using Gemini AI.\n\n"
        "Usage:\n"
        "` .tldr 5 points `\n"
        "` .tldr 3 para `\n"
        "` .tldr 120 words `\n"
        "` .tldr 6 sentences `\n"
        "` .tldr https://example.com `\n\n"
        "Reply to a message or a `.txt/.log` file to summarize.\n\n"
        "Optional Gemini Setup:\n"
        "Set API key using:\n"
        "` .setapi GEMINI_API_KEY <your_api_key> `\n\n"
        "If no API key is set, a local summarizer is used."
    ),
    "commands": {
        "tldr": "Summarize text, files, or web links",
    },
}

REQUIRED_KEY = "GEMINI_API_KEY"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-pro:generateContent"
)


# ----------------------------
# Extract article text
# ----------------------------
async def fetch_url_text(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return None
            html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.extract()

    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()


# ----------------------------
# Parse instruction
# ----------------------------
def parse_instruction(args):
    text = " ".join(args).lower()

    match = re.search(
        r"(\d+)\s*(points|para|paragraphs|words|sentences)",
        text,
    )

    if match:
        number = match.group(1)
        mode = match.group(2)

        if "point" in mode:
            return f"Summarize in {number} concise bullet points."
        if "para" in mode:
            return f"Summarize in {number} short paragraphs."
        if "word" in mode:
            return f"Summarize in approximately {number} words."
        if "sentence" in mode:
            return f"Summarize in {number} sentences."

    return "Summarize in 5 concise bullet points."


# ----------------------------
# Local summarizer
# ----------------------------
def local_summarize(text, sentence_count=5):
    sentences = re.split(r'(?<=[.!?]) +', text)

    # If too short, still reduce it slightly
    if len(sentences) <= sentence_count:
        return " ".join(sentences[:sentence_count])

    words = re.findall(r"\w+", text.lower())
    freq = Counter(words)

    sentence_scores = {}
    for sentence in sentences:
        score = sum(
            freq.get(word.lower(), 0)
            for word in re.findall(r"\w+", sentence)
        )
        sentence_scores[sentence] = score

    top_sentences = sorted(
        sentence_scores,
        key=sentence_scores.get,
        reverse=True
    )[:sentence_count]

    return " ".join(top_sentences)


# ----------------------------
# Gemini summarizer
# ----------------------------
async def gemini_summarize(api_key, instruction, content):
    payload = {
        "contents": [{
            "parts": [{
                "text": f"{instruction}\n\n{content}"
            }]
        }]
    }

    params = {"key": api_key}

    async with aiohttp.ClientSession() as session:
        async with session.post(
            GEMINI_URL, params=params, json=payload
        ) as resp:
            data = await resp.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None


# ----------------------------
# Main handler
# ----------------------------
async def handler(event, args):
    reply = await event.get_reply_message()
    instruction = parse_instruction(args)

    content = None

    # 1️⃣ Priority: reply text
    if reply and reply.text:
        content = reply.text

    # 2️⃣ Reply file
    elif reply and reply.document:
        file_path = await reply.download_media()
        try:
            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:
                content = f.read()
        except Exception:
            content = None

    # 3️⃣ Direct URL
    elif args:
        for arg in args:
            if arg.startswith("http"):
                content = await fetch_url_text(arg)
                break

    # 4️⃣ Inline text (only if not reply)
    if not content and args:
        content = " ".join(args)

    if not content:
        return await respond(event, "No content to summarize.")

    content = content.strip()
    content = content[:20000]  # safety limit

    api_key = get_key(REQUIRED_KEY)

    # Try Gemini
    if api_key:
        summary = await gemini_summarize(
            api_key,
            instruction,
            content
        )
        if summary and summary.strip() != content.strip():
            return await respond(event, summary)

    # Fallback
    summary = local_summarize(content, 5)

    if summary.strip() == content.strip():
        summary = summary[:1000]  # force reduction

    return await respond(event, summary)