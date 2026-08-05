import os
from dotenv import load_dotenv

from database.database import SessionLocal
from extractor.pipeline import run_extraction_pipeline


load_dotenv()

OWNER = os.getenv("GITHUB_OWNER")
REPO = os.getenv("GITHUB_REPOSITORY")


def run_pipeline():
    session = SessionLocal()

    try:
        print("Starting GitHub data extraction pipeline...")
        print(f"Repository: {OWNER}/{REPO}")

        summary = run_extraction_pipeline(session, OWNER, REPO)

        print("\nPipeline completed successfully!")
        print("Extraction summary:")
        print(f"Repository saved: {summary['repository'].name}")
        print(f"Commits extracted: {summary['commits']}")
        print(f"Issues extracted: {summary['issues']}")
        print(f"Issue comments extracted: {summary['issue_comments']}")
        print(f"Pull requests extracted: {summary['pull_requests']}")
        print(
            "Pull request reviews extracted: "
            f"{summary['pull_request_reviews']}"
        )

    finally:
        session.close()


if __name__ == "__main__":
    run_pipeline()