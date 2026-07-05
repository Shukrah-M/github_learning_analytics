import os
from dotenv import load_dotenv

from database.database import SessionLocal
from extractor.repository import extract_repository
from database.repository import save_repository

load_dotenv()

owner = os.getenv("GITHUB_OWNER")
repo = os.getenv("GITHUB_REPOSITORY")


def main():
    print("Extracting repository metadata from GitHub...")

    repository_data = extract_repository(owner, repo)

    print("Repository data extracted:")
    print(repository_data)

    session = SessionLocal()

    try:
        saved_repository = save_repository(session, repository_data)

        print("Repository saved successfully!")
        print("Database ID:", saved_repository.id)
        print("Repository name:", saved_repository.name)
        print("Owner:", saved_repository.owner)

    finally:
        session.close()


if __name__ == "__main__":
    main()