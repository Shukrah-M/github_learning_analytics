"""Train, evaluate and apply the repository-text NLP classifier."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    cohen_kappa_score,
    f1_score,
)
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold
from sklearn.naive_bayes import ComplementNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.svm import LinearSVC


LABELS = [
    "problem_identification",
    "experimentation",
    "reflection",
    "refinement",
    "none",
]

SUBSTANTIVE_LABELS = {
    "problem_identification",
    "experimentation",
    "reflection",
    "refinement",
}

# How many repeated fold assignments to average the comparison
# metrics over. This matters because the smallest class currently
# has only two examples, which forces a 2-fold split; a single
# 2-fold run is noisy, so several reshuffled repeats are averaged
# to get a more stable estimate.
CROSS_VALIDATION_REPEATS = 5

# Minority classes are duplicated (within the training fold only)
# up to this fraction of the largest class's size. This never
# removes majority-class examples and never touches validation or
# test data, so it cannot leak information across a CV split.
OVERSAMPLING_CAP_RATIO = 0.5

RANDOM_STATE = 42

FEATURE_COLUMNS = ["text", "artifact_type"]


def clean_text(value: Any) -> str:
    """Clean repository text while preserving meaningful words."""
    if value is None:
        return ""

    text = str(value).strip()

    if not text or text.lower() == "nan":
        return ""

    text = text.lower()

    # Remove URLs.
    text = re.sub(
        r"https?://\S+|www\.\S+",
        " ",
        text,
    )

    # Remove fenced and inline code.
    text = re.sub(
        r"```.*?```",
        " ",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"`[^`]*`",
        " ",
        text,
    )

    # Replace repository separators with spaces.
    text = re.sub(
        r"[/_\\-]+",
        " ",
        text,
    )

    # Retain letters, numbers, apostrophes and whitespace.
    text = re.sub(
        r"[^a-z0-9'\s]",
        " ",
        text,
    )

    # Remove excessive whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def clean_artifact_type(value: Any) -> str:
    """Normalise the artifact-type feature."""
    if value is None:
        return "unknown"

    text = str(value).strip().lower()

    return text or "unknown"


def build_feature_transformer() -> ColumnTransformer:
    """
    Combine word TF-IDF, character TF-IDF and the artifact-type
    category into a single feature matrix.

    Character n-grams help with short, code-styled text such as
    commit prefixes ("fix(docker):", "chore:") that word n-grams
    alone tend to under-represent. The artifact type is included
    because commits, issues and PR reviews use systematically
    different language for the same underlying behaviour.
    """
    return ColumnTransformer(
        transformers=[
            (
                "word_tfidf",
                TfidfVectorizer(
                    preprocessor=clean_text,
                    lowercase=False,
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=0.95,
                    max_features=5000,
                    sublinear_tf=True,
                ),
                "text",
            ),
            (
                "char_tfidf",
                TfidfVectorizer(
                    preprocessor=clean_text,
                    lowercase=False,
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=1,
                    max_df=0.95,
                    max_features=3000,
                    sublinear_tf=True,
                ),
                "text",
            ),
            (
                "artifact_type",
                OneHotEncoder(handle_unknown="ignore"),
                ["artifact_type"],
            ),
        ]
    )


def build_pipeline(classifier: Any | None = None) -> Pipeline:
    """Create the combined feature-extraction and classifier pipeline."""
    if classifier is None:
        classifier = LogisticRegression(
            solver="lbfgs",
            class_weight="balanced",
            max_iter=2000,
            random_state=RANDOM_STATE,
        )

    return Pipeline(
        steps=[
            ("features", build_feature_transformer()),
            ("classifier", classifier),
        ]
    )


def candidate_classifiers() -> dict[str, Any]:
    """
    Candidate classifiers compared during training.

    Only .predict() is required downstream (no calibrated
    probabilities are used), so LinearSVC is used directly rather
    than wrapped in probability calibration, which would need extra
    internal folds that the smallest class (currently 2 examples)
    cannot reliably support.
    """
    return {
        "logistic_regression": LogisticRegression(
            solver="lbfgs",
            class_weight="balanced",
            max_iter=2000,
            random_state=RANDOM_STATE,
        ),
        "linear_svc": LinearSVC(
            class_weight="balanced",
            max_iter=5000,
            random_state=RANDOM_STATE,
        ),
        "complement_nb": ComplementNB(),
    }


def oversample_training_rows(
    frame: pd.DataFrame,
    label_column: str = "final_label",
    cap_ratio: float = OVERSAMPLING_CAP_RATIO,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Duplicate minority-class rows so no class has fewer examples
    than cap_ratio times the largest class in this frame.

    This must only ever be called on a training fold. Applying it
    before a CV split (or to validation/test data) would leak
    duplicated examples across the split and inflate the score.
    """
    counts = frame[label_column].value_counts()

    if counts.empty:
        return frame

    majority_count = int(counts.max())
    target_count = max(1, int(round(majority_count * cap_ratio)))

    generator = np.random.RandomState(random_state)
    resampled_parts = [frame]

    for label, count in counts.items():
        count = int(count)

        if count >= target_count:
            continue

        deficit = target_count - count
        label_rows = frame[frame[label_column] == label]

        extra_indices = generator.choice(
            label_rows.index.to_numpy(),
            size=deficit,
            replace=True,
        )

        resampled_parts.append(frame.loc[extra_indices])

    return pd.concat(
        resampled_parts,
        ignore_index=True,
    )


