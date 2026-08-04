"""Calculate repository commit-activity metrics."""

from statistics import mean, pstdev


def calculate_commit_metrics(
    commits,
    observation_days=None,
):
    """
    Calculate commit metrics.

    Parameters
    ----------
    commits:
        Repository commit records.

    observation_days:
        Optional fixed observation period.

        Use None for controlled repositories. The function then uses
        the inclusive period between the first and last commit.

        Use 180 for public repositories so every repository has the
        same denominator.
    """
    if observation_days is not None and observation_days <= 0:
        raise ValueError(
            "observation_days must be greater than zero."
        )

    empty_result = {
        "total_commits": 0,
        "project_duration_days": 0,
        "activity_span_days": 0,
        "observation_period_days": observation_days,
        "commit_frequency_per_week": None,
        "active_commit_days": 0,
        "active_day_ratio": None,
        "mean_commit_interval_days": None,
        "commit_interval_std_days": None,
        "longest_inactivity_gap_days": None,
    }

    if not commits:
        return empty_result

    timestamps = sorted(
        commit.committed_at
        for commit in commits
        if commit.committed_at is not None
    )

    if not timestamps:
        empty_result["total_commits"] = len(commits)
        return empty_result

    first_date = timestamps[0].date()
    last_date = timestamps[-1].date()

    # Inclusive period between the first and last commit.
    activity_span_days = (
        last_date - first_date
    ).days + 1

    # Controlled repositories use their activity span.
    # Public repositories use the supplied fixed period.
    denominator_days = (
        observation_days
        if observation_days is not None
        else activity_span_days
    )

    denominator_weeks = denominator_days / 7

    active_dates = {
        timestamp.date()
        for timestamp in timestamps
    }

    intervals = [
        (
            timestamps[index]
            - timestamps[index - 1]
        ).total_seconds() / 86400
        for index in range(1, len(timestamps))
    ]

    return {
        "total_commits": len(timestamps),

        # Retained for compatibility with existing tests and code.
        "project_duration_days": activity_span_days,

        # Clearer research terminology.
        "activity_span_days": activity_span_days,
        "observation_period_days": denominator_days,

        "commit_frequency_per_week": round(
            len(timestamps) / denominator_weeks,
            2,
        ),
        "active_commit_days": len(active_dates),
        "active_day_ratio": round(
            len(active_dates) / denominator_days,
            3,
        ),
        "mean_commit_interval_days": (
            round(mean(intervals), 2)
            if intervals
            else None
        ),
        "commit_interval_std_days": (
            round(pstdev(intervals), 2)
            if len(intervals) > 1
            else None
        ),
        "longest_inactivity_gap_days": (
            round(max(intervals), 2)
            if intervals
            else None
        ),
    }