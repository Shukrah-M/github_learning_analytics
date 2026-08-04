from types import SimpleNamespace

import analytics.nlp.repository_texts as repository_texts_module
from analytics.nlp.repository_texts import get_repository_texts


def test_get_repository_texts_combines_all_artifact_types(monkeypatch):
    monkeypatch.setattr(
        repository_texts_module,
        "get_commits",
        lambda session, repository_id: [
            SimpleNamespace(sha="abc123", message="fix bug"),
            SimpleNamespace(sha="def456", message="   "),
        ],
    )
    monkeypatch.setattr(
        repository_texts_module,
        "get_issues",
        lambda session, repository_id: [
            SimpleNamespace(
                issue_number=1,
                title="Bug report",
                body="Steps to reproduce",
            ),
        ],
    )
    monkeypatch.setattr(
        repository_texts_module,
        "get_issue_comments",
        lambda session, repository_id: [
            SimpleNamespace(
                github_comment_id=99,
                body="Thanks for the fix",
            ),
        ],
    )
    monkeypatch.setattr(
        repository_texts_module,
        "get_pull_requests",
        lambda session, repository_id: [
            SimpleNamespace(
                pr_number=7,
                title="Add feature",
                body=None,
            ),
        ],
    )
    monkeypatch.setattr(
        repository_texts_module,
        "get_pull_request_reviews",
        lambda session, repository_id: [
            SimpleNamespace(
                github_review_id=55,
                body="Looks good",
            ),
        ],
    )

    records = get_repository_texts(
        session=None,
        repository_id=1,
    )

    artifact_types = {
        record["artifact_type"] for record in records
    }

    assert artifact_types == {
        "commit",
        "issue",
        "issue_comment",
        "pull_request",
        "pull_request_review",
    }

    # The blank commit message is excluded.
    assert len(records) == 5

    commit_record = next(
        record
        for record in records
        if record["artifact_type"] == "commit"
    )
    assert commit_record["text"] == "fix bug"
    assert commit_record["artifact_id"] == "abc123"

    pull_request_record = next(
        record
        for record in records
        if record["artifact_type"] == "pull_request"
    )
    assert pull_request_record["text"] == "Add feature"
