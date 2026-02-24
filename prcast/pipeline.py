"""Main pipeline -- orchestrates PR collection, script generation, audio, and feed."""

import json
from datetime import datetime, timezone
from pathlib import Path

from pydub import AudioSegment

from prcast.collector import collect_pr
from prcast.scriptwriter import generate_script
from prcast.audio import render_episode
from prcast.feed import generate_feed, generate_master_feed
from prcast.config import settings


def _repo_slug(repo: str) -> str:
    return repo.replace("/", "-").lower()


def _load_manifest() -> list[dict]:
    manifest_path = settings.FEEDS_DIR / "episodes.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text())
    return []


def _save_manifest(episodes: list[dict]):
    manifest_path = settings.FEEDS_DIR / "episodes.json"
    manifest_path.write_text(json.dumps(episodes, indent=2, default=str))


async def process_pr(repo: str, pr_number: int) -> dict:
    """Full pipeline: collect -> script -> audio -> feed. Returns episode info."""
    print(f"[PRCast] Processing {repo}#{pr_number}...")

    # 1. Collect PR data
    print(f"  Collecting PR data...")
    pr = await collect_pr(repo, pr_number, settings.GITHUB_TOKEN)

    # 2. Generate script
    print(f"  Generating script...")
    script = await generate_script(pr)
    print(f"  Script: {len(script)} segments")

    # 3. Render audio
    slug = _repo_slug(repo)
    episode_id = f"{slug}-pr-{pr_number}"
    print(f"  Rendering audio...")
    audio_path = await render_episode(script, episode_id, slug)
    print(f"  Audio: {audio_path}")

    # 4. Get duration
    audio = AudioSegment.from_mp3(str(audio_path))
    duration_seconds = int(len(audio) / 1000)

    # 5. Build episode metadata
    episode = {
        "id": episode_id,
        "repo": repo,
        "title": f"PR #{pr_number}: {pr.title}",
        "description": (
            f"Pull Request by {pr.author}: {pr.title}. "
            f"{pr.files_changed} files changed, "
            f"+{pr.additions} -{pr.deletions} lines. "
            f"Branch: {pr.head_branch} -> {pr.base_branch}."
        ),
        "audio_file": f"{episode_id}.mp3",
        "duration_seconds": duration_seconds,
        "pub_date": datetime.now(timezone.utc).isoformat(),
        "pr_url": pr.url,
        "pr_number": pr_number,
    }

    # 6. Save script for reference
    script_dir = settings.FEEDS_DIR / "scripts"
    script_dir.mkdir(exist_ok=True)
    script_path = script_dir / f"{episode_id}.json"
    script_path.write_text(json.dumps({
        "episode": episode,
        "script": script,
    }, indent=2))

    # 7. Update manifest and feeds
    manifest = _load_manifest()
    # Remove old episode for same PR if re-processing
    manifest = [e for e in manifest if e["id"] != episode_id]
    manifest.append(episode)
    _save_manifest(manifest)

    # 8. Generate repo feed + master feed
    repo_episodes = [e for e in manifest if e["repo"] == repo]
    generate_feed(repo, repo_episodes)

    all_repos = list(set(e["repo"] for e in manifest))
    generate_master_feed(all_repos)

    print(f"[PRCast] Done: {episode_id} ({duration_seconds}s)")
    return episode
