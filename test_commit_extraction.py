import os
from dotenv import load_dotenv

from database.database import SessionLocal
from extractor.repository import extract_repository
from extractor.commits import extract_commits
from database.repository import save_repository, save_commits

load_dotenv()

owner = os.getenv("GITHUB_OWNER")
repo = os.getenv("GITHUB_REPOSITORY")


def main():
    session = SessionLocal()

    try:
        print("Extracting repository metadata...")
        repository_data = extract_repository(owner, repo)
        saved_repository = save_repository(session, repository_data)

        print("Extracting commits from GitHub...")
        commits_data = extract_commits(owner, repo)

        print(f"Number of commits extracted: {len(commits_data)}")

        save_commits(
            session=session,
            repository_id=saved_repository.id,
            commits_data=commits_data
        )

        print("Commits saved successfully!")

    finally:
        session.close()


if __name__ == "__main__":
    main()