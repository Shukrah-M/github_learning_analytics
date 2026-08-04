"""Review pilot repository candidates without using Excel."""

from __future__ import annotations

import csv
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "pilot_repository_candidates.csv"
)


def load_candidates() -> tuple[list[str], list[dict[str, str]]]:
    """Load candidate repositories from the CSV file."""
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Candidate file not found: {CSV_PATH}"
        )

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise RuntimeError(
                "The CSV file does not contain a header."
            )

        return list(reader.fieldnames), list(reader)


def save_candidates(
    fieldnames: list[str],
    candidates: list[dict[str, str]],
) -> None:
    """Save reviewed candidates back to the CSV file."""
    with CSV_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(candidates)


def main() -> None:
    """Review each candidate interactively."""
    fieldnames, candidates = load_candidates()

    print("\nPilot Repository Manual Review")
    print("--------------------------------")

    for candidate in candidates:
        technical_status = (
            candidate.get("technical_status", "")
            .strip()
            .lower()
        )

        manual_status = (
            candidate.get("manual_status", "")
            .strip()
            .lower()
        )

        if technical_status != "review":
            continue

        if manual_status in {"include", "exclude"}:
            continue

        print("\n========================================")
        print(
            f"Candidate: "
            f"{candidate.get('candidate_id', '')}"
        )
        print(
            f"Repository: "
            f"{candidate.get('owner', '')}/"
            f"{candidate.get('repository', '')}"
        )
        print(
            f"Discovery group: "
            f"{candidate.get('discovery_group', '')}"
        )
        print(
            f"Language: "
            f"{candidate.get('primary_language', '')}"
        )
        print(
            f"Description: "
            f"{candidate.get('description', '')}"
        )
        print(
            f"URL: "
            f"{candidate.get('repository_url', '')}"
        )
        print("========================================")

        open_repository = input(
            "Open this repository in your browser? (y/n): "
        ).strip().lower()

        if open_repository == "y":
            webbrowser.open(
                candidate.get("repository_url", "")
            )

        print("\nRead the first part of the README.")
        print("Enter:")
        print("  i = include")
        print("  e = exclude")
        print("  s = skip for now")

        decision = input(
            "Your decision: "
        ).strip().lower()

        if decision == "i":
            candidate["manual_status"] = "include"

            reason = input(
                "Reason for inclusion: "
            ).strip()

            candidate["manual_reason"] = (
                reason
                or "Functional application with a clear purpose"
            )

        elif decision == "e":
            candidate["manual_status"] = "exclude"

            reason = input(
                "Reason for exclusion: "
            ).strip()

            candidate["manual_reason"] = (
                reason
                or "Repository does not meet the inclusion criteria"
            )

        else:
            print("Candidate skipped.")
            continue

        save_candidates(
            fieldnames,
            candidates,
        )

        print(
            f"Saved decision: "
            f"{candidate['manual_status']}"
        )

    print("\nManual review completed.")
    print(f"Updated file: {CSV_PATH}")


if __name__ == "__main__":
    main()