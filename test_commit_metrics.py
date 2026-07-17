from database.database import SessionLocal
from analytics.data_access import get_commits
from analytics.commit_metrics import calculate_commit_metrics


REPOSITORY_ID = 1


def main():
    session = SessionLocal()

    try:
        commits = get_commits(session, REPOSITORY_ID)
        metrics = calculate_commit_metrics(commits)

        print("Commit metrics")

        for metric_name, value in metrics.items():
            print(f"{metric_name}: {value}")

    finally:
        session.close()


if __name__ == "__main__":
    main()