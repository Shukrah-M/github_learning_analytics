import os
from dotenv import load_dotenv

from database.database import SessionLocal
from extractor.repository import extract_repository
from extractor.issues import extract_issues, extract_issue_comments
from database.repository import (
    save_repository,
    save_issues,
    save_issue_comments
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

        print("Extracting issues from GitHub...")
        issues_data = extract_issues(owner, repo)

        print(f"Number of real issues extracted: {len(issues_data)}")

        saved_issues = save_issues(
            session=session,
            repository_id=saved_repository.id,
            issues_data=issues_data
        )

        total_comments = 0

        for issue, comments_url in saved_issues:
            if comments_url:
                comments_data = extract_issue_comments(comments_url)

                save_issue_comments(
                    session=session,
                    issue_id=issue.id,
                    comments_data=comments_data
                )

                total_comments += len(comments_data)

        print("Issues saved successfully!")
        print(f"Issue comments saved successfully: {total_comments}")

    finally:
        session.close()


if __name__ == "__main__":
    main()