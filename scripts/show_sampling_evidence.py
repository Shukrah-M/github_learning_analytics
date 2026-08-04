from __future__ import annotations

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_FILE = (
    PROJECT_ROOT
    / "data"
    / "pilot_repository_candidates.csv"
)


def normalise(value: str | None) -> str:
    """Return a clean lowercase value."""
    return (value or "").strip().lower()


def count_matching(rows, column, accepted_values):
    """Count rows whose column contains one of the accepted values."""
    accepted = {
        normalise(value)
        for value in accepted_values
    }

    return sum(
        normalise(row.get(column)) in accepted
        for row in rows
    )


def main() -> None:
    """Print a pseudonymised sampling-process summary."""
    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"Candidate file not found: {CSV_FILE}"
        )

    with CSV_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    manually_included = [
        row
        for row in rows
        if normalise(row.get("manual_status"))
        in {"include", "included"}
    ]

    technically_eligible = [
        row
        for row in rows
        if normalise(row.get("pilot_eligibility"))
        in {"eligible", "include", "included"}
    ]

    selected = [
        row
        for row in rows
        if normalise(row.get("pilot_selection"))
        == "selected"
    ]

    selected.sort(
        key=lambda row: row.get("sample_id", "")
    )

    print("=" * 72)
    print("PUBLIC REPOSITORY IDENTIFICATION AND SELECTION PROCEDURE")
    print("=" * 72)

    print("\nSTAGE 1 — CANDIDATE IDENTIFICATION")
    print(f"Candidate repositories recorded: {len(rows)}")
    print(
        "Source: GitHub topic, language and "
        "repository-purpose searches"
    )

    print("\nSTAGE 2 — MANUAL INITIAL SCREENING")
    print(
        "Repositories retained after README and "
        f"purpose review: {len(manually_included)}"
    )
    print(
        "Excluded: tutorials, templates, resource lists, "
        "archives and unclear projects"
    )

    print("\nSTAGE 3 — TECHNICAL AND ACTIVITY CHECK")
    print(
        "Repositories satisfying technical and "
        f"activity criteria: {len(technically_eligible)}"
    )
    print(
        "Checks: public, non-fork, active, created before "
        "window and at least five window commits"
    )

    print("\nSTAGE 4 — PSEUDONYMISATION AND FINAL SELECTION")
    print(f"Repositories selected for the pilot: {len(selected)}")
    print("Repository identities replaced with P001–P005")

    print("\nFINAL PSEUDONYMISED PILOT SAMPLE")
    print("-" * 72)

    header = (
        f"{'Sample':<9}"
        f"{'Category':<20}"
        f"{'Commits':>10}"
        f"{'Issues':>10}"
        f"{'PRs':>10}"
    )

    print(header)
    print("-" * 72)

    for row in selected:
        print(
            f"{row.get('sample_id', ''):<9}"
            f"{row.get('discovery_group', ''):<20}"
            f"{row.get('window_commits', ''):>10}"
            f"{row.get('window_issues', ''):>10}"
            f"{row.get('window_pull_requests', ''):>10}"
        )

    print("-" * 72)
    print(
        "Observation window: "
        "02 January 2026 to 01 July 2026"
    )
    print(
        "Selection file: "
        "data/pilot_repository_candidates.csv"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()