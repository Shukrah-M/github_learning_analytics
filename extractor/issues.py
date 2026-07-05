from datetime import datetime
from extractor.github_api import GitHubAPIClient


def parse_datetime(value):
    if value is None:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def extract_issues(owner, repo):
    client = GitHubAPIClient()

    issues = client.get_paginated(
        f"/repos/{owner}/{repo}/issues",
        params={"state": "all"}
    )

    cleaned_issues = []

    for item in issues:
        # GitHub returns pull requests inside the issues endpoint.
        # This skips PRs so we only save real issues here.
        if "pull_request" in item:
            continue

        issue_data = {
            "github_issue_id": item.get("id"),
            "issue_number": item.get("number"),
            "author_login": item.get("user", {}).get("login"),
            "title": item.get("title"),
            "body": item.get("body"),
            "state": item.get("state"),
            "created_at": parse_datetime(item.get("created_at")),
            "updated_at": parse_datetime(item.get("updated_at")),
            "closed_at": parse_datetime(item.get("closed_at")),
            "comments_url": item.get("comments_url"),
        }

        cleaned_issues.append(issue_data)

    return cleaned_issues


def extract_issue_comments(comments_url):
    client = GitHubAPIClient()

    # Convert full GitHub URL into API endpoint
    endpoint = comments_url.replace("https://api.github.com", "")

    comments = client.get_paginated(endpoint)

    cleaned_comments = []

    for item in comments:
        comment_data = {
            "github_comment_id": item.get("id"),
            "author_login": item.get("user", {}).get("login"),
            "body": item.get("body"),
            "created_at": parse_datetime(item.get("created_at")),
            "updated_at": parse_datetime(item.get("updated_at")),
        }

        cleaned_comments.append(comment_data)

    return cleaned_comments