from database.models import Repository, Commit, Issue, IssueComment


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
def save_issues(session, repository_id, issues_data):
    saved_issues = []

    for issue_data in issues_data:
        comments_url = issue_data.pop("comments_url", None)

        existing_issue = (
            session.query(Issue)
            .filter_by(
                repository_id=repository_id,
                issue_number=issue_data["issue_number"]
            )
            .first()
        )

        if existing_issue:
            existing_issue.github_issue_id = issue_data["github_issue_id"]
            existing_issue.author_login = issue_data["author_login"]
            existing_issue.title = issue_data["title"]
            existing_issue.body = issue_data["body"]
            existing_issue.state = issue_data["state"]
            existing_issue.created_at = issue_data["created_at"]
            existing_issue.updated_at = issue_data["updated_at"]
            existing_issue.closed_at = issue_data["closed_at"]

            saved_issues.append((existing_issue, comments_url))

        else:
            new_issue = Issue(
                repository_id=repository_id,
                **issue_data
            )

            session.add(new_issue)
            session.flush()

            saved_issues.append((new_issue, comments_url))

    session.commit()

    return saved_issues


def save_issue_comments(session, issue_id, comments_data):
    saved_comments = []

    for comment_data in comments_data:
        existing_comment = (
            session.query(IssueComment)
            .filter_by(
                github_comment_id=comment_data["github_comment_id"]
            )
            .first()
        )

        if existing_comment:
            existing_comment.author_login = comment_data["author_login"]
            existing_comment.body = comment_data["body"]
            existing_comment.created_at = comment_data["created_at"]
            existing_comment.updated_at = comment_data["updated_at"]

            saved_comments.append(existing_comment)

        else:
            new_comment = IssueComment(
                issue_id=issue_id,
                **comment_data
            )

            session.add(new_comment)
            saved_comments.append(new_comment)

    session.commit()

    return saved_comments