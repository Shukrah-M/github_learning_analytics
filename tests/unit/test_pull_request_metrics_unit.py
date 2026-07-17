from datetime import datetime, timezone
from types import SimpleNamespace

from analytics.pull_request_metrics import (
    calculate_pull_request_metrics,
)


def make_datetime(day: int):
    return datetime(
        2026,
        7,
        day,
        9,
        tzinfo=timezone.utc,
    )


def make_pull_request(
    pr_id: int,
    merged: bool,
    created_day: int,
    end_day: int,
):
    return SimpleNamespace(
        id=pr_id,
        merged=merged,
        created_at=make_datetime(created_day),
        merged_at=(
            make_datetime(end_day)
            if merged
            else None
        ),
        closed_at=(
            make_datetime(end_day)
            if not merged
            else None
        ),
    )


def make_review(pull_request_id: int):
    return SimpleNamespace(
        pull_request_id=pull_request_id
    )


def test_pull_request_metrics_with_known_results():
    """
    Five PRs exist.

    Four are merged.
    Three distinct PRs receive reviews.
    Six formal reviews exist.

    Merge rate = 4 / 5 = 0.80
    Reviewed PR ratio = 3 / 5 = 0.60

    Cycle times:
    1, 2, 3, 4 and 5 days

    Mean cycle time = 3 days.
    """
    pull_requests = [
        make_pull_request(1, True, 1, 2),
        make_pull_request(2, True, 1, 3),
        make_pull_request(3, True, 1, 4),
        make_pull_request(4, True, 1, 5),
        make_pull_request(5, False, 1, 6),
    ]

    reviews = [
        make_review(1),
        make_review(1),
        make_review(2),
        make_review(2),
        make_review(3),
        make_review(3),
    ]

    metrics = calculate_pull_request_metrics(
        pull_requests,
        reviews,
    )

    assert metrics["total_pull_requests"] == 5
    assert metrics["merged_pull_requests"] == 4
    assert metrics["pull_request_merge_rate"] == 0.8
    assert metrics["total_pull_request_reviews"] == 6
    assert metrics["reviewed_pull_request_ratio"] == 0.6
    assert metrics["mean_pull_request_cycle_days"] == 3.0


def test_pull_request_without_reviews():
    pull_requests = [
        make_pull_request(1, True, 1, 2),
    ]

    metrics = calculate_pull_request_metrics(
        pull_requests,
        [],
    )

    assert metrics["total_pull_requests"] == 1
    assert metrics["merged_pull_requests"] == 1
    assert metrics["pull_request_merge_rate"] == 1.0
    assert metrics["total_pull_request_reviews"] == 0
    assert metrics["reviewed_pull_request_ratio"] == 0.0
    assert metrics["mean_pull_request_cycle_days"] == 1.0


def test_no_pull_requests():
    metrics = calculate_pull_request_metrics(
        pull_requests=[],
        reviews=[],
    )

    assert metrics["total_pull_requests"] == 0
    assert metrics["merged_pull_requests"] == 0
    assert metrics["total_pull_request_reviews"] == 0
    assert metrics["pull_request_merge_rate"] is None
    assert metrics["reviewed_pull_request_ratio"] is None
    assert metrics["mean_pull_request_cycle_days"] is None