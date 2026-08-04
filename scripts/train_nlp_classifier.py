"""Train and evaluate the repository-text classifier."""

from pathlib import Path

from analytics.nlp.classifier import (
    train_and_evaluate,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

TRAINING_CSV = (
    PROJECT_ROOT
    / "data"
    / "nlp_gold_standard.csv"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "nlp_classifier.joblib"
)

RESULTS_DIRECTORY = (
    PROJECT_ROOT
    / "results"
    / "nlp"
)


def main() -> None:
    print("=" * 70)
    print("NLP CLASSIFIER TRAINING AND EVALUATION")
    print("=" * 70)

    results = train_and_evaluate(
        training_csv=TRAINING_CSV,
        model_path=MODEL_PATH,
        results_directory=RESULTS_DIRECTORY,
    )

    print(
        f"Training records:        "
        f"{results['training_records']}"
    )
    print(
        f"Cross-validation folds:  "
        f"{results['cross_validation_folds']} "
        f"(x{results['cross_validation_repeats']} repeats)"
    )
    print(
        f"Selected model:          "
        f"{results['selected_model']}"
    )
    print(
        f"Mean accuracy:           "
        f"{results['accuracy_mean']:.3f}"
    )
    print(
        f"Mean macro-F1:           "
        f"{results['macro_f1_mean']:.3f}"
    )
    print(
        f"Mean weighted-F1:        "
        f"{results['weighted_f1_mean']:.3f}"
    )

    print("-" * 70)
    print("Model comparison:")
    for row in results["model_comparison_rows"]:
        print(
            f"  {row['model']:<20} "
            f"accuracy={row['accuracy_mean']:.3f}  "
            f"macro_f1={row['macro_f1_mean']:.3f}  "
            f"weighted_f1={row['weighted_f1_mean']:.3f}"
        )

    print("-" * 70)
    print(
        "Classification report:  "
        f"{results['classification_report']}"
    )
    print(
        "Confusion matrix:        "
        f"{results['confusion_matrix']}"
    )
    print(
        "Model comparison CSV:    "
        f"{results['model_comparison']}"
    )
    print(
        "Saved model:             "
        f"{results['model_path']}"
    )
    print("=" * 70)
    print(
        "NLP classifier trained and evaluated successfully."
    )


if __name__ == "__main__":
    main()