"""RSS feed generator for PRCast."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from feedgen.feed import FeedGenerator

from prcast.config import settings


def _repo_slug(repo: str) -> str:
    """Convert owner/repo to a safe filename slug."""
    return repo.replace("/", "-").lower()


def _repo_image_url(repo: str) -> str:
    """Resolve per-repo podcast image from JSON map; fallback to PODCAST_IMAGE."""
    raw = os.getenv("PODCAST_IMAGE_MAP", "").strip()
    if raw:
        try:
            image_map = json.loads(raw)
            if isinstance(image_map, dict):
                mapped = image_map.get(repo)
                if isinstance(mapped, str) and mapped.strip():
                    return mapped.strip()
        except json.JSONDecodeError:
            pass
    return settings.PODCAST_IMAGE


def generate_feed(
    repo: str,
    episodes: list[dict],
) -> Path:
    """Generate or update RSS feed for a repo.

    Each episode dict should have:
        - id: str (unique episode id)
        - title: str
        - description: str
        - audio_file: str (filename relative to audio/<repo_slug>/)
        - duration_seconds: int
        - pub_date: datetime
        - pr_url: str
    """
    slug = _repo_slug(repo)
    feed_path = settings.FEEDS_DIR / f"{slug}.xml"

    fg = FeedGenerator()
    fg.load_extension("podcast")

    # Channel metadata
    fg.title(f"{settings.PODCAST_TITLE} - {repo}")
    fg.link(href=f"{settings.BASE_URL}/feeds/{slug}.xml", rel="self")
    fg.link(href=f"https://github.com/{repo}", rel="alternate")
    fg.description(f"AI-generated podcast covering Pull Requests for {repo}")
    fg.language(settings.PODCAST_LANGUAGE)
    fg.generator("PRCast")
    fg.lastBuildDate(datetime.now(timezone.utc))

    # Podcast-specific
    fg.podcast.itunes_author(settings.PODCAST_AUTHOR)
    fg.podcast.itunes_category(settings.PODCAST_CATEGORY)
    fg.podcast.itunes_explicit("no")
    fg.podcast.itunes_owner(
        name=settings.PODCAST_AUTHOR,
        email=settings.PODCAST_EMAIL or "noreply@example.com",
    )
    repo_image = _repo_image_url(repo)
    if repo_image:
        fg.podcast.itunes_image(repo_image)

    # Episodes (newest first)
    for ep in sorted(episodes, key=lambda e: e["pub_date"], reverse=True):
        fe = fg.add_entry()
        fe.id(ep["id"])
        fe.title(ep["title"])
        fe.description(ep["description"])
        fe.published(ep["pub_date"])
        fe.link(href=ep.get("pr_url", ""))

        audio_url = f"{settings.BASE_URL}/audio/{slug}/{ep['audio_file']}"
        audio_path = settings.AUDIO_DIR / slug / ep["audio_file"]
        file_size = audio_path.stat().st_size if audio_path.exists() else 0

        fe.enclosure(audio_url, str(file_size), "audio/mpeg")
        fe.podcast.itunes_duration(ep.get("duration_seconds", 0))

    fg.rss_file(str(feed_path), pretty=True)
    return feed_path


def generate_master_feed(repos: list[str]) -> Path:
    """Generate a combined master feed from all repo feeds."""
    feed_path = settings.FEEDS_DIR / "prcast.xml"

    fg = FeedGenerator()
    fg.load_extension("podcast")

    fg.title(settings.PODCAST_TITLE)
    fg.link(href=f"{settings.BASE_URL}/feeds/prcast.xml", rel="self")
    fg.description(settings.PODCAST_DESCRIPTION)
    fg.language(settings.PODCAST_LANGUAGE)
    fg.generator("PRCast")
    fg.lastBuildDate(datetime.now(timezone.utc))

    fg.podcast.itunes_author(settings.PODCAST_AUTHOR)
    fg.podcast.itunes_category(settings.PODCAST_CATEGORY)
    fg.podcast.itunes_explicit("no")
    if settings.PODCAST_IMAGE:
        fg.podcast.itunes_image(settings.PODCAST_IMAGE)

    # Load episodes from episode manifest
    manifest_path = settings.FEEDS_DIR / "episodes.json"
    if manifest_path.exists():
        import json
        all_episodes = json.loads(manifest_path.read_text())
        for ep in sorted(all_episodes, key=lambda e: e["pub_date"], reverse=True):
            slug = _repo_slug(ep["repo"])
            fe = fg.add_entry()
            fe.id(ep["id"])
            fe.title(f"[{ep['repo']}] {ep['title']}")
            fe.description(ep["description"])
            fe.published(ep["pub_date"])
            fe.link(href=ep.get("pr_url", ""))

            audio_url = f"{settings.BASE_URL}/audio/{slug}/{ep['audio_file']}"
            audio_path = settings.AUDIO_DIR / slug / ep["audio_file"]
            file_size = audio_path.stat().st_size if audio_path.exists() else 0

            fe.enclosure(audio_url, str(file_size), "audio/mpeg")
            fe.podcast.itunes_duration(ep.get("duration_seconds", 0))

    fg.rss_file(str(feed_path), pretty=True)
    return feed_path
