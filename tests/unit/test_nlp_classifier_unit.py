import pandas as pd
import pytest

from analytics.nlp.classifier import (
    build_pipeline,
    calculate_learning_quality_indicator,
    clean_text,
    interpret_cohen_kappa,
    oversample_training_rows,
    predict_repository_texts,
    train_and_evaluate,
)


def test_clean_text_removes_urls_and_code():
    raw = (
        "Fix(docker): visit https://example.com now "
        "`inline` and ```fenced code```"
    )

    cleaned = clean_text(raw)

    assert "https" not in cleaned
    assert "inline" not in cleaned
    assert "fenced" not in cleaned
    assert "fix" in cleaned
    assert "docker" in cleaned


def test_clean_text_handles_none_and_nan():
    assert clean_text(None) == ""
    assert clean_text("") == ""
    assert clean_text("NaN") == ""


def test_oversample_training_rows_duplicates_minority_class_only():
    frame = pd.DataFrame(
        {
            "text": ["a", "b", "c", "d", "e", "f"],
            "artifact_type": ["commit"] * 6,
            "final_label": ["majority"] * 5 + ["minority"] * 1,
        }
    )

    resampled = oversample_training_rows(
        frame,
        cap_ratio=0.5,
        random_state=1,
    )

    counts = resampled["final_label"].value_counts()

    assert counts["majority"] == 5
    assert counts["minority"] == 2
    assert len(resampled) > len(frame)


def test_build_pipeline_fits_and_predicts_on_tiny_dataset():
    frame = pd.DataFrame(
        {
            "text": [
                "fix bug in parser",
                "fix bug in parser again",
                "add new feature for users",
                "add another feature for users",
            ],
            "artifact_type": ["commit", "commit", "issue", "issue"],
            "final_label": [
                "refinement",
                "refinement",
                "experimentation",
                "experimentation",
            ],
        }
    )

    pipeline = build_pipeline()
    pipeline.fit(
        frame[["text", "artifact_type"]],
        frame["final_label"],
    )

    predictions = pipeline.predict(
        frame[["text", "artifact_type"]]
    )

    assert len(predictions) == len(frame)
    assert set(predictions) <= {"refinement", "experimentation"}


def test_calculate_learning_quality_indicator():
    predictions = ["refinement", "none", "experimentation", "none"]

    assert calculate_learning_quality_indicator(
        predictions
    ) == pytest.approx(50.0)

    assert calculate_learning_quality_indicator([]) == 0.0


def test_train_and_evaluate_and_predict_round_trip(tmp_path):
    samples = {
        "problem_identification": [
            "there is a bug when saving",
            "error occurs on submit",
        ],
        "experimentation": [
            "trying a new approach here",
            "testing an alternative algorithm",
        ],
        "reflection": [
            "looking back this was a good decision",
            "in hindsight we learned a lot",
        ],
        "refinement": [
            "refactor the module for clarity",
            "clean up unused imports",
        ],
        "none": [
            "update readme wording",
            "bump version number",
        ],
    }

    rows = [
        {
            "sample_id": "T001",
            "artifact_type": "commit",
            "artifact_id": f"{label}-{index}",
            "text": text,
            "final_label": label,
        }
        for label, texts in samples.items()
        for index, text in enumerate(texts)
    ]

    training_csv = tmp_path / "gold_standard.csv"
    pd.DataFrame(rows).to_csv(training_csv, index=False)

    model_path = tmp_path / "model.joblib"
    results_directory = tmp_path / "results"

    results = train_and_evaluate(
        training_csv=training_csv,
        model_path=model_path,
        results_directory=results_directory,
    )

    assert model_path.exists()
    assert results["training_records"] == 10
    assert results["selected_model"] in {
        "logistic_regression",
        "linear_svc",
        "complement_nb",
    }
    assert (results_directory / "model_comparison.csv").exists()
    assert -1.0 <= results["cohen_kappa"] <= 1.0
    assert results["cohen_kappa_interpretation"] in {
        "poor (worse than chance)",
        "slight",
        "fair",
        "moderate",
        "substantial",
        "almost perfect",
    }

    prediction = predict_repository_texts(
        ["refactor the module for clarity"],
        ["commit"],
        model_path,
    )

    assert prediction["text_count"] == 1
    assert prediction["predictions"][0] in {
        "problem_identification",
        "experimentation",
        "reflection",
        "refinement",
        "none",
    }


@pytest.mark.parametrize(
    "kappa,expected",
    [
        (-0.1, "poor (worse than chance)"),
        (0.0, "slight"),
        (0.20, "slight"),
        (0.21, "fair"),
        (0.40, "fair"),
        (0.41, "moderate"),
        (0.60, "moderate"),
        (0.61, "substantial"),
        (0.80, "substantial"),
        (0.81, "almost perfect"),
        (1.0, "almost perfect"),
    ],
)
def test_interpret_cohen_kappa_matches_landis_koch_scale(kappa, expected):
    assert interpret_cohen_kappa(kappa) == expected
