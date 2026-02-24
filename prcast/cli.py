"""CLI entry point for PRCast -- run locally or from GitHub Actions."""

import argparse
import asyncio
import sys

from prcast.pipeline import process_pr


def main():
    parser = argparse.ArgumentParser(description="PRCast - AI podcasts from PRs")
    parser.add_argument("repo", help="GitHub repo (owner/repo)")
    parser.add_argument("pr", type=int, help="PR number")
    args = parser.parse_args()

    episode = asyncio.run(process_pr(args.repo, args.pr))
    print(f"\nEpisode generated: {episode['title']}")
    print(f"Audio: audio/{episode['repo'].replace('/', '-').lower()}/{episode['audio_file']}")
    print(f"Duration: {episode['duration_seconds']}s")


if __name__ == "__main__":
    main()
