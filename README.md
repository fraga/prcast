# PRCast

AI-generated podcasts from Pull Requests.

PRCast watches your GitHub repos via webhooks, collects PR diffs and discussions, generates a two-host conversational podcast script using Gemini, renders audio with TTS, and publishes RSS feeds -- one per repo plus a combined master feed.

## Features (planned)

- GitHub webhook listener for PR events (opened, merged, reviewed, commented)
- Full PR context collection (diff, reviews, discussions, CI status)
- AI script generation with two distinct "host" personalities
- Multi-speaker TTS audio rendering
- Per-repo RSS feeds + combined master feed
- Spotify-compatible podcast format

## Stack

- **Python 3.12+** / FastAPI
- **Google Gemini** for script generation
- **ElevenLabs** or **Edge TTS** for audio
- **feedgen** for RSS
- **ffmpeg** / **pydub** for audio processing

## Setup

```bash
# Clone
git clone https://github.com/fraga/prcast.git
cd prcast

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python -m prcast.server
```

## Project Structure

```
prcast/
  prcast/
    __init__.py
    server.py          # FastAPI webhook endpoint
    collector.py       # Fetches PR diff, comments, reviews
    scriptwriter.py    # Gemini prompt -> dialogue script
    audio.py           # TTS rendering (two speakers)
    feed.py            # RSS feed generator
    config.py          # Settings and configuration
  feeds/               # Generated RSS XML per repo
  audio/               # Generated MP3 files
  templates/           # Prompt templates
  .env.example
  requirements.txt
```

## License

MIT
