"""
Plain-English explanations for the dashboard's two headline scores.

The dissertation's own user evaluation (SUS = 84.0/100, 20 participants)
found strong usability but flagged interpretability as the main
weakness: 95% had difficulty understanding what the metrics meant and
85% asked for clearer explanations. These functions generate the
per-repository "why did I get this score" text that the dashboard
shows alongside each score, and load the NLP classifier's live
validation numbers so the accuracy caveat never goes stale.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
NLP_VALIDATION_SUMMARY_PATH = (
    PROJECT_ROOT / "results" / "nlp" / "evaluation_summary.json"
)

MODEL_DISPLAY_NAMES = {
    "linear_svc": "Linear SVC",
    "logistic_regression": "Logistic Regression",
    "complement_nb": "Complement Naive Bayes",
}


def _format_percent(fraction: float | None) -> str | None:
    if fraction is None:
        return None

    return f"{fraction * 100:.1f}%"


def load_nlp_validation_summary() -> dict[str, Any] | None:
    """
    Load the NLP classifier's live cross-validation results.

    Returns None if the summary hasn't been generated yet (e.g. the
    classifier hasn't been trained), so callers can fall back to a
    generic "not yet validated" message instead of failing.
    """
    if not NLP_VALIDATION_SUMMARY_PATH.exists():
        return None

    try:
        with open(NLP_VALIDATION_SUMMARY_PATH, encoding="utf-8") as handle:
            summary = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None

    selected_model = summary.get("selected_model")

    return {
        "selected_model": MODEL_DISPLAY_NAMES.get(
            selected_model, selected_model
        ),
        "training_records": summary.get("training_records"),
        "accuracy_percent": _format_percent(summary.get("accuracy_mean")),
        "macro_f1_percent": _format_percent(summary.get("macro_f1_mean")),
        "weighted_f1_percent": _format_percent(
            summary.get("weighted_f1_mean")
        ),
        "cohen_kappa_interpretation": summary.get(
            "cohen_kappa_interpretation"
        ),
    }


_SCORE_DIMENSIONS = (
    ("Engagement", "engagement_score"),
    ("Regularity", "regularity_score"),
    ("Issue Refinement", "refinement_score"),
    ("Integration", "integration_score"),
)


def _missing_dimension_reason(dimension_key: str, metrics: dict[str, Any]) -> str:
    """Give the most specific reason available for why a dimension is N/A."""
    if dimension_key == "refinement_score":
        return "this repository has no recorded issues"

    if dimension_key == "integration_score":
        return "this repository has no recorded pull requests"

    if dimension_key in ("engagement_score", "regularity_score"):
        has_interval = metrics.get("commit_interval_std_days") is not None
        has_gap = metrics.get("longest_inactivity_gap_days") is not None
        has_frequency = metrics.get("commit_frequency_per_week") is not None

        if dimension_key == "regularity_score" and not has_interval and not has_gap:
            return (
                "there aren't enough commits with valid timestamps to "
                "measure commit spacing or inactivity gaps"
            )

        if dimension_key == "engagement_score" and not has_frequency:
            return "there is no recorded commit activity"

    return "there isn't enough data to calculate it yet"


def explain_experimentation_score(
    score: dict[str, Any],
    metrics: dict[str, Any],
) -> str:
    """
    Build the dynamic "why you got this score" sentence for the
    Experimentation Intensity Score, naming which dimensions
    contributed and, for any that are N/A, why.
    """
    final_score = score.get("experimentation_intensity_score")

    if final_score is None:
        return (
            "None of the four behavioural dimensions could be "
            "calculated for this repository yet, so no overall score "
            "is available. Add more commit, issue or pull-request "
            "activity and check back."
        )

    applicable: list[str] = []
    missing: list[str] = []

    for label, key in _SCORE_DIMENSIONS:
        value = score.get(key)

        if value is None:
            reason = _missing_dimension_reason(key, metrics)
            missing.append(f"{label} is N/A because {reason}")
        else:
            applicable.append(f"{label} ({value:.2f})")

    sentences = [
        f"This score of {final_score:.1f}/100 is the average of "
        f"{len(applicable)} applicable dimension"
        f"{'s' if len(applicable) != 1 else ''}: "
        + ", ".join(applicable)
        + "."
    ]

    if missing:
        sentences.append("; ".join(missing) + ".")

    return " ".join(sentences)


def explain_learning_quality_indicator(
    nlp_result: dict[str, Any] | None,
) -> str:
    """
    Build the dynamic "why you got this score" sentence for the
    Learning Quality Indicator, based on the actual category counts
    for this repository.
    """
    if not nlp_result:
        return (
            "No repository text was available to classify, so this "
            "indicator could not be calculated."
        )

    distribution = nlp_result.get("category_distribution", {})
    total = sum(distribution.values())
    indicator = nlp_result.get("learning_quality_indicator")

    if not total or indicator is None:
        return (
            "No repository text was available to classify, so this "
            "indicator could not be calculated."
        )

    substantive = {
        label: count
        for label, count in distribution.items()
        if label != "none" and count > 0
    }

    none_count = distribution.get("none", 0)

    base = (
        f"Of the {total} pieces of repository text analysed, "
        f"{total - none_count} ({indicator:.1f}%) were classified as "
        "substantive learning-oriented language"
    )

    if substantive:
        top_label, top_count = max(substantive.items(), key=lambda item: item[1])
        base += (
            f", most often '{top_label.replace('_', ' ')}' ({top_count})"
        )

    base += f"; the remaining {none_count} were classified as routine text."

    return base
