import os
from dotenv import load_dotenv

from database.database import SessionLocal

from extractor.repository import extract_repository
from extractor.commits import extract_commits
from extractor.issues import extract_issues, extract_issue_comments
from extractor.pull_requests import (
    extract_pull_requests,
    extract_pull_request_reviews,
)

from database.repository import (
    save_repository,
    save_commits,
    save_issues,
    save_issue_comments,
    save_pull_requests,
    save_pull_request_reviews,
)


load_dotenv()

OWNER = os.getenv("GITHUB_OWNER")
REPO = os.getenv("GITHUB_REPOSITORY")


def run_pipeline():
    session = SessionLocal()

    try:
        print("Starting GitHub data extraction pipeline...")
        print(f"Repository: {OWNER}/{REPO}")

        repository_data = extract_repository(OWNER, REPO)
        saved_repository = save_repository(session, repository_data)

        commits_data = extract_commits(OWNER, REPO)
        save_commits(session, saved_repository.id, commits_data)

        issues_data = extract_issues(OWNER, REPO)
        saved_issues = save_issues(session, saved_repository.id, issues_data)

        total_issue_comments = 0

        for issue, comments_url in saved_issues:
            if comments_url:
                comments_data = extract_issue_comments(comments_url)
                save_issue_comments(session, issue.id, comments_data)
                total_issue_comments += len(comments_data)

        pull_requests_data = extract_pull_requests(OWNER, REPO)
        saved_pull_requests = save_pull_requests(
            session,
            saved_repository.id,
            pull_requests_data
        )

        total_pr_reviews = 0

        for pull_request in saved_pull_requests:
            reviews_data = extract_pull_request_reviews(
                OWNER,
                REPO,
                pull_request.pr_number
            )

            save_pull_request_reviews(
                session,
                pull_request.id,
                reviews_data
            )

            total_pr_reviews += len(reviews_data)

        print("\nPipeline completed successfully!")
        print("Extraction summary:")
        print(f"Repository saved: {saved_repository.name}")
        print(f"Commits extracted: {len(commits_data)}")
        print(f"Issues extracted: {len(issues_data)}")
        print(f"Issue comments extracted: {total_issue_comments}")
        print(f"Pull requests extracted: {len(pull_requests_data)}")
        print(f"Pull request reviews extracted: {total_pr_reviews}")

    finally:
        session.close()


if __name__ == "__main__":
    run_pipeline()