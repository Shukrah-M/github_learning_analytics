from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import dashboard.app as dashboard_app_module
from dashboard.app import app
from dashboard.rate_limit import RateLimiter
from extractor.github_api import GitHubAPIError


@pytest.fixture(autouse=True)
def reset_add_repository_rate_limiter():
    """Give every test a fresh rate limiter, since it's shared module state."""
    dashboard_app_module.add_repository_rate_limiter = RateLimiter(
        max_requests=dashboard_app_module.ADD_REPOSITORY_RATE_LIMIT,
        window_seconds=dashboard_app_module.ADD_REPOSITORY_RATE_WINDOW_SECONDS,
    )


def make_repository(
    repository_id=1,
    owner="octocat",
    name="hello-world",
    language="Python",
    description="An example repository.",
):
    return SimpleNamespace(
        id=repository_id,
        owner=owner,
        name=name,
        language=language,
        description=description,
    )


def make_metrics():
    return {
        "commit_frequency_per_week": 2.0,
        "active_day_ratio": 0.5,
        "commit_interval_std_days": 1.0,
        "longest_inactivity_gap_days": 3.0,
        "total_issues": 4,
        "issue_closure_rate": 0.5,
        "mean_comments_per_issue": 1.0,
        "mean_issue_resolution_days": 2.0,
        "total_pull_requests": 2,
        "pull_request_merge_rate": 1.0,
        "reviewed_pull_request_ratio": 1.0,
        "mean_pull_request_cycle_days": 0.5,
    }


def make_session_local(monkeypatch):
    monkeypatch.setattr(
        dashboard_app_module,
        "SessionLocal",
        lambda: MagicMock(close=lambda: None),
    )


def get_csrf_token(client, path):
    client.get(path)

    with client.session_transaction() as recorded_session:
        return recorded_session["_csrf_token"]


def test_index_route_lists_repositories(monkeypatch):
    make_session_local(monkeypatch)

    monkeypatch.setattr(
        dashboard_app_module,
        "get_all_repositories",
        lambda session: [make_repository()],
    )
    monkeypatch.setattr(
        dashboard_app_module,
        "get_commits",
        lambda session, repository_id: [SimpleNamespace()] * 3,
    )

    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"octocat/hello-world" in response.data


def test_index_route_renders_empty_state(monkeypatch):
    make_session_local(monkeypatch)

    monkeypatch.setattr(
        dashboard_app_module,
        "get_all_repositories",
        lambda session: [],
    )

    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"No repositories yet" in response.data


def test_repository_detail_route_renders_metrics(monkeypatch, tmp_path):
    repository = make_repository()

    make_session_local(monkeypatch)

    monkeypatch.setattr(
        dashboard_app_module,
        "get_repository_by_id",
        lambda session, repository_id: repository,
    )
    monkeypatch.setattr(
        dashboard_app_module,
        "get_all_repositories",
        lambda session: [repository],
    )
    monkeypatch.setattr(
        dashboard_app_module,
        "get_commits",
        lambda session, repository_id: [],
    )
    monkeypatch.setattr(
        dashboard_app_module,
        "analyse_repository",
        lambda repository_id: make_metrics(),
    )
    monkeypatch.setattr(
        dashboard_app_module,
        "calculate_experimentation_scores",
        lambda repository_metrics: {
            repository.id: {
                "engagement_score": 0.6,
                "regularity_score": 0.4,
                "refinement_score": None,
                "integration_score": 0.8,
                "applicable_dimensions": 3,
                "experimentation_intensity_score": 60.0,
            }
        },
    )
    monkeypatch.setattr(
        dashboard_app_module,
        "MODEL_PATH",
        tmp_path / "missing_model.joblib",
    )

    client = app.test_client()
    response = client.get(f"/repository/{repository.id}")

    assert response.status_code == 200
    assert b"octocat/hello-world" in response.data
    assert b"60.0" in response.data
    assert b"NLP model not trained yet" in response.data


def test_repository_detail_route_404_for_unknown_repository(monkeypatch):
    make_session_local(monkeypatch)

    monkeypatch.setattr(
        dashboard_app_module,
        "get_repository_by_id",
        lambda session, repository_id: None,
    )

    client = app.test_client()
    response = client.get("/repository/999")

    assert response.status_code == 404


def test_add_repository_get_renders_form(monkeypatch):
    client = app.test_client()
    response = client.get("/repositories/new")

    assert response.status_code == 200
    assert b"Add a repository" in response.data


def test_add_repository_post_success_redirects_to_detail(monkeypatch):
    saved_repository = make_repository(
        repository_id=5, owner="torvalds", name="linux"
    )

    make_session_local(monkeypatch)
    monkeypatch.setattr(
        dashboard_app_module,
        "run_extraction_pipeline",
        lambda session, owner, repo: {"repository": saved_repository},
    )

    client = app.test_client()
    csrf_token = get_csrf_token(client, "/repositories/new")

    response = client.post(
        "/repositories/new",
        data={
            "owner": "torvalds",
            "repo": "linux",
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/repository/5")


def test_add_repository_post_rejects_invalid_csrf_token(monkeypatch):
    client = app.test_client()

    response = client.post(
        "/repositories/new",
        data={
            "owner": "torvalds",
            "repo": "linux",
            "csrf_token": "wrong-token",
        },
    )

    assert response.status_code == 400


def test_add_repository_post_shows_friendly_error_for_missing_repository(
    monkeypatch,
):
    make_session_local(monkeypatch)

    def raise_not_found(session, owner, repo):
        raise GitHubAPIError(404, "not found")

    monkeypatch.setattr(
        dashboard_app_module,
        "run_extraction_pipeline",
        raise_not_found,
    )

    client = app.test_client()
    csrf_token = get_csrf_token(client, "/repositories/new")

    response = client.post(
        "/repositories/new",
        data={
            "owner": "nobody",
            "repo": "missing",
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 200
    assert b"Repository not found" in response.data


def test_add_repository_post_rejects_invalid_owner_name(monkeypatch):
    client = app.test_client()
    csrf_token = get_csrf_token(client, "/repositories/new")

    response = client.post(
        "/repositories/new",
        data={
            "owner": "not a valid owner!",
            "repo": "linux",
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 200
    assert b"must be valid GitHub names" in response.data


def test_add_repository_post_rate_limits_after_repeated_requests(
    monkeypatch,
):
    make_session_local(monkeypatch)
    monkeypatch.setattr(
        dashboard_app_module,
        "run_extraction_pipeline",
        lambda session, owner, repo: {
            "repository": make_repository(repository_id=5)
        },
    )
    monkeypatch.setattr(
        dashboard_app_module,
        "add_repository_rate_limiter",
        RateLimiter(max_requests=2, window_seconds=3600),
    )

    client = app.test_client()

    for _ in range(2):
        csrf_token = get_csrf_token(client, "/repositories/new")
        response = client.post(
            "/repositories/new",
            data={
                "owner": "torvalds",
                "repo": "linux",
                "csrf_token": csrf_token,
            },
        )
        assert response.status_code == 302

    csrf_token = get_csrf_token(client, "/repositories/new")
    response = client.post(
        "/repositories/new",
        data={
            "owner": "torvalds",
            "repo": "linux",
            "csrf_token": csrf_token,
        },
    )

    assert response.status_code == 429
    assert b"Too many repositories added recently" in response.data
