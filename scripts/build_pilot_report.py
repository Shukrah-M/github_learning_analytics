"""Build a pseudonymised report for the five public pilot repositories."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from utils.observation_window import (
    OBSERVATION_END,
    OBSERVATION_START,
)


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CANDIDATE_FILE = (
    PROJECT_ROOT
    / "data"
    / "pilot_repository_candidates.csv"
)

RESULTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "pilot_extraction_results.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "docs"
    / "public_repository_pilot_results.md"
)


def safe_integer(value: str | None) -> int | None:
    """Convert a CSV value to an integer."""
    if value is None or not value.strip():
        return None

    try:
        return int(value)
    except ValueError:
        return None


def database_connection():
    """Create the PostgreSQL connection."""
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def load_selected_repositories() -> list[dict[str, str]]:
    """Read the five selected pilot repositories."""
    if not CANDIDATE_FILE.exists():
        raise FileNotFoundError(
            f"Candidate file not found: {CANDIDATE_FILE}"
        )

    with CANDIDATE_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    selected = [
        row
        for row in rows
        if row.get("pilot_selection", "").strip().lower()
        == "selected"
    ]

    selected.sort(
        key=lambda row: row.get("sample_id", "")
    )

    if len(selected) != 5:
        raise RuntimeError(
            f"Expected 5 selected repositories, found {len(selected)}."
        )

    return selected


def count_records(
    cursor,
    query: str,
    repository_id: int,
) -> int:
    """Run a count query for one repository."""
    cursor.execute(
        query,
        (repository_id,),
    )

    return cursor.fetchone()[0]


def count_outside_window(
    cursor,
    query: str,
    repository_id: int,
) -> int:
    """Count records outside the fixed observation window."""
    cursor.execute(
        query,
        (
            repository_id,
            OBSERVATION_START,
            OBSERVATION_END,
        ),
    )

    return cursor.fetchone()[0]


def build_repository_result(
    cursor,
    candidate: dict[str, str],
) -> dict[str, str | int]:
    """Build one repository's pilot result."""
    owner = candidate["owner"].strip()
    repository = candidate["repository"].strip()

    cursor.execute(
        """
        SELECT id
        FROM repositories
        WHERE LOWER(owner) = LOWER(%s)
          AND LOWER(name) = LOWER(%s)
        ORDER BY id DESC
        LIMIT 1;
        """,
        (owner, repository),
    )

    repository_row = cursor.fetchone()

    if repository_row is None:
        return {
            "sample_id": candidate["sample_id"],
            "category": candidate["discovery_group"],
            "repository_id": "",
            "commits": 0,
            "issues": 0,
            "issue_comments": 0,
            "pull_requests": 0,
            "pull_request_reviews": 0,
            "outside_window_records": 0,
            "counts_match": "No",
            "result": "Fail",
            "notes": "Repository was not found in PostgreSQL",
        }

    repository_id = repository_row[0]

    commits = count_records(
        cursor,
        """
        SELECT COUNT(*)
        FROM commits
        WHERE repository_id = %s;
        """,
        repository_id,
    )

    issues = count_records(
        cursor,
        """
        SELECT COUNT(*)
        FROM issues
        WHERE repository_id = %s;
        """,
        repository_id,
    )

    issue_comments = count_records(
        cursor,
        """
        SELECT COUNT(*)
        FROM issue_comments ic
        JOIN issues i
          ON i.id = ic.issue_id
        WHERE i.repository_id = %s;
        """,
        repository_id,
    )

    pull_requests = count_records(
        cursor,
        """
        SELECT COUNT(*)
        FROM pull_requests
        WHERE repository_id = %s;
        """,
        repository_id,
    )

    pull_request_reviews = count_records(
        cursor,
        """
        SELECT COUNT(*)
        FROM pull_request_reviews prr
        JOIN pull_requests pr
          ON pr.id = prr.pull_request_id
        WHERE pr.repository_id = %s;
        """,
        repository_id,
    )

    outside_commits = count_outside_window(
        cursor,
        """
        SELECT COUNT(*)
        FROM commits
        WHERE repository_id = %s
          AND (
              committed_at < %s
              OR committed_at >= %s
          );
        """,
        repository_id,
    )

    outside_issues = count_outside_window(
        cursor,
        """
        SELECT COUNT(*)
        FROM issues
        WHERE repository_id = %s
          AND (
              created_at < %s
              OR created_at >= %s
          );
        """,
        repository_id,
    )

    outside_comments = count_outside_window(
        cursor,
        """
        SELECT COUNT(*)
        FROM issue_comments ic
        JOIN issues i
          ON i.id = ic.issue_id
        WHERE i.repository_id = %s
          AND (
              ic.created_at < %s
              OR ic.created_at >= %s
          );
        """,
        repository_id,
    )

    outside_pull_requests = count_outside_window(
        cursor,
        """
        SELECT COUNT(*)
        FROM pull_requests
        WHERE repository_id = %s
          AND (
              created_at < %s
              OR created_at >= %s
          );
        """,
        repository_id,
    )

    outside_reviews = count_outside_window(
        cursor,
        """
        SELECT COUNT(*)
        FROM pull_request_reviews prr
        JOIN pull_requests pr
          ON pr.id = prr.pull_request_id
        WHERE pr.repository_id = %s
          AND (
              prr.submitted_at < %s
              OR prr.submitted_at >= %s
          );
        """,
        repository_id,
    )

    outside_total = (
        outside_commits
        + outside_issues
        + outside_comments
        + outside_pull_requests
        + outside_reviews
    )

    expected_commits = safe_integer(
        candidate.get("window_commits")
    )

    expected_issues = safe_integer(
        candidate.get("window_issues")
    )

    expected_pull_requests = safe_integer(
        candidate.get("window_pull_requests")
    )

    counts_match = (
        expected_commits == commits
        and expected_issues == issues
        and expected_pull_requests == pull_requests
    )

    passed = (
        counts_match
        and outside_total == 0
    )

    notes = (
        "Extraction counts matched and all records were inside the window"
        if passed
        else "Review count differences or observation-window records"
    )

    return {
        "sample_id": candidate["sample_id"],
        "category": candidate["discovery_group"],
        "repository_id": repository_id,
        "commits": commits,
        "issues": issues,
        "issue_comments": issue_comments,
        "pull_requests": pull_requests,
        "pull_request_reviews": pull_request_reviews,
        "outside_window_records": outside_total,
        "counts_match": "Yes" if counts_match else "No",
        "result": "Pass" if passed else "Check",
        "notes": notes,
    }


