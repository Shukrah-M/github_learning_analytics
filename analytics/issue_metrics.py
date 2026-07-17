from statistics import mean


def calculate_issue_metrics(issues, comments):
    total_issues = len(issues)

    closed_issues = [
        issue
        for issue in issues
        if issue.state == "closed"
    ]

    resolution_times = []

    for issue in closed_issues:
        if issue.created_at and issue.closed_at:
            resolution_days = (
                issue.closed_at - issue.created_at
            ).total_seconds() / 86400

            resolution_times.append(resolution_days)

    closure_rate = (
        len(closed_issues) / total_issues
        if total_issues > 0
        else None
    )

    return {
    "total_issues_created": total_issues,
    "total_issues_closed": len(closed_issues),

    "issue_closure_rate": (
        round(closure_rate, 3)
        if closure_rate is not None
        else None
    ),

    "mean_issue_resolution_days": (
        round(mean(resolution_times), 2)
        if resolution_times
        else None
    ),

    "total_issue_comments": len(comments),

    "mean_comments_per_issue": (
        round(len(comments) / total_issues, 2)
        if total_issues > 0
        else None
    ),
}