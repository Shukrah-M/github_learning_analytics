from datetime import datetime, timezone
from types import SimpleNamespace

from analytics.experimentation_score import (
    calculate_behavioural_metrics,
)


def make_datetime(day: int):
    return datetime(
        2026,
        7,
        day,
        9,
        tzinfo=timezone.utc,
    )


def test_unified_behavioural_analytics():
    commits = [
        SimpleNamespace(committed_at=make_datetime(1)),
        SimpleNamespace(committed_at=make_datetime(3)),
        SimpleNamespace(committed_at=make_datetime(5)),
        SimpleNamespace(committed_at=make_datetime(7)),
    ]

    issues = [
        SimpleNamespace(
            state="closed",
            created_at=make_datetime(1),
            closed_at=make_datetime(3),
        )
    ]

    issue_comments = [
        SimpleNamespace(),
    ]

    pull_requests = [
        SimpleNamespace(
            id=1,
            merged=True,
            created_at=make_datetime(1),
            merged_at=make_datetime(2),
            closed_at=None,
        )
    ]

    pull_request_reviews = [
        SimpleNamespace(
            pull_request_id=1
        ),
    ]

    metrics = calculate_behavioural_metrics(
        commits=commits,
        issues=issues,
        issue_comments=issue_comments,
        pull_requests=pull_requests,
        pull_request_reviews=pull_request_reviews,
    )

    assert "commit_metrics" in metrics
    assert "issue_metrics" in metrics
    assert "pull_request_metrics" in metrics

    assert metrics["commit_metrics"]["total_commits"] == 4

    assert (
        metrics["issue_metrics"]["issue_closure_rate"]
        == 1.0
    )

    assert (
        metrics["pull_request_metrics"]
        ["pull_request_merge_rate"]
        == 1.0
    )

    assert (
        metrics["pull_request_metrics"]
        ["reviewed_pull_request_ratio"]
        == 1.0
    )