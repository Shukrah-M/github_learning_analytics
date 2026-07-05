from datetime import datetime
from extractor.github_api import GitHubAPIClient


def parse_datetime(value):
    if value is None:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def extract_commits(owner, repo):
    client = GitHubAPIClient()

    commits = client.get_paginated(f"/repos/{owner}/{repo}/commits")

    cleaned_commits = []

    for item in commits:
        commit_info = item.get("commit", {})
        author_info = commit_info.get("author", {})
        github_author = item.get("author")

        cleaned_commit = {
            "sha": item.get("sha"),
            "author_name": author_info.get("name"),
            "author_email": author_info.get("email"),
            "author_login": github_author.get("login") if github_author else None,
            "message": commit_info.get("message"),
            "committed_at": parse_datetime(author_info.get("date")),
        }

        cleaned_commits.append(cleaned_commit)

    return cleaned_commits