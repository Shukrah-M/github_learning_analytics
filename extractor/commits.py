"""Extract repository commits within the fixed observation window."""

from datetime import datetime

from extractor.github_api import GitHubAPIClient
from utils.observation_window import (
    is_within_observation_window,
)


def parse_datetime(value):
    """Convert a GitHub timestamp to a datetime."""
    if value is None:
        return None

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def extract_commits(owner, repo):
    """
    Extract commits and retain only records inside the
    fixed research observation window.
    """
    client = GitHubAPIClient()

    commits = client.get_paginated(
        f"/repos/{owner}/{repo}/commits"
    )

    cleaned_commits = []

    for item in commits:
        commit_info = item.get("commit", {})

        author_info = commit_info.get(
            "author",
            {},
        ) or {}

        committer_info = commit_info.get(
            "committer",
            {},
        ) or {}

        github_author = item.get("author")

        # Use the committer timestamp for committed_at.
        # Fall back to the author timestamp if necessary.
        committed_at = parse_datetime(
            committer_info.get("date")
            or author_info.get("date")
        )

        # Ignore commits outside the fixed observation window.
        if not is_within_observation_window(
            committed_at
        ):
            continue

        cleaned_commit = {
            "sha": item.get("sha"),
            "author_name": author_info.get("name"),
            "author_email": author_info.get("email"),
            "author_login": (
                github_author.get("login")
                if github_author
                else None
            ),
            "message": commit_info.get("message"),
            "committed_at": committed_at,
        }

        cleaned_commits.append(cleaned_commit)

    return cleaned_commits