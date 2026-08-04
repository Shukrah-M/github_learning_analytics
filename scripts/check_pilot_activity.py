"""Check pilot repository activity within the fixed observation window."""

from __future__ import annotations

import csv
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "pilot_repository_candidates.csv"
)

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

ADDITIONAL_COLUMNS = [
    "window_commits",
    "window_issues",
    "window_pull_requests",
    "pilot_eligibility",
    "pilot_reason",
    "pilot_selection",
    "sample_id",
]


def parse_datetime(value: str) -> datetime:
    """Convert a GitHub timestamp to UTC."""
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).astimezone(timezone.utc)


def load_rows() -> tuple[list[str], list[dict[str, str]]]:
    """Load the pilot-candidate CSV."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV file not found: {CSV_PATH}"
        )

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise RuntimeError(
                "The CSV file has no header."
            )

        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    for column in ADDITIONAL_COLUMNS:
        if column not in fieldnames:
            fieldnames.append(column)

    return fieldnames, rows


def save_rows(
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    """Save activity results to the CSV."""
    with CSV_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


def create_session() -> requests.Session:
    """Create an authenticated GitHub API session."""
    token = (
        os.getenv("GitHub_Token")
        or os.getenv("GITHUB_TOKEN")
    )

    session = requests.Session()

    session.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )

    if token:
        session.headers.update(
            {
                "Authorization": f"Bearer {token}",
            }
        )

    return session


def count_commits(
    session: requests.Session,
    owner: str,
    repository: str,
) -> int:
    """Count commits created within the observation window."""
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/commits"
    )

    page = 1
    total = 0

    while True:
        response = session.get(
            url,
            params={
                "since": OBSERVATION_START.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "until": OBSERVATION_END.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "per_page": 100,
                "page": page,
            },
            timeout=30,
        )

        if response.status_code == 409:
            return 0

        response.raise_for_status()

        records = response.json()
        total += len(records)

        if len(records) < 100:
            break

        page += 1

    return total


def count_created_records(
    session: requests.Session,
    owner: str,
    repository: str,
    endpoint: str,
) -> int:
    """Count issues or pull requests created in the window."""
    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repository}/{endpoint}"
    )

    page = 1
    total = 0
    reached_start_boundary = False

    while not reached_start_boundary:
        response = session.get(
            url,
            params={
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": 100,
                "page": page,
            },
            timeout=30,
        )

        response.raise_for_status()
        records = response.json()

        if not records:
            break

        for record in records:
            created_at = parse_datetime(
                record["created_at"]
            )

            if created_at >= OBSERVATION_END:
                continue

            if created_at < OBSERVATION_START:
                reached_start_boundary = True
                break

            # The GitHub issues endpoint also returns PRs.
            if (
                endpoint == "issues"
                and "pull_request" in record
            ):
                continue

            total += 1

        if len(records) < 100:
            break

        page += 1

    return total


def main() -> None:
    """Check all manually included pilot candidates."""
    fieldnames, rows = load_rows()
    session = create_session()

    included_rows = [
        row
        for row in rows
        if row.get(
            "manual_status",
            "",
        ).strip().lower() == "include"
    ]

    print("\nPilot Activity Check")
    print("--------------------------------")
    print(
        f"Repositories to check: {len(included_rows)}"
    )

    for index, row in enumerate(
        included_rows,
        start=1,
    ):
        owner = row["owner"].strip()
        repository = row["repository"].strip()
        candidate_id = row["candidate_id"].strip()

        print(
            f"\n[{index}/{len(included_rows)}] "
            f"Checking {candidate_id}: "
            f"{owner}/{repository}"
        )

        try:
            commits = count_commits(
                session,
                owner,
                repository,
            )

            issues = count_created_records(
                session,
                owner,
                repository,
                "issues",
            )

            pull_requests = count_created_records(
                session,
                owner,
                repository,
                "pulls",
            )

            row["window_commits"] = str(commits)
            row["window_issues"] = str(issues)
            row["window_pull_requests"] = str(
                pull_requests
            )

            if commits < 5:
                row["pilot_eligibility"] = "exclude"
                row["pilot_reason"] = (
                    "Fewer than five commits "
                    "during the observation window"
                )
            elif commits > 1000:
                row["pilot_eligibility"] = "reserve"
                row["pilot_reason"] = (
                    "Very high activity volume for "
                    "the initial pilot"
                )
            else:
                row["pilot_eligibility"] = "eligible"
                row["pilot_reason"] = (
                    "Meets the pilot activity requirement"
                )

            print(f"Commits: {commits}")
            print(f"Issues: {issues}")
            print(
                f"Pull requests: {pull_requests}"
            )
            print(
                f"Eligibility: "
                f"{row['pilot_eligibility']}"
            )

        except requests.HTTPError as error:
            row["pilot_eligibility"] = "error"
            row["pilot_reason"] = str(error)

            print(f"GitHub API error: {error}")

        except requests.RequestException as error:
            row["pilot_eligibility"] = "error"
            row["pilot_reason"] = str(error)

            print(f"Connection error: {error}")

        save_rows(fieldnames, rows)
        time.sleep(1)

    print("\n================================")
    print("Pilot activity summary")
    print("================================")

    for row in included_rows:
        print(
            f"{row.get('candidate_id', '')}: "
            f"{row.get('discovery_group', '')} | "
            f"commits={row.get('window_commits', '')} | "
            f"issues={row.get('window_issues', '')} | "
            f"PRs={row.get('window_pull_requests', '')} | "
            f"{row.get('pilot_eligibility', '')}"
        )

    print(
        "\nResults saved to: "
        f"{CSV_PATH}"
    )


if __name__ == "__main__":
    main()