def prepare_training_data(
    csv_path: Path,
) -> pd.DataFrame:
    """Load and validate the manually coded dataset."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Training dataset not found: {csv_path}"
        )

    try:
        frame = pd.read_csv(
            csv_path,
            encoding="utf-8-sig",
        )
    except UnicodeDecodeError:
        frame = pd.read_csv(
            csv_path,
            encoding="cp1252",
        )

    required_columns = {
        "text",
        "final_label",
    }

    missing_columns = (
        required_columns - set(frame.columns)
    )

    if missing_columns:
        raise ValueError(
            "Training CSV is missing columns: "
            + ", ".join(sorted(missing_columns))
        )

    frame["text"] = (
        frame["text"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    if "artifact_type" in frame.columns:
        frame["artifact_type"] = frame[
            "artifact_type"
        ].apply(clean_artifact_type)
    else:
        frame["artifact_type"] = "unknown"

    frame["final_label"] = (
        frame["final_label"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    invalid_labels = sorted(
        set(frame["final_label"]) - set(LABELS)
    )

    if invalid_labels:
        raise ValueError(
            "Invalid labels found: "
            + ", ".join(invalid_labels)
        )

    frame = frame[
        frame["text"].str.len() > 0
    ].copy()

    conflicting_texts = (
        frame.groupby("text")["final_label"]
        .nunique()
    )

    conflicting_texts = conflicting_texts[
        conflicting_texts > 1
    ]

    if not conflicting_texts.empty:
        raise ValueError(
            "Some identical texts have conflicting labels. "
            "Review the gold-standard CSV."
        )

    frame = frame.drop_duplicates(
        subset=["text", "final_label"]
    ).reset_index(drop=True)

    missing_expected_labels = (
        set(LABELS)
        - set(frame["final_label"])
    )

    if missing_expected_labels:
        raise ValueError(
            "The following required classes have no examples: "
            + ", ".join(sorted(missing_expected_labels))
        )

    class_counts = frame[
        "final_label"
    ].value_counts()

    if class_counts.min() < 2:
        raise ValueError(
            "Every category requires at least two examples. "
            f"Current counts: {class_counts.to_dict()}"
        )

    return frame


def evaluate_candidate(
    frame: pd.DataFrame,
    classifier: Any,
    n_splits: int,
    n_repeats: int,
) -> dict[str, float]:
    """
    Estimate a candidate classifier's cross-validated performance.

    Oversampling is applied separately inside every fold's training
    split so the held-out fold in each repeat is never touched.
    """
    cross_validator = RepeatedStratifiedKFold(
        n_splits=n_splits,
        n_repeats=n_repeats,
        random_state=RANDOM_STATE,
    )

    accuracies: list[float] = []
    macro_f1_scores: list[float] = []
    weighted_f1_scores: list[float] = []

    for train_positions, test_positions in cross_validator.split(
        frame,
        frame["final_label"],
    ):
        train_frame = oversample_training_rows(
            frame.iloc[train_positions].reset_index(drop=True)
        )
        test_frame = frame.iloc[test_positions]

        pipeline = build_pipeline(clone(classifier))
        pipeline.fit(
            train_frame[FEATURE_COLUMNS],
            train_frame["final_label"],
        )

        predictions = pipeline.predict(
            test_frame[FEATURE_COLUMNS]
        )

        accuracies.append(
            accuracy_score(
                test_frame["final_label"],
                predictions,
            )
        )
        macro_f1_scores.append(
            f1_score(
                test_frame["final_label"],
                predictions,
                labels=LABELS,
                average="macro",
                zero_division=0,
            )
        )
        weighted_f1_scores.append(
            f1_score(
                test_frame["final_label"],
                predictions,
                labels=LABELS,
                average="weighted",
                zero_division=0,
            )
        )

    return {
        "accuracy_mean": float(np.mean(accuracies)),
        "macro_f1_mean": float(np.mean(macro_f1_scores)),
        "weighted_f1_mean": float(np.mean(weighted_f1_scores)),
    }


def cross_val_predict_with_oversampling(
    frame: pd.DataFrame,
    classifier: Any,
    n_splits: int,
) -> list[str]:
    """
    Produce one out-of-fold prediction per row for the report and
    confusion matrix, using a single (non-repeated) stratified split
    so every row is predicted exactly once.
    """
    cross_validator = StratifiedKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    predictions = np.empty(len(frame), dtype=object)

    for train_positions, test_positions in cross_validator.split(
        frame,
        frame["final_label"],
    ):
        train_frame = oversample_training_rows(
            frame.iloc[train_positions].reset_index(drop=True)
        )
        test_frame = frame.iloc[test_positions]

        pipeline = build_pipeline(clone(classifier))
        pipeline.fit(
            train_frame[FEATURE_COLUMNS],
            train_frame["final_label"],
        )

        predictions[test_positions] = pipeline.predict(
            test_frame[FEATURE_COLUMNS]
        )

    return predictions.tolist()


def interpret_cohen_kappa(kappa: float) -> str:
    """
    Label a kappa value using the Landis & Koch (1977) benchmark
    scale, the standard reference for interpreting chance-corrected
    agreement.
    """
    if kappa < 0:
        return "poor (worse than chance)"
    if kappa <= 0.20:
        return "slight"
    if kappa <= 0.40:
        return "fair"
    if kappa <= 0.60:
        return "moderate"
    if kappa <= 0.80:
        return "substantial"
    return "almost perfect"


def train_and_evaluate(
    training_csv: Path,
    model_path: Path,
    results_directory: Path,
) -> dict[str, Any]:
    """
    Compare candidate classifiers, cross-validate, train and save
    the best-performing NLP classifier.
    """
    frame = prepare_training_data(
        training_csv
    )

    results_directory.mkdir(
        parents=True,
        exist_ok=True,
    )
    model_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    class_counts = frame[
        "final_label"
    ].value_counts()

    minimum_class_count = int(
        class_counts.min()
    )

    number_of_folds = min(
        5,
        minimum_class_count,
    )

    if number_of_folds < 2:
        raise ValueError(
            "Insufficient examples for cross-validation."
        )

    comparison_rows: list[dict[str, Any]] = []
    best_model_name: str | None = None
    best_classifier: Any = None
    best_scores: dict[str, float] | None = None

    for model_name, classifier in candidate_classifiers().items():
        scores = evaluate_candidate(
            frame,
            classifier,
            n_splits=number_of_folds,
            n_repeats=CROSS_VALIDATION_REPEATS,
        )

        comparison_rows.append(
            {
                "model": model_name,
                **scores,
            }
        )

        if (
            best_scores is None
            or scores["macro_f1_mean"] > best_scores["macro_f1_mean"]
        ):
            best_model_name = model_name
            best_classifier = classifier
            best_scores = scores

    comparison_frame = pd.DataFrame(
        comparison_rows
    ).sort_values(
        "macro_f1_mean",
        ascending=False,
    )

    comparison_path = (
        results_directory
        / "model_comparison.csv"
    )

    comparison_frame.to_csv(
        comparison_path,
        index=False,
    )

    cross_validated_predictions = cross_val_predict_with_oversampling(
        frame,
        best_classifier,
        n_splits=number_of_folds,
    )

    # Chance-corrected agreement between the classifier and the human
    # gold-standard labels, on the same out-of-fold predictions used
    # for the report/confusion matrix above. Unlike raw accuracy, this
    # is not inflated by the labels' uneven class sizes.
    cohen_kappa = cohen_kappa_score(
        frame["final_label"],
        cross_validated_predictions,
        labels=LABELS,
    )

    report = classification_report(
        frame["final_label"],
        cross_validated_predictions,
        labels=LABELS,
        target_names=LABELS,
        output_dict=True,
        zero_division=0,
    )

    report_frame = (
        pd.DataFrame(report)
        .transpose()
    )

    report_path = (
        results_directory
        / "classification_report.csv"
    )

    report_frame.to_csv(
        report_path,
        index=True,
    )

    figure, axis = plt.subplots(
        figsize=(10, 8)
    )

    ConfusionMatrixDisplay.from_predictions(
        frame["final_label"],
        cross_validated_predictions,
        labels=LABELS,
        display_labels=LABELS,
        xticks_rotation=45,
        ax=axis,
    )

    axis.set_title(
        "Cross-Validated NLP Confusion Matrix "
        f"({best_model_name})"
    )

    figure.tight_layout()

    confusion_matrix_path = (
        results_directory
        / "confusion_matrix.png"
    )

    figure.savefig(
        confusion_matrix_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)

    metrics = {
        "training_records": int(len(frame)),
        "cross_validation_folds": number_of_folds,
        "cross_validation_repeats": CROSS_VALIDATION_REPEATS,
        "selected_model": best_model_name,
        "class_distribution": {
            label: int(
                class_counts.get(label, 0)
            )
            for label in LABELS
        },
        "accuracy_mean": best_scores["accuracy_mean"],
        "macro_f1_mean": best_scores["macro_f1_mean"],
        "weighted_f1_mean": best_scores["weighted_f1_mean"],
        "cohen_kappa": float(cohen_kappa),
        "cohen_kappa_interpretation": interpret_cohen_kappa(cohen_kappa),
        "model_comparison_rows": comparison_rows,
        "scikit_learn_version":
            sklearn.__version__,
    }

    metrics_path = (
        results_directory
        / "evaluation_summary.json"
    )

    metrics_path.write_text(
        json.dumps(
            metrics,
            indent=4,
        ),
        encoding="utf-8",
    )

    # Fit the final model on all coded records, oversampled the
    # same way each training fold was above.
    final_training_frame = oversample_training_rows(frame)

    pipeline = build_pipeline(
        clone(best_classifier)
    )

    pipeline.fit(
        final_training_frame[FEATURE_COLUMNS],
        final_training_frame["final_label"],
    )

    model_bundle = {
        "model": pipeline,
        "labels": LABELS,
        "metrics": metrics,
    }

    joblib.dump(
        model_bundle,
        model_path,
    )

    return {
        **metrics,
        "classification_report":
            str(report_path),
        "confusion_matrix":
            str(confusion_matrix_path),
        "model_comparison":
            str(comparison_path),
        "model_path":
            str(model_path),
    }


def load_model_bundle(
    model_path: Path,
) -> dict[str, Any]:
    """Load the locally trained model."""
    if not model_path.exists():
        raise FileNotFoundError(
            f"Trained model not found: {model_path}"
        )

    return joblib.load(model_path)


def calculate_learning_quality_indicator(
    predictions: Sequence[str],
) -> float:
    """
    Calculate the percentage of texts classified into
    substantive learning-indicator categories.
    """
    predictions = list(predictions)

    if not predictions:
        return 0.0

    substantive_count = sum(
        prediction in SUBSTANTIVE_LABELS
        for prediction in predictions
    )

    return (
        substantive_count
        / len(predictions)
    ) * 100


def predict_repository_texts(
    texts: Sequence[str],
    artifact_types: Sequence[str],
    model_path: Path,
) -> dict[str, Any]:
    """Classify repository texts and calculate the LQI."""
    if len(texts) != len(artifact_types):
        raise ValueError(
            "texts and artifact_types must be the same length."
        )

    frame = pd.DataFrame(
        {
            "text": [str(text) for text in texts],
            "artifact_type": [
                clean_artifact_type(artifact_type)
                for artifact_type in artifact_types
            ],
        }
    )

    frame = frame[
        frame["text"].str.strip().str.len() > 0
    ].reset_index(drop=True)

    if frame.empty:
        raise ValueError(
            "No repository text was supplied."
        )

    bundle = load_model_bundle(
        model_path
    )

    pipeline = bundle["model"]

    predictions = pipeline.predict(
        frame[FEATURE_COLUMNS]
    )

    distribution = Counter(
        predictions
    )

    learning_quality_indicator = (
        calculate_learning_quality_indicator(
            predictions
        )
    )

    feature_matrix = (
        pipeline
        .named_steps["features"]
        .transform(frame[FEATURE_COLUMNS])
    )

    return {
        "text_count": len(frame),
        "feature_matrix_shape":
            feature_matrix.shape,
        "predictions":
            predictions.tolist(),
        "category_distribution": {
            label: int(
                distribution.get(label, 0)
            )
            for label in LABELS
        },
        "learning_quality_indicator":
            learning_quality_indicator,
    }
