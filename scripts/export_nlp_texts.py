"""Export real repository text from PostgreSQL for manual NLP labelling."""

from __future__ import annotations

import csv
import os
import random
import re
from collections import defaultdict
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT_ROOT / "data" / "pilot_repository_candidates.csv"
OUTPUT = PROJECT_ROOT / "data" / "nlp_gold_standard.csv"

TARGET_REPOSITORIES = {"P001", "P002", "P003", "P004", "P005"}
ROWS_PER_REPOSITORY = 21
RANDOM_SEED = 42


def clean_text(value: object) -> str:
    """Convert text to one clean line."""
    text = "" if value is None else str(value)
    return re.sub(r"\s+", " ", text).strip()


def load_pilot_manifest() -> list[dict[str, str]]:
    """Read P001-P005 and their real repository names from the private manifest."""
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST}")

    with MANIFEST.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    selected = []
    for row in rows:
        sample_id = clean_text(row.get("sample_id"))
        if sample_id not in TARGET_REPOSITORIES:
            continue

        owner = clean_text(row.get("owner"))
        repository = clean_text(
            row.get("repository")
            or row.get("repo")
            or row.get("name")
        )

        if owner and repository:
            selected.append(
                {
                    "sample_id": sample_id,
                    "owner": owner,
                    "repository": repository,
                }
            )

    found = {row["sample_id"] for row in selected}
    missing = sorted(TARGET_REPOSITORIES - found)

    if missing:
        raise ValueError(
            "The manifest does not contain owner/repository details for: "
            + ", ".join(missing)
        )

    return sorted(selected, key=lambda row: row["sample_id"])


def connect_to_database() -> psycopg.Connection:
    """Create a PostgreSQL connection from .env values."""
    load_dotenv(PROJECT_ROOT / ".env")

    database = os.getenv("DB_NAME") or os.getenv("DB_DATABASE")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")

    missing = [
        name
        for name, value in {
            "DB_NAME/DB_DATABASE": database,
            "DB_USER": user,
            "DB_PASSWORD": password,
        }.items()
        if not value
    ]

    if missing:
        raise ValueError(
            "Missing database settings in .env: " + ", ".join(missing)
        )

    return psycopg.connect(
        dbname=database,
        user=user,
        password=password,
        host=host,
        port=port,
    )


def get_repository_id(
    connection: psycopg.Connection,
    owner: str,
    repository: str,
) -> int:
    """Find the database repository ID."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT id
            FROM repositories
            WHERE LOWER(owner) = LOWER(%s)
              AND LOWER(name) = LOWER(%s)
            LIMIT 1
            """,
            (owner, repository),
        )
        row = cursor.fetchone()

    if row is None:
        raise ValueError(
            f"Repository not found in PostgreSQL: {owner}/{repository}"
        )

    return int(row[0])


def fetch_repository_texts(
    connection: psycopg.Connection,
    repository_id: int,
) -> list[dict[str, str]]:
    """Collect text from commits, issues, comments, PRs and reviews."""
    queries = {
        "commit": """
            SELECT sha::text, message
            FROM commits
            WHERE repository_id = %s
              AND NULLIF(TRIM(message), '') IS NOT NULL
        """,
        "issue": """
            SELECT issue_number::text,
                   CONCAT_WS(' ', NULLIF(TRIM(title), ''), NULLIF(TRIM(body), ''))
            FROM issues
            WHERE repository_id = %s
              AND NULLIF(
                    TRIM(CONCAT_WS(' ', title, body)),
                    ''
                  ) IS NOT NULL
        """,
        "issue_comment": """
            SELECT COALESCE(ic.github_comment_id::text, ic.id::text),
                   ic.body
            FROM issue_comments AS ic
            JOIN issues AS i
              ON i.id = ic.issue_id
            WHERE i.repository_id = %s
              AND NULLIF(TRIM(ic.body), '') IS NOT NULL
        """,
        "pull_request": """
            SELECT pr_number::text,
                   CONCAT_WS(' ', NULLIF(TRIM(title), ''), NULLIF(TRIM(body), ''))
            FROM pull_requests
            WHERE repository_id = %s
              AND NULLIF(
                    TRIM(CONCAT_WS(' ', title, body)),
                    ''
                  ) IS NOT NULL
        """,
        "pull_request_review": """
            SELECT COALESCE(prr.github_review_id::text, prr.id::text),
                   prr.body
            FROM pull_request_reviews AS prr
            JOIN pull_requests AS pr
              ON pr.id = prr.pull_request_id
            WHERE pr.repository_id = %s
              AND NULLIF(TRIM(prr.body), '') IS NOT NULL
        """,
    }

    records: list[dict[str, str]] = []

    with connection.cursor() as cursor:
        for artifact_type, query in queries.items():
            cursor.execute(query, (repository_id,))

            for artifact_id, text in cursor.fetchall():
                cleaned = clean_text(text)
                if cleaned:
                    records.append(
                        {
                            "artifact_type": artifact_type,
                            "artifact_id": clean_text(artifact_id),
                            "text": cleaned,
                        }
                    )

    unique = {}
    for record in records:
        key = record["text"].lower()
        unique.setdefault(key, record)

    return list(unique.values())


def choose_sample(
    records: list[dict[str, str]],
    sample_size: int,
    random_generator: random.Random,
) -> list[dict[str, str]]:
    """Take a reproducible, reasonably diverse sample."""
    by_type: dict[str, list[dict[str, str]]] = defaultdict(list)

    for record in records:
        by_type[record["artifact_type"]].append(record)

    selected: list[dict[str, str]] = []
    selected_keys: set[tuple[str, str]] = set()

    artifact_types = [
        "commit",
        "issue",
        "issue_comment",
        "pull_request",
        "pull_request_review",
    ]

    quota = max(1, sample_size // len(artifact_types))

    for artifact_type in artifact_types:
        candidates = by_type.get(artifact_type, [])
        random_generator.shuffle(candidates)

        for record in candidates[:quota]:
            selected.append(record)
            selected_keys.add(
                (record["artifact_type"], record["artifact_id"])
            )

    remaining = [
        record
        for record in records
        if (record["artifact_type"], record["artifact_id"])
        not in selected_keys
    ]

    random_generator.shuffle(remaining)
    selected.extend(remaining[: max(0, sample_size - len(selected))])

    return selected[:sample_size]


def main() -> None:
    random_generator = random.Random(RANDOM_SEED)
    pilot_repositories = load_pilot_manifest()
    output_rows: list[dict[str, str]] = []

    with connect_to_database() as connection:
        for repository in pilot_repositories:
            sample_id = repository["sample_id"]

            repository_id = get_repository_id(
                connection,
                repository["owner"],
                repository["repository"],
            )

            records = fetch_repository_texts(
                connection,
                repository_id,
            )

            sample = choose_sample(
                records,
                ROWS_PER_REPOSITORY,
                random_generator,
            )

            for record in sample:
                output_rows.append(
                    {
                        "sample_id": sample_id,
                        "artifact_type": record["artifact_type"],
                        "artifact_id": record["artifact_id"],
                        "text": record["text"],
                        "final_label": "",
                    }
                )

            print(
                f"{sample_id}: exported {len(sample)} "
                f"of {len(records)} available text artefacts"
            )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "sample_id",
                "artifact_type",
                "artifact_id",
                "text",
                "final_label",
            ],
        )
        writer.writeheader()
        writer.writerows(output_rows)

    print("-" * 70)
    print(f"Created: {OUTPUT}")
    print(f"Rows exported: {len(output_rows)}")
    print("Next step: open the CSV in Excel and fill only final_label.")


if __name__ == "__main__":
    main()