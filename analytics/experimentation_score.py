"""Combine behavioural metrics and calculate experimentation-intensity scores."""

from __future__ import annotations

from statistics import mean
from typing import Any

from analytics.commit_metrics import calculate_commit_metrics
from analytics.issue_metrics import calculate_issue_metrics
from analytics.pull_request_metrics import (
    calculate_pull_request_metrics,
)


def calculate_behavioural_metrics(
    commits,
    issues,
    issue_comments,
    pull_requests,
    pull_request_reviews,
    observation_days=None,
):
    """
    Calculate all repository behavioural metrics.

    Use observation_days=None for controlled repositories.
    Use observation_days=180 for public repositories.
    """
    commit_metrics = calculate_commit_metrics(
        commits,
        observation_days=observation_days,
    )

    issue_metrics = calculate_issue_metrics(
        issues,
        issue_comments,
    )

    pull_request_metrics = calculate_pull_request_metrics(
        pull_requests,
        pull_request_reviews,
    )

    return {
        "commit_metrics": commit_metrics,
        "issue_metrics": issue_metrics,
        "pull_request_metrics": pull_request_metrics,
    }


def as_number(value: Any) -> float | None:
    """Convert a metric to float while preserving non-applicable values."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp_rate(value: Any) -> float | None:
    """Restrict an applicable rate to the range 0–1."""
    number = as_number(value)

    if number is None:
        return None

    return max(0.0, min(1.0, number))


def applicable_mean(
    values: list[float | None],
) -> float | None:
    """Calculate the mean of applicable metric values."""
    applicable = [
        value
        for value in values
        if value is not None
    ]

    if not applicable:
        return None

    return mean(applicable)


def normalise_metric(
    raw_values: dict[str, float | None],
    *,
    reverse: bool = False,
) -> dict[str, float | None]:
    """
    Apply min–max normalisation across repositories.

    When all applicable repositories contain the same value,
    assign 0.5 because the metric does not discriminate between
    repositories.
    """
    applicable = [
        value
        for value in raw_values.values()
        if value is not None
    ]

    if not applicable:
        return {
            repository: None
            for repository in raw_values
        }

    minimum = min(applicable)
    maximum = max(applicable)

    results: dict[str, float | None] = {}

    for repository, value in raw_values.items():
        if value is None:
            results[repository] = None
            continue

        if maximum == minimum:
            normalised = 0.5
        else:
            normalised = (
                value - minimum
            ) / (
                maximum - minimum
            )

        if reverse:
            normalised = 1.0 - normalised

        results[repository] = normalised

    return results


def calculate_experimentation_scores(
    repository_metrics: dict[str, dict[str, Any]],
) -> dict[str, dict[str, float | int | None]]:
    """
    Calculate experimentation-intensity scores for repositories.

    Required metric keys:
    - commit_frequency_per_week
    - active_day_ratio
    - commit_interval_std_days
    - longest_inactivity_gap_days
    - total_issues
    - issue_closure_rate
    - mean_comments_per_issue
    - mean_issue_resolution_days
    - total_pull_requests
    - pull_request_merge_rate
    - reviewed_pull_request_ratio
    - mean_pull_request_cycle_days
    """
    metric_names = [
        "commit_frequency_per_week",
        "commit_interval_std_days",
        "longest_inactivity_gap_days",
        "mean_comments_per_issue",
        "mean_issue_resolution_days",
        "mean_pull_request_cycle_days",
    ]

    raw_columns: dict[
        str,
        dict[str, float | None],
    ] = {}

    for metric_name in metric_names:
        raw_columns[metric_name] = {
            repository: as_number(
                metrics.get(metric_name)
            )
            for repository, metrics
            in repository_metrics.items()
        }

    commit_frequency = normalise_metric(
        raw_columns["commit_frequency_per_week"]
    )

    interval_regularity = normalise_metric(
        raw_columns["commit_interval_std_days"],
        reverse=True,
    )

    inactivity_regularity = normalise_metric(
        raw_columns["longest_inactivity_gap_days"],
        reverse=True,
    )

    comments_score = normalise_metric(
        raw_columns["mean_comments_per_issue"]
    )

    resolution_score = normalise_metric(
        raw_columns["mean_issue_resolution_days"],
        reverse=True,
    )

    cycle_score = normalise_metric(
        raw_columns["mean_pull_request_cycle_days"],
        reverse=True,
    )

    results: dict[
        str,
        dict[str, float | int | None],
    ] = {}

    for repository, metrics in repository_metrics.items():
        engagement = applicable_mean(
            [
                commit_frequency[repository],
                clamp_rate(
                    metrics.get("active_day_ratio")
                ),
            ]
        )

        regularity = applicable_mean(
            [
                interval_regularity[repository],
                inactivity_regularity[repository],
            ]
        )

        total_issues = int(
            metrics.get("total_issues") or 0
        )

        if total_issues > 0:
            refinement = applicable_mean(
                [
                    clamp_rate(
                        metrics.get(
                            "issue_closure_rate"
                        )
                    ),
                    comments_score[repository],
                    resolution_score[repository],
                ]
            )
        else:
            refinement = None

        total_pull_requests = int(
            metrics.get("total_pull_requests") or 0
        )

        if total_pull_requests > 0:
            integration = applicable_mean(
                [
                    clamp_rate(
                        metrics.get(
                            "pull_request_merge_rate"
                        )
                    ),
                    clamp_rate(
                        metrics.get(
                            "reviewed_pull_request_ratio"
                        )
                    ),
                    cycle_score[repository],
                ]
            )
        else:
            integration = None

        dimensions = [
            engagement,
            regularity,
            refinement,
            integration,
        ]

        applicable_dimensions = [
            dimension
            for dimension in dimensions
            if dimension is not None
        ]

        final_score = (
            mean(applicable_dimensions) * 100
            if applicable_dimensions
            else None
        )

        results[repository] = {
            "engagement_score": engagement,
            "regularity_score": regularity,
            "refinement_score": refinement,
            "integration_score": integration,
            "applicable_dimensions": len(
                applicable_dimensions
            ),
            "experimentation_intensity_score": final_score,
        }

    return results