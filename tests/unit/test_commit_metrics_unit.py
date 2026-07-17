from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from analytics.commit_metrics import calculate_commit_metrics


def make_commit(
    day: int,
    hour: int = 9,
):
    """Create a lightweight object resembling a database commit."""
    return SimpleNamespace(
        committed_at=datetime(
            2026,
            7,
            day,
            hour,
            tzinfo=timezone.utc,
        )
    )


def test_regular_commit_pattern():
    """
    Four commits occur every two days:

    1 July
    3 July
    5 July
    7 July

    Expected intervals:
    2, 2 and 2 days.
    """
    commits = [
        make_commit(1),
        make_commit(3),
        make_commit(5),
        make_commit(7),
    ]

    metrics = calculate_commit_metrics(commits)

    assert metrics["total_commits"] == 4
    assert metrics["project_duration_days"] == 7
    assert metrics["commit_frequency_per_week"] == 4.0
    assert metrics["active_commit_days"] == 4

    assert metrics["active_day_ratio"] == pytest.approx(
        4 / 7,
        abs=0.001,
    )

    assert metrics["mean_commit_interval_days"] == 2.0
    assert metrics["commit_interval_std_days"] == 0.0
    assert metrics["longest_inactivity_gap_days"] == 2.0


def test_no_commits():
    """An empty repository must not cause an error."""
    metrics = calculate_commit_metrics([])

    assert metrics["total_commits"] == 0
    assert metrics["active_commit_days"] == 0
    assert metrics["active_day_ratio"] is None
    assert metrics["commit_frequency_per_week"] is None
    assert metrics["mean_commit_interval_days"] is None
    assert metrics["commit_interval_std_days"] is None
    assert metrics["longest_inactivity_gap_days"] is None


def test_single_commit():
    """One commit has no intervals to calculate."""
    metrics = calculate_commit_metrics([
        make_commit(1),
    ])

    assert metrics["total_commits"] == 1
    assert metrics["project_duration_days"] == 1
    assert metrics["active_commit_days"] == 1
    assert metrics["active_day_ratio"] == 1.0

    assert metrics["mean_commit_interval_days"] is None
    assert metrics["commit_interval_std_days"] is None
    assert metrics["longest_inactivity_gap_days"] is None


def test_irregular_commit_pattern():
    """
    Intervals are 1, 4 and 10 days.

    The longest inactivity gap should therefore be 10 days.
    """
    commits = [
        make_commit(1),
        make_commit(2),
        make_commit(6),
        make_commit(16),
    ]

    metrics = calculate_commit_metrics(commits)

    assert metrics["total_commits"] == 4
    assert metrics["longest_inactivity_gap_days"] == 10.0
    assert metrics["commit_interval_std_days"] > 0