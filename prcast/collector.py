"""Collect PR data from GitHub."""

import httpx
from dataclasses import dataclass, field


@dataclass
class PRData:
    repo: str
    number: int
    title: str
    author: str
    body: str
    diff: str
    reviews: list[dict] = field(default_factory=list)
    comments: list[dict] = field(default_factory=list)
    state: str = ""
    merged: bool = False
    base_branch: str = ""
    head_branch: str = ""
    url: str = ""
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0


async def collect_pr(repo: str, pr_number: int, token: str) -> PRData:
    """Fetch full PR context from GitHub API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    diff_headers = {
        **headers,
        "Accept": "application/vnd.github.v3.diff",
    }

    base = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"

    async with httpx.AsyncClient(timeout=30) as client:
        # Fetch PR metadata
        pr_resp = await client.get(base, headers=headers)
        pr_resp.raise_for_status()
        pr = pr_resp.json()

        # Fetch diff (truncate to ~50k chars to stay within token limits)
        diff_resp = await client.get(base, headers=diff_headers)
        diff_resp.raise_for_status()
        diff = diff_resp.text[:50000]

        # Fetch reviews
        reviews_resp = await client.get(f"{base}/reviews", headers=headers)
        reviews_resp.raise_for_status()
        reviews = [
            {
                "author": r["user"]["login"],
                "state": r["state"],
                "body": r.get("body", ""),
            }
            for r in reviews_resp.json()
            if r.get("body")
        ]

        # Fetch review comments (inline code comments)
        review_comments_resp = await client.get(f"{base}/comments", headers=headers)
        review_comments_resp.raise_for_status()
        review_comments = [
            {
                "author": c["user"]["login"],
                "body": c["body"],
                "path": c.get("path", ""),
                "line": c.get("original_line"),
            }
            for c in review_comments_resp.json()
        ]

        # Fetch issue comments (general discussion)
        issue_comments_resp = await client.get(
            f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments",
            headers=headers,
        )
        issue_comments_resp.raise_for_status()
        issue_comments = [
            {
                "author": c["user"]["login"],
                "body": c["body"],
            }
            for c in issue_comments_resp.json()
        ]

    return PRData(
        repo=repo,
        number=pr_number,
        title=pr["title"],
        author=pr["user"]["login"],
        body=pr.get("body") or "",
        diff=diff,
        reviews=reviews,
        comments=review_comments + issue_comments,
        state=pr["state"],
        merged=pr.get("merged", False),
        base_branch=pr["base"]["ref"],
        head_branch=pr["head"]["ref"],
        url=pr["html_url"],
        files_changed=pr.get("changed_files", 0),
        additions=pr.get("additions", 0),
        deletions=pr.get("deletions", 0),
    )
