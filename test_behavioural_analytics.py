"""Run behavioural analytics and sanity checks for one repository."""

from pprint import pprint

from analytics.repository_analysis import (
    analyse_repository,
)
from database.database import SessionLocal


# Change this value for each public repository.
REPOSITORY_ID = 12

# All public repositories use the same fixed observation period.
OBSERVATION_DAYS = 180


def main() -> None:
    session = SessionLocal()

    try:
        metrics = analyse_repository(
            session=session,
            repository_id=REPOSITORY_ID,
            observation_days=OBSERVATION_DAYS,
        )

        print("=" * 72)
        print("BEHAVIOURAL ANALYTICS EXECUTION")
        print("=" * 72)
        print(f"Repository database ID: {REPOSITORY_ID}")
        print(
            f"Observation period: {OBSERVATION_DAYS} days"
        )
        print("-" * 72)

        pprint(metrics, sort_dicts=False)

        commit_metrics = metrics["commit_metrics"]
        issue_metrics = metrics["issue_metrics"]
        pr_metrics = metrics["pull_request_metrics"]

        # Commit metric checks
        active_day_ratio = commit_metrics[
            "active_day_ratio"
        ]

        if active_day_ratio is not None:
            assert 0 <= active_day_ratio <= 1

        assert commit_metrics["total_commits"] >= 0
        assert (
            commit_metrics["project_duration_days"]
            >= 0
        )
        assert (
            commit_metrics[
                "observation_period_days"
            ]
            == OBSERVATION_DAYS
        )

        # Issue metric checks
        issue_closure_rate = issue_metrics[
            "issue_closure_rate"
        ]

        if issue_closure_rate is not None:
            assert 0 <= issue_closure_rate <= 1

        assert (
            issue_metrics["total_issues_created"]
            >= 0
        )
        assert (
            issue_metrics["total_issues_closed"]
            >= 0
        )

        # Pull-request metric checks
        pr_merge_rate = pr_metrics[
            "pull_request_merge_rate"
        ]

        if pr_merge_rate is not None:
            assert 0 <= pr_merge_rate <= 1

        reviewed_pr_ratio = pr_metrics[
            "reviewed_pull_request_ratio"
        ]

        if reviewed_pr_ratio is not None:
            assert 0 <= reviewed_pr_ratio <= 1

        assert (
            pr_metrics["total_pull_requests"]
            >= 0
        )
        assert (
            pr_metrics[
                "total_pull_request_reviews"
            ]
            >= 0
        )

        print("-" * 72)
        print(
            "All public-repository behavioural "
            "metric sanity checks passed."
        )
        print("=" * 72)

    finally:
        session.close()


if __name__ == "__main__":
    main()