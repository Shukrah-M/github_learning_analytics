"""Automatically select five balanced pilot repositories."""

from __future__ import annotations

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "pilot_repository_candidates.csv"
)

REQUIRED_GROUPS = [
    ("mvp", "P001"),
    ("saas", "P002"),
    ("web-development", "P003"),
    ("prototype", "P004"),
    ("startup", "P005"),
]


def normalise_group(value: str) -> str:
    """Convert different group labels to consistent values."""
    cleaned = (
        value.strip()
        .lower()
        .replace("_", "-")
        .replace(" ", "-")
    )

    aliases = {
        "web-application": "web-development",
        "web-app": "web-development",
        "web-development": "web-development",
        "webapplication": "web-development",
        "prototype": "prototype",
        "mvp": "mvp",
        "saas": "saas",
        "startup": "startup",
    }

    return aliases.get(cleaned, cleaned)


def safe_integer(value: str) -> int:
    """Convert a CSV value to an integer safely."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def load_rows() -> tuple[list[str], list[dict[str, str]]]:
    """Load repository candidates from the CSV file."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Candidate CSV not found: {CSV_PATH}"
        )

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise RuntimeError(
                "The candidate CSV does not contain a header."
            )

        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    for column in ["pilot_selection", "sample_id"]:
        if column not in fieldnames:
            fieldnames.append(column)

    return fieldnames, rows


def save_rows(
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    """Save the completed pilot selection."""
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


def is_eligible(row: dict[str, str]) -> bool:
    """Return True when a repository passed both review stages."""
    manual_status = (
        row.get("manual_status", "")
        .strip()
        .lower()
    )

    pilot_eligibility = (
        row.get("pilot_eligibility", "")
        .strip()
        .lower()
    )

    return (
        manual_status == "include"
        and pilot_eligibility == "eligible"
    )


def ranking_key(row: dict[str, str]) -> tuple[int, int, int, int]:
    """
    Rank repositories by useful pilot activity.

    Repositories with issues or pull requests are preferred.
    Commit count is used as the final tie-breaker.
    """
    commits = safe_integer(
        row.get("window_commits", "")
    )
    issues = safe_integer(
        row.get("window_issues", "")
    )
    pull_requests = safe_integer(
        row.get("window_pull_requests", "")
    )

    interaction_total = issues + pull_requests
    has_interaction = int(interaction_total > 0)

    return (
        has_interaction,
        interaction_total,
        pull_requests,
        commits,
    )


def main() -> None:
    """Select one eligible repository from each required group."""
    fieldnames, rows = load_rows()

    # Remove previous pilot assignments before recalculating.
    for row in rows:
        row["pilot_selection"] = ""
        row["sample_id"] = ""

    selected_rows: list[dict[str, str]] = []
    missing_groups: list[str] = []

    for required_group, sample_id in REQUIRED_GROUPS:
        group_candidates = [
            row
            for row in rows
            if is_eligible(row)
            and normalise_group(
                row.get("discovery_group", "")
            ) == required_group
        ]

        group_candidates.sort(
            key=ranking_key,
            reverse=True,
        )

        if not group_candidates:
            missing_groups.append(required_group)
            continue

        selected = group_candidates[0]

        selected["pilot_selection"] = "selected"
        selected["sample_id"] = sample_id

        selected_rows.append(selected)

    selected_candidate_ids = {
        row.get("candidate_id", "")
        for row in selected_rows
    }

    # Mark other eligible repositories as reserves.
    for row in rows:
        candidate_id = row.get("candidate_id", "")

        if (
            is_eligible(row)
            and candidate_id not in selected_candidate_ids
        ):
            row["pilot_selection"] = "reserve"

    save_rows(fieldnames, rows)

    print("\nAutomatic Pilot Selection")
    print("--------------------------------")

    for row in selected_rows:
        print(
            f"{row['sample_id']}: "
            f"{row.get('candidate_id', '')} | "
            f"{row.get('discovery_group', '')} | "
            f"{row.get('owner', '')}/"
            f"{row.get('repository', '')} | "
            f"commits={row.get('window_commits', '')} | "
            f"issues={row.get('window_issues', '')} | "
            f"PRs={row.get('window_pull_requests', '')}"
        )

    if missing_groups:
        print("\nSelection is incomplete.")
        print(
            "No eligible repository was found for: "
            + ", ".join(missing_groups)
        )
        print(
            "Add or review another candidate for "
            "the missing group."
        )
    else:
        print("\nFive pilot repositories selected successfully.")

    print(f"\nUpdated CSV: {CSV_PATH}")


if __name__ == "__main__":
    main()