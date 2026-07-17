from database.models import (
    Repository,
    Commit,
    Issue,
    IssueComment,
    PullRequest,
    PullRequestReview,
)


def get_repository_by_id(session, repository_id):
    return (
        session.query(Repository)
        .filter(Repository.id == repository_id)
        .first()
    )


def get_commits(session, repository_id):
    return (
        session.query(Commit)
        .filter(Commit.repository_id == repository_id)
        .order_by(Commit.committed_at.asc())
        .all()
    )


def get_issues(session, repository_id):
    return (
        session.query(Issue)
        .filter(Issue.repository_id == repository_id)
        .order_by(Issue.created_at.asc())
        .all()
    )


def get_issue_comments(session, repository_id):
    return (
        session.query(IssueComment)
        .join(Issue)
        .filter(Issue.repository_id == repository_id)
        .all()
    )


def get_pull_requests(session, repository_id):
    return (
        session.query(PullRequest)
        .filter(PullRequest.repository_id == repository_id)
        .order_by(PullRequest.created_at.asc())
        .all()
    )


def get_pull_request_reviews(session, repository_id):
    return (
        session.query(PullRequestReview)
        .join(PullRequest)
        .filter(PullRequest.repository_id == repository_id)
        .all()
    )
