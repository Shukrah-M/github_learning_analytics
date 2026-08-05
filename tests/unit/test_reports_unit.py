from types import SimpleNamespace

from dashboard.reports import (
    build_all_repositories_summary_csv,
    build_repository_report_csv,
)


def make_repository(owner="octocat", name="hello-world", language="Python"):
    return SimpleNamespace(
        owner=owner,
        name=name,
        language=language,
        description="An example repository.",
    )


def test_build_repository_report_csv_includes_all_sections():
    repository = make_repository()

    metrics = {
        "commit_frequency_per_week": 2.0,
        "active_day_ratio": 0.5,
    }

    score = {
        "experimentation_intensity_score": 60.0,
        "engagement_score": 0.6,
        "regularity_score": 0.4,
        "refinement_score": None,
        "integration_score": 0.8,
    }

    nlp_result = {
        "learning_quality_indicator": 40.0,
        "category_distribution": {"refinement": 4, "none": 6},
    }

    csv_content = build_repository_report_csv(
        repository, metrics, score, nlp_result
    )

    assert "owner,octocat" in csv_content
    assert "commit_frequency_per_week,2.0" in csv_content
    assert "experimentation_intensity_score,60.0" in csv_content
    assert "category_refinement,4" in csv_content
    assert "learning_quality_indicator_percent,40.0" in csv_content


def test_build_repository_report_csv_handles_missing_nlp_result():
    repository = make_repository()

    csv_content = build_repository_report_csv(
        repository,
        {"commit_frequency_per_week": 1.0},
        {"experimentation_intensity_score": None},
        nlp_result=None,
    )

    assert "nlp_classification" not in csv_content
    assert "owner,octocat" in csv_content


def test_build_all_repositories_summary_csv_has_one_row_per_repository():
    rows = [
        {
            "repository": make_repository(name="repo-one"),
            "metrics": {
                "commit_frequency_per_week": 3.0,
                "active_day_ratio": 0.2,
                "issue_closure_rate": 0.5,
                "pull_request_merge_rate": 1.0,
            },
            "score": {"experimentation_intensity_score": 70.0},
        },
        {
            "repository": make_repository(name="repo-two"),
            "metrics": {},
            "score": {"experimentation_intensity_score": None},
        },
    ]

    csv_content = build_all_repositories_summary_csv(rows)
    lines = csv_content.strip().splitlines()

    assert len(lines) == 3
    assert "repo-one" in lines[1]
    assert "repo-two" in lines[2]
