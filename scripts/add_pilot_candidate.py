"""Collect metadata for public GitHub pilot repository candidates."""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "data" / "pilot_repository_candidates.csv"

OBSERVATION_START = datetime(
    2026,
    1,
    2,
    tzinfo=timezone.utc,
)

OBSERVATION_END = datetime(
    2026,
    7,
    1,
    tzinfo=timezone.utc,
)

FIELDNAMES = [
    "candidate_id",
    "owner",
    "repository",
    "repository_url",
    "discovery_group",
    "primary_language",
    "created_at",
    "pushed_at",
    "is_fork",
    "is_archived",
    "is_disabled",
    "is_template",
    "description",
    "technical_status",
    "technical_reason",
    "manual_status",
    "manual_reason",
]


def parse_github_url(repository_url: str) -> tuple[str, str]:
    """Extract the repository owner and name from a GitHub URL."""
    cleaned_url = repository_url.strip().rstrip("/")

    if cleaned_url.endswith(".git"):
        cleaned_url = cleaned_url[:-4]

    parsed = urlparse(cleaned_url)

    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise ValueError(
            "Enter a GitHub repository URL such as "
            "https://github.com/owner/repository"
        )

    path_parts = [
        part
        for part in parsed.path.split("/")
        if part
    ]

    if len(path_parts) < 2:
        raise ValueError(
            "The URL must contain both the owner and repository name."
        )

    return path_parts[0], path_parts[1]


def parse_github_datetime(value: str) -> datetime:
    """Convert a GitHub timestamp to a UTC datetime."""
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).astimezone(timezone.utc)


def read_existing_rows() -> list[dict[str, str]]:
    """Read previously saved candidates."""
    if not CSV_PATH.exists():
        return []

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def create_candidate_id(rows: list[dict[str, str]]) -> str:
    """Create the next candidate ID."""
    return f"C{len(rows) + 1:03d}"


def evaluate_repository(
    repository_data: dict,
) -> tuple[str, str]:
    """Evaluate basic technical inclusion conditions."""
    reasons: list[str] = []

    created_at = parse_github_datetime(
        repository_data["created_at"]
    )

    pushed_at = parse_github_datetime(
        repository_data["pushed_at"]
    )

    if repository_data.get("fork", False):
        reasons.append("Repository is a fork")

    if repository_data.get("archived", False):
        reasons.append("Repository is archived")

    if repository_data.get("disabled", False):
        reasons.append("Repository is disabled")

    if repository_data.get("is_template", False):
        reasons.append("Repository is a template")

    if created_at >= OBSERVATION_START:
        reasons.append(
            "Repository was created after the observation window started"
        )

    if pushed_at < OBSERVATION_START:
     reasons.append(
        "Repository has no push activity on or after "
        "the observation-window start"
    )

    if reasons:
        return "exclude", "; ".join(reasons)

    return "review", "Technical checks passed; inspect README manually"


def save_candidate(row: dict[str, str]) -> None:
    """Append one repository candidate to the CSV file."""
    CSV_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_exists = CSV_PATH.exists()

    with CSV_PATH.open(
        "a",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def main() -> None:
    """Collect repository candidates until the user finishes."""
    token = (
        os.getenv("GitHub_Token")
        or os.getenv("GITHUB_TOKEN")
    )

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    print("GitHub Public Repository Pilot")
    print("--------------------------------")
    print("Paste one repository URL at a time.")
    print("Press Enter without a URL when finished.\n")

    while True:
        repository_url = input(
            "Repository URL: "
        ).strip()

        if not repository_url:
            print("\nCandidate collection finished.")
            print(f"Saved file: {CSV_PATH}")
            break

        discovery_group = input(
            "Discovery group "
            "(startup/saas/mvp/prototype/web-application): "
        ).strip().lower()

        try:
            owner, repository = parse_github_url(
                repository_url
            )

            existing_rows = read_existing_rows()

            duplicate = any(
                row.get("owner", "").lower() == owner.lower()
                and row.get("repository", "").lower()
                == repository.lower()
                for row in existing_rows
            )

            if duplicate:
                print(
                    "This repository is already in the CSV file.\n"
                )
                continue

            api_url = (
                f"https://api.github.com/repos/"
                f"{owner}/{repository}"
            )

            response = requests.get(
                api_url,
                headers=headers,
                timeout=30,
            )

            response.raise_for_status()
            repository_data = response.json()

            technical_status, technical_reason = (
                evaluate_repository(repository_data)
            )

            row = {
                "candidate_id": create_candidate_id(
                    existing_rows
                ),
                "owner": repository_data["owner"]["login"],
                "repository": repository_data["name"],
                "repository_url": repository_data["html_url"],
                "discovery_group": discovery_group,
                "primary_language": (
                    repository_data.get("language") or ""
                ),
                "created_at": repository_data["created_at"],
                "pushed_at": repository_data["pushed_at"],
                "is_fork": str(
                    repository_data.get("fork", False)
                ).lower(),
                "is_archived": str(
                    repository_data.get("archived", False)
                ).lower(),
                "is_disabled": str(
                    repository_data.get("disabled", False)
                ).lower(),
                "is_template": str(
                    repository_data.get("is_template", False)
                ).lower(),
                "description": (
                    repository_data.get("description") or ""
                ),
                "technical_status": technical_status,
                "technical_reason": technical_reason,
                "manual_status": "",
                "manual_reason": "",
            }

            save_candidate(row)

            print(
                f"\nSaved: {row['candidate_id']} "
                f"{owner}/{repository}"
            )
            print(
                f"Language: {row['primary_language']}"
            )
            print(
                f"Technical status: {technical_status}"
            )
            print(
                f"Reason: {technical_reason}\n"
            )

        except requests.HTTPError as error:
            print(
                f"GitHub could not retrieve this repository: "
                f"{error}\n"
            )

        except requests.RequestException as error:
            print(
                f"Connection error: {error}\n"
            )

        except ValueError as error:
            print(f"Invalid URL: {error}\n")


if __name__ == "__main__":
    main()