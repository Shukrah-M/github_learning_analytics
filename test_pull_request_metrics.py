from database.database import SessionLocal
from analytics.data_access import (
    get_pull_requests,
    get_pull_request_reviews,
)
from analytics.pull_request_metrics import (
    calculate_pull_request_metrics,
)


REPOSITORY_ID = 1


def main():
    session = SessionLocal()

    try:
        pull_requests = get_pull_requests(
            session,
            REPOSITORY_ID,
        )

        reviews = get_pull_request_reviews(
            session,
            REPOSITORY_ID,
        )

        metrics = calculate_pull_request_metrics(
            pull_requests,
            reviews,
        )

        print("Pull request metrics")

        for metric_name, value in metrics.items():
            print(f"{metric_name}: {value}")

    finally:
        session.close()


if __name__ == "__main__":
    main()