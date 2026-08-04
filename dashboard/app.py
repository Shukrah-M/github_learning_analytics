"""
Flask dashboard for the GitHub-Based Learning Analytics System.

Run with:

    python dashboard/app.py

Then open http://127.0.0.1:5000 in a browser, or
http://<this machine's LAN IP>:5000 from another device (phone,
tablet, another computer) on the same network.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, abort, render_template  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402

from analytics.data_access import (  # noqa: E402
    get_all_repositories,
    get_commits,
    get_repository_by_id,
)
from analytics.experimentation_score import (  # noqa: E402
    calculate_experimentation_scores,
)
from analytics.nlp.classifier import predict_repository_texts  # noqa: E402
from analytics.nlp.repository_texts import get_repository_texts  # noqa: E402
from analytics.repository_analysis import analyse_repository  # noqa: E402
from dashboard.charts import (  # noqa: E402
    render_bar_chart,
    render_donut_chart,
    render_sparkline,
)
from database.database import SessionLocal  # noqa: E402


MODEL_PATH = PROJECT_ROOT / "models" / "nlp_classifier.joblib"

app = Flask(__name__)


def format_metric(value: Any, kind: str) -> str:
    """Format a behavioural metric value for display."""
    if value is None:
        return "N/A"

    if kind == "ratio":
        return f"{float(value):.1%}"

    if kind == "days":
        return f"{float(value):.1f} days"

    if kind == "rate":
        return f"{float(value):.2f} / week"

    if kind == "count":
        return str(int(value))

    return f"{float(value):.2f}"


def build_metric_groups(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    """Group behavioural metrics into display cards."""
    return [
        {
            "title": "Commit activity",
            "rows": [
                (
                    "Commit frequency",
                    format_metric(
                        metrics.get("commit_frequency_per_week"), "rate"
                    ),
                ),
                (
                    "Active-day ratio",
                    format_metric(metrics.get("active_day_ratio"), "ratio"),
                ),
                (
                    "Commit interval variability",
                    format_metric(
                        metrics.get("commit_interval_std_days"), "days"
                    ),
                ),
                (
                    "Longest inactivity gap",
                    format_metric(
                        metrics.get("longest_inactivity_gap_days"), "days"
                    ),
                ),
            ],
        },
        {
            "title": "Issue activity",
            "rows": [
                (
                    "Total issues",
                    format_metric(metrics.get("total_issues"), "count"),
                ),
                (
                    "Issue closure rate",
                    format_metric(
                        metrics.get("issue_closure_rate"), "ratio"
                    ),
                ),
                (
                    "Mean comments per issue",
                    format_metric(
                        metrics.get("mean_comments_per_issue"), "plain"
                    ),
                ),
                (
                    "Mean issue resolution time",
                    format_metric(
                        metrics.get("mean_issue_resolution_days"), "days"
                    ),
                ),
            ],
        },
        {
            "title": "Pull request activity",
            "rows": [
                (
                    "Total pull requests",
                    format_metric(
                        metrics.get("total_pull_requests"), "count"
                    ),
                ),
                (
                    "Merge rate",
                    format_metric(
                        metrics.get("pull_request_merge_rate"), "ratio"
                    ),
                ),
                (
                    "Reviewed PR ratio",
                    format_metric(
                        metrics.get("reviewed_pull_request_ratio"), "ratio"
                    ),
                ),
                (
                    "Mean PR cycle time",
                    format_metric(
                        metrics.get("mean_pull_request_cycle_days"), "days"
                    ),
                ),
            ],
        },
    ]


def build_weekly_commit_counts(commits) -> list[int]:
    """Aggregate commits into calendar-week counts for the sparkline."""
    buckets: dict[tuple[int, int], int] = {}

    for commit in commits:
        if commit.committed_at is None:
            continue

        iso_year, iso_week, _ = commit.committed_at.isocalendar()
        key = (iso_year, iso_week)
        buckets[key] = buckets.get(key, 0) + 1

    return [buckets[key] for key in sorted(buckets)]


@app.route("/")
def index():
    session = SessionLocal()

    try:
        repositories = get_all_repositories(session)

        rows = [
            {
                "repository": repository,
                "commit_count": len(
                    get_commits(session, repository.id)
                ),
            }
            for repository in repositories
        ]

        return render_template("index.html", rows=rows)

    except SQLAlchemyError as error:
        return (
            render_template(
                "error.html",
                message=f"Could not reach the database: {error}",
            ),
            500,
        )

    finally:
        session.close()


@app.route("/repository/<int:repository_id>")
def repository_detail(repository_id: int):
    session = SessionLocal()

    try:
        repository = get_repository_by_id(session, repository_id)

        if repository is None:
            abort(404)

        all_repositories = get_all_repositories(session)

        repository_metrics = {
            repo.id: analyse_repository(repo.id)
            for repo in all_repositories
        }

        scores = calculate_experimentation_scores(repository_metrics)

        metrics = repository_metrics[repository_id]
        score = scores[repository_id]

        commits = get_commits(session, repository_id)
        weekly_commit_counts = build_weekly_commit_counts(commits)

        nlp_result = None
        nlp_error = None

        if not MODEL_PATH.exists():
            nlp_error = (
                "NLP model not trained yet. "
                "Run: python -m scripts.train_nlp_classifier"
            )
        else:
            texts = get_repository_texts(session, repository_id)

            if not texts:
                nlp_error = (
                    "No repository text available for classification."
                )
            else:
                nlp_result = predict_repository_texts(
                    [item["text"] for item in texts],
                    [item["artifact_type"] for item in texts],
                    MODEL_PATH,
                )

        charts = {
            "score_bar": render_bar_chart(
                [
                    ("Engagement", score["engagement_score"]),
                    ("Regularity", score["regularity_score"]),
                    ("Refinement", score["refinement_score"]),
                    ("Integration", score["integration_score"]),
                ]
            ),
            "nlp_donut": (
                render_donut_chart(nlp_result["category_distribution"])
                if nlp_result
                else None
            ),
            "commit_sparkline": render_sparkline(weekly_commit_counts),
        }

        return render_template(
            "repository_detail.html",
            repository=repository,
            metric_groups=build_metric_groups(metrics),
            score=score,
            nlp_result=nlp_result,
            nlp_error=nlp_error,
            charts=charts,
        )

    except SQLAlchemyError as error:
        return (
            render_template(
                "error.html",
                message=f"Could not reach the database: {error}",
            ),
            500,
        )

    finally:
        session.close()


@app.errorhandler(404)
def handle_not_found(_error):
    return (
        render_template(
            "error.html",
            message="Repository not found.",
        ),
        404,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
