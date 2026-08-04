"""Retrieve repository text artefacts from PostgreSQL for NLP classification."""

from __future__ import annotations

from typing import Any

from analytics.data_access import (
    get_commits,
    get_issue_comments,
    get_issues,
    get_pull_request_reviews,
    get_pull_requests,
)


def clean_text(value: Any) -> str:
    """Strip a database text field to a plain string."""
    if value is None:
        return ""

    return str(value).strip()


def combine_title_and_body(title: Any, body: Any) -> str:
    """Join a title and body into one text artefact."""
    return clean_text(
        " ".join(
            part
            for part in (clean_text(title), clean_text(body))
            if part
        )
    )


def get_repository_texts(
    session,
    repository_id: int,
) -> list[dict[str, str]]:
    """
    Collect text artefacts for a repository for live NLP
    classification: commit messages, issue titles/bodies, issue
    comments, pull-request titles/bodies, and pull-request reviews.

    Uses the same data-access queries as the behavioural metrics
    (analytics/data_access.py) so the dashboard reads from a single,
    consistent path into PostgreSQL.
    """
    records: list[dict[str, str]] = []

    for commit in get_commits(session, repository_id):
        text = clean_text(commit.message)

        if text:
            records.append(
                {
                    "artifact_type": "commit",
                    "artifact_id": commit.sha,
                    "text": text,
                }
            )

    for issue in get_issues(session, repository_id):
        text = combine_title_and_body(
            issue.title,
            issue.body,
        )

        if text:
            records.append(
                {
                    "artifact_type": "issue",
                    "artifact_id": str(issue.issue_number),
                    "text": text,
                }
            )

    for comment in get_issue_comments(session, repository_id):
        text = clean_text(comment.body)

        if text:
            records.append(
                {
                    "artifact_type": "issue_comment",
                    "artifact_id": str(comment.github_comment_id),
                    "text": text,
                }
            )

    for pull_request in get_pull_requests(session, repository_id):
        text = combine_title_and_body(
            pull_request.title,
            pull_request.body,
        )

        if text:
            records.append(
                {
                    "artifact_type": "pull_request",
                    "artifact_id": str(pull_request.pr_number),
                    "text": text,
                }
            )

    for review in get_pull_request_reviews(session, repository_id):
        text = clean_text(review.body)

        if text:
            records.append(
                {
                    "artifact_type": "pull_request_review",
                    "artifact_id": str(review.github_review_id),
                    "text": text,
                }
            )

    return records
