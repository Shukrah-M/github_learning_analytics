"""CSV report generation for the dashboard's export buttons."""

from __future__ import annotations

import csv
import io
from typing import Any


def build_repository_report_csv(
    repository: Any,
    metrics: dict[str, Any],
    score: dict[str, Any],
    nlp_result: dict[str, Any] | None,
) -> str:
    """Build a flat CSV report for one repository's analysis results."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["section", "metric", "value"])

    writer.writerow(["repository", "owner", repository.owner])
    writer.writerow(["repository", "name", repository.name])
    writer.writerow(["repository", "language", repository.language or ""])
    writer.writerow(
        ["repository", "description", repository.description or ""]
    )

    writer.writerow(
        [
            "experimentation_score",
            "experimentation_intensity_score",
            score.get("experimentation_intensity_score"),
        ]
    )
    writer.writerow(
        ["experimentation_score", "engagement", score.get("engagement_score")]
    )
    writer.writerow(
        ["experimentation_score", "regularity", score.get("regularity_score")]
    )
    writer.writerow(
        ["experimentation_score", "refinement", score.get("refinement_score")]
    )
    writer.writerow(
        ["experimentation_score", "integration", score.get("integration_score")]
    )

    for key, value in metrics.items():
        writer.writerow(["behavioural_metrics", key, value])

    if nlp_result:
        writer.writerow(
            [
                "nlp_classification",
                "learning_quality_indicator_percent",
                nlp_result.get("learning_quality_indicator"),
            ]
        )

        for label, count in nlp_result.get(
            "category_distribution", {}
        ).items():
            writer.writerow(
                ["nlp_classification", f"category_{label}", count]
            )

    return buffer.getvalue()


def build_all_repositories_summary_csv(
    rows: list[dict[str, Any]],
) -> str:
    """Build a one-row-per-repository summary CSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(
        [
            "owner",
            "name",
            "language",
            "commit_frequency_per_week",
            "active_day_ratio",
            "issue_closure_rate",
            "pull_request_merge_rate",
            "experimentation_intensity_score",
        ]
    )

    for row in rows:
        repository = row["repository"]
        metrics = row["metrics"]
        score = row["score"]

        writer.writerow(
            [
                repository.owner,
                repository.name,
                repository.language or "",
                metrics.get("commit_frequency_per_week"),
                metrics.get("active_day_ratio"),
                metrics.get("issue_closure_rate"),
                metrics.get("pull_request_merge_rate"),
                score.get("experimentation_intensity_score"),
            ]
        )

    return buffer.getvalue()