def save_csv(results: list[dict]) -> None:
    """Save pseudonymised pilot results as CSV."""
    RESULTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "sample_id",
        "category",
        "repository_id",
        "commits",
        "issues",
        "issue_comments",
        "pull_requests",
        "pull_request_reviews",
        "outside_window_records",
        "counts_match",
        "result",
        "notes",
    ]

    with RESULTS_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(results)


def save_markdown(results: list[dict]) -> None:
    """Create the dissertation pilot-results document."""
    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    table_rows = []

    for result in results:
        table_rows.append(
            "| {sample_id} | {category} | {commits} | "
            "{issues} | {issue_comments} | {pull_requests} | "
            "{pull_request_reviews} | {outside_window_records} | "
            "{result_status} |".format(
                sample_id=result["sample_id"],
                category=result["category"],
                commits=result["commits"],
                issues=result["issues"],
                issue_comments=result["issue_comments"],
                pull_requests=result["pull_requests"],
                pull_request_reviews=result[
                    "pull_request_reviews"
                ],
                outside_window_records=result[
                    "outside_window_records"
                ],
                result_status=result["result"],
            )
        )

    passed_count = sum(
        result["result"] == "Pass"
        for result in results
    )

    report = f"""# Public Repository Pilot Results

## Observation window

- Start: {OBSERVATION_START.isoformat()}
- End: {OBSERVATION_END.isoformat()}
- Duration: 180 days
- Start boundary: inclusive
- End boundary: exclusive

## Extraction results

| Sample | Category | Commits | Issues | Comments | Pull requests | Reviews | Outside-window records | Result |
|---|---|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(table_rows)}

## Pilot outcome

Repositories passing automatic extraction validation: {passed_count}/5.

A repository passed when its extracted commit, issue and pull-request
counts matched the preliminary activity check and no retained records
fell outside the fixed observation window.

The repositories are reported using pseudonymous identifiers P001 to
P005. Actual owner and repository names remain in the private research
manifest.

## Conclusion

The pilot evaluated whether the extraction pipeline could collect and
store activity from naturally occurring public GitHub repositories
using a consistent 180-day observation period.

The pilot results should be reviewed before scaling the collection
workflow to the complete public repository sample.
"""

    REPORT_FILE.write_text(
        report,
        encoding="utf-8",
    )


def main() -> None:
    """Generate the pilot validation report."""
    candidates = load_selected_repositories()
    results = []

    with database_connection() as connection:
        with connection.cursor() as cursor:
            for candidate in candidates:
                result = build_repository_result(
                    cursor,
                    candidate,
                )

                results.append(result)

                print(
                    f"{result['sample_id']}: "
                    f"{result['result']} | "
                    f"commits={result['commits']} | "
                    f"issues={result['issues']} | "
                    f"PRs={result['pull_requests']} | "
                    f"outside={result['outside_window_records']}"
                )

    save_csv(results)
    save_markdown(results)

    print("\nPilot report completed.")
    print(f"CSV: {RESULTS_FILE}")
    print(f"Report: {REPORT_FILE}")


if __name__ == "__main__":
    main()