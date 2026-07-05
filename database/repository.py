from database.models import Repository


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