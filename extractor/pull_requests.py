"""Extract pull requests and reviews within the observation window."""

from extractor.github_api import GitHubAPIClient
from utils.observation_window import (
    OBSERVATION_END,
    is_within_observation_window,
    parse_datetime,
)


def extract_pull_requests(owner, repo):
    """
    Extract pull requests created inside the fixed
    observation window.
    """
    client = GitHubAPIClient()

    pull_requests = client.get_paginated(
        f"/repos/{owner}/{repo}/pulls",
        params={
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": 100,
        },
    )

    cleaned_pull_requests = []

    for item in pull_requests:
        created_at = parse_datetime(
            item.get("created_at")
        )

        # Ignore pull requests created outside the window.
        if not is_within_observation_window(
            created_at
        ):
            continue

        closed_at = parse_datetime(
            item.get("closed_at")
        )

        merged_at = parse_datetime(
            item.get("merged_at")
        )

        # A pull request only counts as merged when it
        # was merged before the observation-window cutoff.
        merged_within_window = (
            merged_at is not None
            and merged_at < OBSERVATION_END
        )

        # A pull request only counts as closed when it
        # was closed before the observation-window cutoff.
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

        effective_merged_at = (
            merged_at
            if merged_within_window
            else None
        )

        user = item.get("user") or {}

        pr_data = {
            "github_pr_id": item.get("id"),
            "pr_number": item.get("number"),
            "author_login": user.get("login"),
            "title": item.get("title"),
            "body": item.get("body"),
            "state": effective_state,
            "merged": merged_within_window,
            "created_at": created_at,
            "updated_at": parse_datetime(
                item.get("updated_at")
            ),
            "closed_at": effective_closed_at,
            "merged_at": effective_merged_at,
        }

        cleaned_pull_requests.append(pr_data)

    return cleaned_pull_requests


def extract_pull_request_reviews(
    owner,
    repo,
    pr_number,
):
    """
    Extract pull-request reviews submitted inside the
    fixed observation window.
    """
    client = GitHubAPIClient()

    reviews = client.get_paginated(
        (
            f"/repos/{owner}/{repo}/pulls/"
            f"{pr_number}/reviews"
        ),
        params={
            "per_page": 100,
        },
    )

    cleaned_reviews = []

    for item in reviews:
        submitted_at = parse_datetime(
            item.get("submitted_at")
        )

        # Ignore reviews submitted outside the window.
        if not is_within_observation_window(
            submitted_at
        ):
            continue

        user = item.get("user") or {}

        review_data = {
            "github_review_id": item.get("id"),
            "reviewer_login": user.get("login"),
            "state": item.get("state"),
            "body": item.get("body"),
            "submitted_at": submitted_at,
        }

        cleaned_reviews.append(review_data)

    return cleaned_reviews