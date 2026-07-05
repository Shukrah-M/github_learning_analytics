from datetime import datetime
from extractor.github_api import GitHubAPIClient


def parse_datetime(value):
    if value is None:
        return None

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def extract_repository(owner, repo):
    client = GitHubAPIClient()

    data = client.get(f"/repos/{owner}/{repo}")

    repository_data = {
        "github_id": data["id"],
        "name": data["name"],
        "owner": data["owner"]["login"],
        "description": data.get("description"),
        "language": data.get("language"),
        "default_branch": data.get("default_branch"),
        "created_at": parse_datetime(data.get("created_at")),
        "updated_at": parse_datetime(data.get("updated_at")),
    }

    return repository_data