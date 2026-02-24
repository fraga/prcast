"""Generate podcast script from PR data -- supports OpenAI, Gemini, and Anthropic."""

import os
import httpx
from prcast.collector import PRData
from prcast.config import settings


SYSTEM_PROMPT = """You are a podcast script writer for PRCast, a developer podcast that covers Pull Requests.

You write a monologue script for a single host named {host} who breaks down code changes in an engaging, conversational way.

RULES:
- Write ONLY the spoken monologue. No stage directions, no sound effects, no labels.
- Do NOT prefix lines with the speaker name.
- Keep it conversational -- rhetorical questions, "now here's the interesting part", "let me walk you through this" are good.
- Explain technical concepts so a mid-level developer would follow along.
- Cover: what the PR does, why it matters, interesting code changes, any discussions/reviews.
- If there were review comments or debates, recap them like you're telling a story.
- Keep episodes between 2-5 minutes of spoken content (roughly 300-800 words).
- Start with a brief intro ("Hey everyone, welcome back to PRCast...") and end with a quick sign-off.
- Be opinionated. If the code is clever, say so. If something looks risky, call it out.
- DO NOT make up information not present in the PR data.
"""

EPISODE_PROMPT = """Generate a podcast monologue for this Pull Request:

**Repository:** {repo}
**PR #{number}: {title}**
**Author:** {author}
**Branch:** {head} -> {base}
**Changes:** {files_changed} files, +{additions} -{deletions}

**Description:**
{body}

**Code Diff (key changes):**
```diff
{diff}
```

**Reviews:**
{reviews}

**Discussion:**
{comments}

Write the monologue now.
"""


def _format_reviews(reviews: list[dict]) -> str:
    if not reviews:
        return "No reviews yet."
    return "\n".join(f"- {r['author']} ({r['state']}): {r['body']}" for r in reviews)


def _format_comments(comments: list[dict]) -> str:
    if not comments:
        return "No comments."
    parts = []
    for c in comments:
        path = f" on `{c['path']}`" if c.get("path") else ""
        parts.append(f"- {c['author']}{path}: {c['body']}")
    return "\n".join(parts)


def _build_prompt(pr: PRData) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt)."""
    system = SYSTEM_PROMPT.format(host=settings.HOST_A_NAME)
    user = EPISODE_PROMPT.format(
        repo=pr.repo,
        number=pr.number,
        title=pr.title,
        author=pr.author,
        head=pr.head_branch,
        base=pr.base_branch,
        files_changed=pr.files_changed,
        additions=pr.additions,
        deletions=pr.deletions,
        body=pr.body or "(no description)",
        diff=pr.diff[:30000],
        reviews=_format_reviews(pr.reviews),
        comments=_format_comments(pr.comments),
    )
    return system, user


async def _generate_openai(system: str, user: str) -> str:
    """Generate via OpenAI API (GPT-4o, etc.)."""
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{settings.OPENAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.9,
                "max_tokens": 4096,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _generate_gemini(system: str, user: str) -> str:
    """Generate via Google Gemini API."""
    from google import genai

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = await client.aio.models.generate_content(
        model=settings.LLM_MODEL,
        contents=user,
        config=genai.types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.9,
            max_output_tokens=4096,
        ),
    )
    return response.text


async def _generate_anthropic(system: str, user: str) -> str:
    """Generate via Anthropic Claude API."""
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL,
                "system": system,
                "messages": [{"role": "user", "content": user}],
                "temperature": 0.9,
                "max_tokens": 4096,
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


PROVIDERS = {
    "openai": _generate_openai,
    "gemini": _generate_gemini,
    "anthropic": _generate_anthropic,
}


async def generate_script(pr: PRData) -> list[dict]:
    """Generate a monologue script. Returns list of {speaker, text} segments."""
    system, user = _build_prompt(pr)

    provider = settings.LLM_PROVIDER
    if provider not in PROVIDERS:
        raise ValueError(
            f"Unknown LLM provider '{provider}'. "
            f"Supported: {', '.join(PROVIDERS.keys())}"
        )

    raw = await PROVIDERS[provider](system, user)
    return _parse_monologue(raw)


def _parse_monologue(raw: str) -> list[dict]:
    """Parse monologue into segments for TTS rendering.

    Splits on paragraph breaks so TTS gets natural pauses.
    Each segment is attributed to the single host.
    """
    segments = []
    for paragraph in raw.strip().split("\n\n"):
        text = paragraph.strip()
        if text:
            segments.append({
                "speaker": settings.HOST_A_NAME,
                "text": text,
            })
    return segments
