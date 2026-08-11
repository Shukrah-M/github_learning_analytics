"""
Flask dashboard for the GitHub-Based Learning Analytics System.

Run with:

    python dashboard/app.py

Then open https://127.0.0.1:5000 in a browser, or
https://<this machine's LAN IP>:5000 from another device (phone,
tablet, another computer) on the same network. If
dashboard/certs/dashboard.pem and dashboard-key.pem (generated with
mkcert, see README) aren't present, the server falls back to plain
HTTP on the same port.

The dashboard is open: no account is needed to browse repositories or
add new ones via /repositories/new.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402
from flask import (  # noqa: E402
    Flask,
    Response,
    abort,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402

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
    donut_color,
    format_category_label,
    render_bar_chart,
    render_donut_chart,
    render_sparkline,
)
from dashboard.csrf import generate_csrf_token, validate_csrf_token  # noqa: E402
from dashboard.rate_limit import RateLimiter  # noqa: E402
from dashboard.reports import (  # noqa: E402
    build_all_repositories_summary_csv,
    build_repository_report_csv,
)
from database.database import SessionLocal  # noqa: E402
from extractor.github_api import GitHubAPIError  # noqa: E402
from extractor.pipeline import run_extraction_pipeline  # noqa: E402


load_dotenv()

MODEL_PATH = PROJECT_ROOT / "models" / "nlp_classifier.joblib"

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

if not FLASK_SECRET_KEY:
    raise RuntimeError(
        "FLASK_SECRET_KEY is not set. Add one to .env, e.g. by running:\n"
        '  python -c "import secrets; print(secrets.token_hex(32))"\n'
        "and adding FLASK_SECRET_KEY=<the output> to .env."
    )

GITHUB_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")

# The GitHub token behind /repositories/new is shared by every visitor
# (there's no login), so this caps how many extraction runs any one
# client can trigger per hour to blunt casual abuse if this instance
# is reachable publicly.
ADD_REPOSITORY_RATE_LIMIT = 5
ADD_REPOSITORY_RATE_WINDOW_SECONDS = 60 * 60
add_repository_rate_limiter = RateLimiter(
    max_requests=ADD_REPOSITORY_RATE_LIMIT,
    window_seconds=ADD_REPOSITORY_RATE_WINDOW_SECONDS,
)

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Trust one hop of X-Forwarded-For/-Proto so request.remote_addr (used
# for rate limiting) and url_for's scheme are correct when running
# behind a reverse proxy, which most hosting platforms use.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)


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


def gather_repository_analysis(
    db_session, repository_id: int
) -> dict[str, Any] | None:
    """
    Compute everything one repository's page/export needs: its
    behavioural metrics, experimentation score (relative to every
    other repository currently in the database), and NLP
    classification. Returns None if the repository doesn't exist.
    """
    repository = get_repository_by_id(db_session, repository_id)

    if repository is None:
        return None

    all_repositories = get_all_repositories(db_session)

    repository_metrics = {
        repo.id: analyse_repository(repo.id) for repo in all_repositories
    }

    scores = calculate_experimentation_scores(repository_metrics)

    metrics = repository_metrics[repository_id]
    score = scores[repository_id]

    nlp_result = None
    nlp_error = None

    if not MODEL_PATH.exists():
        nlp_error = (
            "NLP model not trained yet. "
            "Run: python -m scripts.train_nlp_classifier"
        )
    else:
        texts = get_repository_texts(db_session, repository_id)

        if not texts:
            nlp_error = "No repository text available for classification."
        else:
            nlp_result = predict_repository_texts(
                [item["text"] for item in texts],
                [item["artifact_type"] for item in texts],
                MODEL_PATH,
            )

    return {
        "repository": repository,
        "metrics": metrics,
        "score": score,
        "nlp_result": nlp_result,
        "nlp_error": nlp_error,
    }


def describe_github_error(error: GitHubAPIError) -> str:
    """Translate a GitHub API error into a user-facing message."""
    if error.status_code == 404:
        return (
            "Repository not found. Check the owner and repository name "
            "(private repositories need access from the GitHub token "
            "configured in .env)."
        )

    if error.status_code in (401, 403):
        return (
            "GitHub rejected the request (invalid token or rate limit "
            "exceeded). Check GITHUB_TOKEN in .env."
        )

    return f"GitHub API error ({error.status_code}). Please try again."


@app.route("/repositories/new", methods=["GET", "POST"])
def add_repository():
    if request.method == "GET":
        return render_template(
            "add_repository.html",
            csrf_token=generate_csrf_token(),
            error=None,
            owner="",
            repo="",
        )

    if not validate_csrf_token(request.form.get("csrf_token")):
        abort(400)

    client_key = request.remote_addr or "unknown"

    if not add_repository_rate_limiter.is_allowed(client_key):
        return (
            render_template(
                "add_repository.html",
                csrf_token=generate_csrf_token(),
                error=(
                    "Too many repositories added recently from this "
                    "network. Please wait a while and try again."
                ),
                owner=request.form.get("owner", "").strip(),
                repo=request.form.get("repo", "").strip(),
            ),
            429,
        )

    owner = request.form.get("owner", "").strip()
    repo = request.form.get("repo", "").strip()

    if not GITHUB_NAME_PATTERN.match(owner) or not GITHUB_NAME_PATTERN.match(
        repo
    ):
        return render_template(
            "add_repository.html",
            csrf_token=generate_csrf_token(),
            error=(
                "Owner and repository must be valid GitHub names "
                "(letters, numbers, '.', '_', '-')."
            ),
            owner=owner,
            repo=repo,
        )

    db_session = SessionLocal()

    try:
        try:
            summary = run_extraction_pipeline(db_session, owner, repo)
        except GitHubAPIError as error:
            return render_template(
                "add_repository.html",
                csrf_token=generate_csrf_token(),
                error=describe_github_error(error),
                owner=owner,
                repo=repo,
            )

        return redirect(
            url_for(
                "repository_detail",
                repository_id=summary["repository"].id,
            )
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
        db_session.close()


@app.route("/")
def index():
    db_session = SessionLocal()

    try:
        repositories = get_all_repositories(db_session)

        rows = [
            {
                "repository": repository,
                "commit_count": len(
                    get_commits(db_session, repository.id)
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
        db_session.close()


@app.route("/repository/<int:repository_id>")
def repository_detail(repository_id: int):
    db_session = SessionLocal()

    try:
        analysis = gather_repository_analysis(db_session, repository_id)

        if analysis is None:
            abort(404)

        commits = get_commits(db_session, repository_id)
        weekly_commit_counts = build_weekly_commit_counts(commits)

        score = analysis["score"]
        nlp_result = analysis["nlp_result"]

        charts = {
            "score_bar": render_bar_chart(
                [
                    ("Engagement", score["engagement_score"]),
                    ("Regularity", score["regularity_score"]),
                    ("Issue Refinement", score["refinement_score"]),
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

        category_rows = []

        if nlp_result:
            distribution = nlp_result["category_distribution"]
            total_classified = sum(distribution.values())

            category_rows = [
                {
                    "label": format_category_label(label),
                    "count": count,
                    "percent": (
                        count / total_classified * 100
                        if total_classified
                        else 0
                    ),
                    "color": donut_color(label),
                }
                for label, count in distribution.items()
            ]

        return render_template(
            "repository_detail.html",
            repository=analysis["repository"],
            metric_groups=build_metric_groups(analysis["metrics"]),
            score=score,
            nlp_result=nlp_result,
            nlp_error=analysis["nlp_error"],
            category_rows=category_rows,
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
        db_session.close()


@app.route("/repository/<int:repository_id>/export.csv")
def export_repository_csv(repository_id: int):
    db_session = SessionLocal()

    try:
        analysis = gather_repository_analysis(db_session, repository_id)

        if analysis is None:
            abort(404)

        repository = analysis["repository"]

        csv_content = build_repository_report_csv(
            repository,
            analysis["metrics"],
            analysis["score"],
            analysis["nlp_result"],
        )

        filename = f"{repository.owner}-{repository.name}-report.csv"

        return Response(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
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
        db_session.close()


@app.route("/export.csv")
def export_all_repositories_csv():
    db_session = SessionLocal()

    try:
        repositories = get_all_repositories(db_session)

        rows = [
            gather_repository_analysis(db_session, repository.id)
            for repository in repositories
        ]

        csv_content = build_all_repositories_summary_csv(rows)

        return Response(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": (
                    'attachment; filename="all-repositories-report.csv"'
                )
            },
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
        db_session.close()


@app.errorhandler(404)
def handle_not_found(_error):
    return (
        render_template(
            "error.html",
            message="Repository not found.",
        ),
        404,
    )


CERT_PATH = PROJECT_ROOT / "dashboard" / "certs" / "dashboard.pem"
KEY_PATH = PROJECT_ROOT / "dashboard" / "certs" / "dashboard-key.pem"


if __name__ == "__main__":
    ssl_context = None

    if CERT_PATH.exists() and KEY_PATH.exists():
        ssl_context = (str(CERT_PATH), str(KEY_PATH))
    else:
        print(
            "No TLS certificate found at dashboard/certs/ — running "
            "over plain HTTP. See README for how to generate one "
            "with mkcert."
        )

    # Off by default: the Werkzeug debugger is a remote-code-execution
    # risk if this process is ever reachable from an untrusted network.
    # Set FLASK_DEBUG=true in .env for local development only.
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=debug_mode,
        ssl_context=ssl_context,
    )
