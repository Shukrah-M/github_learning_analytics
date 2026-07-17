from database.database import SessionLocal
from analytics.data_access import get_issues, get_issue_comments
from analytics.issue_metrics import calculate_issue_metrics


REPOSITORY_ID = 1


def main():
    session = SessionLocal()

    try:
        issues = get_issues(session, REPOSITORY_ID)
        comments = get_issue_comments(session, REPOSITORY_ID)

        metrics = calculate_issue_metrics(issues, comments)

        print("Issue metrics")

        for metric_name, value in metrics.items():
            print(f"{metric_name}: {value}")

    finally:
        session.close()


if __name__ == "__main__":
    main()