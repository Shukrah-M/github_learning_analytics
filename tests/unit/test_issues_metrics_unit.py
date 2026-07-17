from datetime import datetime, timezone
from types import SimpleNamespace

from analytics.issue_metrics import calculate_issue_metrics


def make_datetime(day: int):
    return datetime(
        2026,
        7,
        day,
        9,
        tzinfo=timezone.utc,
    )


def make_issue(
    state: str,
    created_day: int,
    closed_day: int | None = None,
):
    return SimpleNamespace(
        state=state,
        created_at=make_datetime(created_day),
        closed_at=(
            make_datetime(closed_day)
            if closed_day is not None
            else None
        ),
    )


def test_issue_closure_and_resolution_metrics():
    """
    Four issues exist.

    Three are closed in:
    2 days
    4 days
    6 days

    Closure rate = 3 / 4 = 0.75
    Mean resolution time = 4 days
    """
    issues = [
        make_issue("closed", 1, 3),
        make_issue("closed", 1, 5),
        make_issue("closed", 2, 8),
        make_issue("open", 4),
    ]

    comments = [
        SimpleNamespace(),
        SimpleNamespace(),
        SimpleNamespace(),
        SimpleNamespace(),
    ]

    metrics = calculate_issue_metrics(
        issues,
        comments,
    )

    assert metrics["total_issues_created"] == 4
    assert metrics["total_issues_closed"] == 3
    assert metrics["issue_closure_rate"] == 0.75
    assert metrics["mean_issue_resolution_days"] == 4.0
    assert metrics["total_issue_comments"] == 4
    assert metrics["mean_comments_per_issue"] == 1.0


def test_open_issues_have_no_resolution_time():
    issues = [
        make_issue("open", 1),
        make_issue("open", 2),
    ]

    metrics = calculate_issue_metrics(
        issues=issues,
        comments=[],
    )

    assert metrics["total_issues_created"] == 2
    assert metrics["total_issues_closed"] == 0
    assert metrics["issue_closure_rate"] == 0.0
    assert metrics["mean_issue_resolution_days"] is None
    assert metrics["total_issue_comments"] == 0


def test_no_issues():
    metrics = calculate_issue_metrics(
        issues=[],
        comments=[],
    )

    assert metrics["total_issues_created"] == 0
    assert metrics["total_issues_closed"] == 0
    assert metrics["issue_closure_rate"] is None
    assert metrics["mean_issue_resolution_days"] is None
    assert metrics["total_issue_comments"] == 0