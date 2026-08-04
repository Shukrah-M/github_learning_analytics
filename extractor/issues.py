"""Extract GitHub issues and comments within the observation window."""

from extractor.github_api import GitHubAPIClient
from utils.observation_window import (
    OBSERVATION_END,
    is_within_observation_window,
    parse_datetime,
)


def extract_issues(owner, repo):
    """
    Extract real GitHub issues created inside the fixed
    observation window.
    """
    client = GitHubAPIClient()

    issues = client.get_paginated(
        f"/repos/{owner}/{repo}/issues",
        params={
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": 100,
        },
    )

    cleaned_issues = []

    for item in issues:
        # GitHub includes pull requests in the issues endpoint.
        if "pull_request" in item:
            continue

        created_at = parse_datetime(
            item.get("created_at")
        )

        # Ignore issues created outside the fixed window.
        if not is_within_observation_window(
            created_at
        ):
            continue

        closed_at = parse_datetime(
            item.get("closed_at")
        )

        # Only count an issue as closed when it was closed
        # before the observation-window cutoff.
        closed_within_window = (
            closed_at is not None
            and closed_at < OBSERVATION_END
        )

        effective_state = (
            "closed"
            if closed_within_window
            else "open"
        )

        effective_closed_at = (
            closed_at
            if closed_within_window
            else None
        )

        user = item.get("user") or {}

        issue_data = {
            "github_issue_id": item.get("id"),
            "issue_number": item.get("number"),
            "author_login": user.get("login"),
            "title": item.get("title"),
            "body": item.get("body"),
            "state": effective_state,
            "created_at": created_at,
            "updated_at": parse_datetime(
                item.get("updated_at")
            ),
            "closed_at": effective_closed_at,
            "comments_url": item.get(
                "comments_url"
            ),
        }

        cleaned_issues.append(issue_data)

    return cleaned_issues


def extract_issue_comments(comments_url):
    """
    Extract issue comments created inside the fixed
    observation window.
    """
    if not comments_url:
        return []

    client = GitHubAPIClient()

    # Convert the full GitHub API URL into an endpoint
    # accepted by GitHubAPIClient.
    endpoint = comments_url.replace(
        "https://api.github.com",
        "",
    )

    comments = client.get_paginated(
        endpoint,
        params={
            "per_page": 100,
        },
    )

    cleaned_comments = []

    for item in comments:
        created_at = parse_datetime(
            item.get("created_at")
        )

        # Ignore comments outside the fixed window.
        if not is_within_observation_window(
            created_at
        ):
            continue

        user = item.get("user") or {}

        comment_data = {
            "github_comment_id": item.get("id"),
            "author_login": user.get("login"),
            "body": item.get("body"),
            "created_at": created_at,
            "updated_at": parse_datetime(
                item.get("updated_at")
            ),
        }

        cleaned_comments.append(comment_data)

    return cleaned_comments