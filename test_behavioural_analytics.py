from pprint import pprint

from database.database import SessionLocal
from analytics.data_access import (
    get_commits,
    get_issues,
    get_issue_comments,
    get_pull_requests,
    get_pull_request_reviews,
)
from analytics.experimentation_score import (
    calculate_behavioural_metrics,
)


REPOSITORY_ID = 1


def main():
    session = SessionLocal()

    try:
        metrics = calculate_behavioural_metrics(
            commits=get_commits(session, REPOSITORY_ID),
            issues=get_issues(session, REPOSITORY_ID),
            issue_comments=get_issue_comments(
                session,
                REPOSITORY_ID,
            ),
            pull_requests=get_pull_requests(
                session,
                REPOSITORY_ID,
            ),
            pull_request_reviews=get_pull_request_reviews(
                session,
                REPOSITORY_ID,
            ),
        )

        pprint(metrics)

        # Sanity checks must stay inside main(),
        # where the metrics variable is available.
        commit_metrics = metrics["commit_metrics"]
        issue_metrics = metrics["issue_metrics"]
        pr_metrics = metrics["pull_request_metrics"]

        active_day_ratio = commit_metrics["active_day_ratio"]

        if active_day_ratio is not None:
            assert 0 <= active_day_ratio <= 1

        assert commit_metrics["total_commits"] >= 0
        assert commit_metrics["project_duration_days"] >= 0

        issue_closure_rate = issue_metrics["issue_closure_rate"]

        if issue_closure_rate is not None:
            assert 0 <= issue_closure_rate <= 1

        assert issue_metrics["total_issues_created"] >= 0
        assert issue_metrics["total_issues_closed"] >= 0

        pr_merge_rate = pr_metrics["pull_request_merge_rate"]

        if pr_merge_rate is not None:
            assert 0 <= pr_merge_rate <= 1

        reviewed_pr_ratio = pr_metrics["reviewed_pull_request_ratio"]

        if reviewed_pr_ratio is not None:
            assert 0 <= reviewed_pr_ratio <= 1

        assert pr_metrics["total_pull_requests"] >= 0
        assert pr_metrics["total_pull_request_reviews"] >= 0

        print("\nAll behavioural metric sanity checks passed.")

    finally:
        session.close()


if __name__ == "__main__":
    main()