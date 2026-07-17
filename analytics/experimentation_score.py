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
):
    commit_metrics = calculate_commit_metrics(commits)

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