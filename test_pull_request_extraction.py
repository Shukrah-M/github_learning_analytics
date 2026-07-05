import os
from dotenv import load_dotenv

from database.database import SessionLocal
from extractor.repository import extract_repository
from extractor.pull_requests import (
    extract_pull_requests,
    extract_pull_request_reviews
)
from database.repository import (
    save_repository,
    save_pull_requests,
    save_pull_request_reviews
)

load_dotenv()

owner = os.getenv("GITHUB_OWNER")
repo = os.getenv("GITHUB_REPOSITORY")


def main():
    session = SessionLocal()

    try:
        print("Extracting repository metadata...")
        repository_data = extract_repository(owner, repo)
        saved_repository = save_repository(session, repository_data)

        print("Extracting pull requests from GitHub...")
        pull_requests_data = extract_pull_requests(owner, repo)

        print(f"Number of pull requests extracted: {len(pull_requests_data)}")

        saved_pull_requests = save_pull_requests(
            session=session,
            repository_id=saved_repository.id,
            pull_requests_data=pull_requests_data
        )

        total_reviews = 0

        for pull_request in saved_pull_requests:
            reviews_data = extract_pull_request_reviews(
                owner=owner,
                repo=repo,
                pr_number=pull_request.pr_number
            )

            save_pull_request_reviews(
                session=session,
                pull_request_id=pull_request.id,
                reviews_data=reviews_data
            )

            total_reviews += len(reviews_data)

        print("Pull requests saved successfully!")
        print(f"Pull request reviews saved successfully: {total_reviews}")

    finally:
        session.close()


if __name__ == "__main__":
    main()