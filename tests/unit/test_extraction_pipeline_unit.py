from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import extractor.pipeline as pipeline_module
from extractor.github_api import GitHubAPIError
from extractor.pipeline import run_extraction_pipeline


def test_run_extraction_pipeline_orchestrates_extraction_and_save(
    monkeypatch,
):
    saved_repository = SimpleNamespace(id=42, name="hello-world")

    monkeypatch.setattr(
        pipeline_module,
        "extract_repository",
        lambda owner, repo: {"github_id": 1, "name": repo},
    )
    monkeypatch.setattr(
        pipeline_module,
        "save_repository",
        lambda session, data: saved_repository,
    )

    monkeypatch.setattr(
        pipeline_module,
        "extract_commits",
        lambda owner, repo: [{"sha": "a"}, {"sha": "b"}],
    )
    monkeypatch.setattr(
        pipeline_module,
        "save_commits",
        lambda session, repository_id, commits_data: None,
    )

    issue_object = SimpleNamespace(id=7)

    monkeypatch.setattr(
        pipeline_module,
        "extract_issues",
        lambda owner, repo: [{"issue_number": 1}],
    )
    monkeypatch.setattr(
        pipeline_module,
        "save_issues",
        lambda session, repository_id, issues_data: [
            (issue_object, "https://api.github.com/comments")
        ],
    )
    monkeypatch.setattr(
        pipeline_module,
        "extract_issue_comments",
        lambda comments_url: [{"body": "hi"}],
    )
    monkeypatch.setattr(
        pipeline_module,
        "save_issue_comments",
        lambda session, issue_id, comments_data: None,
    )

    pull_request_object = SimpleNamespace(id=9, pr_number=3)

    monkeypatch.setattr(
        pipeline_module,
        "extract_pull_requests",
        lambda owner, repo: [{"pr_number": 3}],
    )
    monkeypatch.setattr(
        pipeline_module,
        "save_pull_requests",
        lambda session, repository_id, pull_requests_data: [
            pull_request_object
        ],
    )
    monkeypatch.setattr(
        pipeline_module,
        "extract_pull_request_reviews",
        lambda owner, repo, pr_number: [{"state": "APPROVED"}],
    )
    monkeypatch.setattr(
        pipeline_module,
        "save_pull_request_reviews",
        lambda session, pull_request_id, reviews_data: None,
    )

    summary = run_extraction_pipeline(
        session=MagicMock(),
        owner="octocat",
        repo="hello-world",
    )

    assert summary["repository"] is saved_repository
    assert summary["commits"] == 2
    assert summary["issues"] == 1
    assert summary["issue_comments"] == 1
    assert summary["pull_requests"] == 1
    assert summary["pull_request_reviews"] == 1


def test_run_extraction_pipeline_propagates_github_api_error(monkeypatch):
    def raise_error(owner, repo):
        raise GitHubAPIError(404, "not found")

    monkeypatch.setattr(
        pipeline_module,
        "extract_repository",
        raise_error,
    )

    with pytest.raises(GitHubAPIError) as excinfo:
        run_extraction_pipeline(
            session=MagicMock(),
            owner="octocat",
            repo="missing",
        )

    assert excinfo.value.status_code == 404
