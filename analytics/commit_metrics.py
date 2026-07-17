from statistics import mean, pstdev


def calculate_commit_metrics(commits):
    empty_result = {
        "total_commits": 0,
        "project_duration_days": 0,
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

    # Inclusive calendar-day observation period.
    project_duration_days = (last_date - first_date).days + 1
    project_duration_weeks = project_duration_days / 7

    active_dates = {
        timestamp.date()
        for timestamp in timestamps
    }

    intervals = [
        (
            timestamps[index] - timestamps[index - 1]
        ).total_seconds() / 86400
        for index in range(1, len(timestamps))
    ]

    return {
        "total_commits": len(commits),
        "project_duration_days": project_duration_days,
        "commit_frequency_per_week": round(
            len(commits) / project_duration_weeks,
            2,
        ),
        "active_commit_days": len(active_dates),
        "active_day_ratio": round(
            len(active_dates) / project_duration_days,
            3,
        ),
        "mean_commit_interval_days": (
            round(mean(intervals), 2)
            if intervals else None
        ),
        "commit_interval_std_days": (
            round(pstdev(intervals), 2)
            if len(intervals) > 1 else None
        ),
        "longest_inactivity_gap_days": (
            round(max(intervals), 2)
            if intervals else None
        ),
    }