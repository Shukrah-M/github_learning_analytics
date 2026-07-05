from database.models import Repository, Commit


def save_repository(session, repository_data):
    existing_repository = (
        session.query(Repository)
        .filter_by(github_id=repository_data["github_id"])
        .first()
    )

    if existing_repository:
        existing_repository.name = repository_data["name"]
        existing_repository.owner = repository_data["owner"]
        existing_repository.description = repository_data["description"]
        existing_repository.language = repository_data["language"]
        existing_repository.default_branch = repository_data["default_branch"]
        existing_repository.created_at = repository_data["created_at"]
        existing_repository.updated_at = repository_data["updated_at"]

        session.commit()
        session.refresh(existing_repository)

        return existing_repository

    new_repository = Repository(**repository_data)

    session.add(new_repository)
    session.commit()
    session.refresh(new_repository)

    return new_repository
def save_commits(session, repository_id, commits_data):
    saved_commits = []

    for commit_data in commits_data:
        existing_commit = (
            session.query(Commit)
            .filter_by(
                repository_id=repository_id,
                sha=commit_data["sha"]
            )
            .first()
        )

        if existing_commit:
            existing_commit.author_name = commit_data["author_name"]
            existing_commit.author_email = commit_data["author_email"]
            existing_commit.author_login = commit_data["author_login"]
            existing_commit.message = commit_data["message"]
            existing_commit.committed_at = commit_data["committed_at"]

            saved_commits.append(existing_commit)

        else:
            new_commit = Commit(
                repository_id=repository_id,
                **commit_data
            )

            session.add(new_commit)
            saved_commits.append(new_commit)

    session.commit()

    return saved_commits