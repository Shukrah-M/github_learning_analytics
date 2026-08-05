"""Shared GitHub extraction-and-save pipeline for one repository."""

from __future__ import annotations

from extractor.commits import extract_commits
from extractor.issues import extract_issue_comments, extract_issues
from extractor.pull_requests import (
    extract_pull_request_reviews,
    extract_pull_requests,
)
from extractor.repository import extract_repository

from database.repository import (
    save_commits,
    save_issue_comments,
    save_issues,
    save_pull_request_reviews,
    save_pull_requests,
    save_repository,
)


def run_extraction_pipeline(session, owner: str, repo: str) -> dict:
    """
    Extract one repository's activity from GitHub and save it to
    PostgreSQL, using the fixed observation window from
    utils/observation_window.py.

    Returns the saved Repository plus extraction counts.
    """
    repository_data = extract_repository(owner, repo)
    saved_repository = save_repository(session, repository_data)

    commits_data = extract_commits(owner, repo)
    save_commits(session, saved_repository.id, commits_data)

    issues_data = extract_issues(owner, repo)
    saved_issues = save_issues(session, saved_repository.id, issues_data)

    total_issue_comments = 0

    for issue, comments_url in saved_issues:
        if comments_url:
            comments_data = extract_issue_comments(comments_url)
            save_issue_comments(session, issue.id, comments_data)
            total_issue_comments += len(comments_data)

    pull_requests_data = extract_pull_requests(owner, repo)
    saved_pull_requests = save_pull_requests(
        session,
        saved_repository.id,
        pull_requests_data,
    )

    total_pr_reviews = 0

    for pull_request in saved_pull_requests:
        reviews_data = extract_pull_request_reviews(
            owner,
            repo,
            pull_request.pr_number,
        )

        save_pull_request_reviews(
            session,
            pull_request.id,
            reviews_data,
        )

        total_pr_reviews += len(reviews_data)

    return {
        "repository": saved_repository,
        "commits": len(commits_data),
        "issues": len(issues_data),
        "issue_comments": total_issue_comments,
        "pull_requests": len(pull_requests_data),
        "pull_request_reviews": total_pr_reviews,
    }
