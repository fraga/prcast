"""TTS rendering -- turn a script into an MP3."""

import tempfile
from pathlib import Path

from pydub import AudioSegment

from prcast.config import settings


async def render_edge_tts(text: str, voice: str, output_path: Path):
    """Render text to MP3 using Edge TTS."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))


async def render_elevenlabs(text: str, voice: str, output_path: Path):
    """Render text to MP3 using ElevenLabs API."""
    import httpx

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
            headers={
                "xi-api-key": settings.ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            },
        )
        resp.raise_for_status()
        output_path.write_bytes(resp.content)


async def render_segment(text: str, voice: str, output_path: Path):
    """Render a single text segment to audio."""
    if settings.TTS_PROVIDER == "elevenlabs":
        await render_elevenlabs(text, voice, output_path)
    else:
        await render_edge_tts(text, voice, output_path)


async def render_episode(
    script: list[dict],
    episode_id: str,
    repo_slug: str,
) -> Path:
    """Render full episode from script segments. Returns path to final MP3."""
    output_dir = settings.AUDIO_DIR / repo_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{episode_id}.mp3"

    with tempfile.TemporaryDirectory() as tmpdir:
        segment_paths = []

        for i, segment in enumerate(script):
            seg_path = Path(tmpdir) / f"seg_{i:03d}.mp3"
            # Monologue: always use host A voice
            voice = settings.HOST_A_VOICE
            await render_segment(segment["text"], voice, seg_path)
            segment_paths.append(seg_path)

        # Combine segments with natural pauses between paragraphs
        combined = AudioSegment.empty()
        pause = AudioSegment.silent(duration=600)  # 600ms between paragraphs

        for seg_path in segment_paths:
            segment_audio = AudioSegment.from_mp3(str(seg_path))
            combined += segment_audio + pause

        # Export final episode
        combined.export(str(output_path), format="mp3", bitrate="128k")

    return output_path
