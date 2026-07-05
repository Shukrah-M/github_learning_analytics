from datetime import datetime
from extractor.github_api import GitHubAPIClient


def parse_datetime(value):
    if value is None:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def extract_pull_requests(owner, repo):
    client = GitHubAPIClient()

    pull_requests = client.get_paginated(
        f"/repos/{owner}/{repo}/pulls",
        params={"state": "all"}
    )

    cleaned_pull_requests = []

    for item in pull_requests:
        pr_data = {
            "github_pr_id": item.get("id"),
            "pr_number": item.get("number"),
            "author_login": item.get("user", {}).get("login"),
            "title": item.get("title"),
            "body": item.get("body"),
            "state": item.get("state"),
            "merged": item.get("merged_at") is not None,
            "created_at": parse_datetime(item.get("created_at")),
            "updated_at": parse_datetime(item.get("updated_at")),
            "closed_at": parse_datetime(item.get("closed_at")),
            "merged_at": parse_datetime(item.get("merged_at")),
        }

        cleaned_pull_requests.append(pr_data)

    return cleaned_pull_requests


def extract_pull_request_reviews(owner, repo, pr_number):
    client = GitHubAPIClient()

    reviews = client.get_paginated(
        f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    )

    cleaned_reviews = []

    for item in reviews:
        review_data = {
            "github_review_id": item.get("id"),
            "reviewer_login": item.get("user", {}).get("login") if item.get("user") else None,
            "state": item.get("state"),
            "body": item.get("body"),
            "submitted_at": parse_datetime(item.get("submitted_at")),
        }

        cleaned_reviews.append(review_data)

    return cleaned_reviews