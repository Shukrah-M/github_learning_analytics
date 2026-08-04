"""Generate and display experimentation-intensity scores."""

from __future__ import annotations

import argparse

from analytics.experimentation_score import (
    calculate_experimentation_scores,
)
from analytics.repository_analysis import (
    analyse_repository,
)


# Replace these example IDs with the actual database IDs.
REPOSITORIES = {
    "controlled_regular": 1,
    "controlled_burst": 2,
    "controlled_refinement": 3,
    "controlled_collaboration": 4,
    "controlled_low_activity": 5,
    "P001": 7,
    "P002": 8,
    "P003": 9,
    "P004": 10,
    "P005": 11,
}


def format_score(
    value: float | int | None,
) -> str:
    """Format score values consistently."""
    if value is None:
        return "N/A"

    return f"{float(value):.2f}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Display the experimentation-intensity "
            "score for a repository."
        )
    )

    parser.add_argument(
        "--repository",
        default="P001",
        choices=sorted(REPOSITORIES),
        help="Repository label to display.",
    )

    arguments = parser.parse_args()

    print(
        "Calculating behavioural metrics "
        "from PostgreSQL..."
    )

    repository_metrics = {}

    for label, repository_id in REPOSITORIES.items():
        repository_metrics[label] = analyse_repository(
            repository_id
        )

    scores = calculate_experimentation_scores(
        repository_metrics
    )

    selected = scores[arguments.repository]

    print()
    print("=" * 62)
    print("EXPERIMENTATION INTENSITY SCORE")
    print("=" * 62)
    print(
        f"Repository: {arguments.repository}"
    )
    print("-" * 62)

    print(
        "Engagement score:       "
        f"{format_score(selected['engagement_score'])}"
    )

    print(
        "Regularity score:       "
        f"{format_score(selected['regularity_score'])}"
    )

    print(
        "Refinement score:       "
        f"{format_score(selected['refinement_score'])}"
    )

    print(
        "Integration score:      "
        f"{format_score(selected['integration_score'])}"
    )

    print("-" * 62)

    print(
        "Applicable dimensions:  "
        f"{selected['applicable_dimensions']}"
    )

    final_score = selected[
        "experimentation_intensity_score"
    ]

    if final_score is None:
        final_display = "N/A"
    else:
        final_display = (
            f"{float(final_score):.2f} / 100"
        )

    print(
        "Experimentation intensity score: "
        f"{final_display}"
    )

    print("=" * 62)
    print(
        "Score generated successfully from "
        "repository activity stored in PostgreSQL."
    )


if __name__ == "__main__":
    main()