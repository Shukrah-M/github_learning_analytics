"""Retrieve and combine repository behavioural metrics for scoring."""

from __future__ import annotations

from typing import Any

from analytics.data_access import (
    get_commits,
    get_issue_comments,
    get_issues,
    get_pull_request_reviews,
    get_pull_requests,
)
from analytics.experimentation_score import (
    calculate_behavioural_metrics,
)
from database.database import SessionLocal


def first_available(
    metric_group: dict[str, Any],
    *possible_keys: str,
) -> float | int | None:
    """
    Return the first available metric value.

    Multiple possible keys are supported because metric naming
    may differ slightly between analytics modules.
    """
    for key in possible_keys:
        if key in metric_group:
            return metric_group[key]

    return None


def analyse_repository(
    repository_id: int,
    observation_days: int = 180,
) -> dict[str, float | int | None]:
    """
    Retrieve repository activity from PostgreSQL and return the
    flattened behavioural metrics required for scoring.
    """
    session = SessionLocal()

    try:
        all_metrics = calculate_behavioural_metrics(
            commits=get_commits(
                session,
                repository_id,
            ),
            issues=get_issues(
                session,
                repository_id,
            ),
            issue_comments=get_issue_comments(
                session,
                repository_id,
            ),
            pull_requests=get_pull_requests(
                session,
                repository_id,
            ),
            pull_request_reviews=get_pull_request_reviews(
                session,
                repository_id,
            ),
            observation_days=observation_days,
        )

        commit_metrics = all_metrics["commit_metrics"]
        issue_metrics = all_metrics["issue_metrics"]
        pull_request_metrics = all_metrics[
            "pull_request_metrics"
        ]

        return {
            # Commit and temporal metrics
            "commit_frequency_per_week": first_available(
                commit_metrics,
                "commit_frequency_per_week",
            ),
            "active_day_ratio": first_available(
                commit_metrics,
                "active_day_ratio",
            ),
            "commit_interval_std_days": first_available(
                commit_metrics,
                "commit_interval_std_days",
                "std_commit_interval_days",
                "commit_interval_standard_deviation_days",
            ),
            "longest_inactivity_gap_days": first_available(
                commit_metrics,
                "longest_inactivity_gap_days",
                "longest_commit_gap_days",
            ),

            # Issue and refinement metrics
            "total_issues": first_available(
                issue_metrics,
                "total_issues_created",
                "total_issues",
            ),
            "issue_closure_rate": first_available(
                issue_metrics,
                "issue_closure_rate",
            ),
            "mean_comments_per_issue": first_available(
                issue_metrics,
                "mean_comments_per_issue",
                "average_comments_per_issue",
            ),
            "mean_issue_resolution_days": first_available(
                issue_metrics,
                "mean_issue_resolution_days",
                "average_issue_resolution_days",
            ),

            # Pull-request and integration metrics
            "total_pull_requests": first_available(
                pull_request_metrics,
                "total_pull_requests",
            ),
            "pull_request_merge_rate": first_available(
                pull_request_metrics,
                "pull_request_merge_rate",
            ),
            "reviewed_pull_request_ratio": first_available(
                pull_request_metrics,
                "reviewed_pull_request_ratio",
            ),
            "mean_pull_request_cycle_days": first_available(
                pull_request_metrics,
                "mean_pull_request_cycle_days",
                "mean_pr_cycle_time_days",
                "mean_pull_request_cycle_time_days",
            ),
        }

    finally:
        session.close()