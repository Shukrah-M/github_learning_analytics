"""
Diagnose why a specific NLP category is under-detected: a sampling
gap (too few real labelled examples for cross-validation to say
anything meaningful) versus a genuine recall problem (enough examples
exist, but the model isn't picking up the distinguishing signal).

Usage:

    python -m scripts.diagnose_classifier
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sklearn.metrics import classification_report, confusion_matrix  # noqa: E402

from analytics.nlp.classifier import (  # noqa: E402
    LABELS,
    candidate_classifiers,
    cross_val_predict_with_oversampling,
    prepare_training_data,
)

TRAINING_CSV = PROJECT_ROOT / "data" / "nlp_gold_standard.csv"

# Rule of thumb: below this many real examples, a cross-validated
# recall estimate for that class isn't meaningful — every fold trains
# on essentially none of it.
MIN_RELIABLE_SAMPLE_SIZE = 5


def diagnose(target_classes: list[str]) -> None:
    frame = prepare_training_data(TRAINING_CSV)

    class_counts = frame["final_label"].value_counts()
    minimum_class_count = int(class_counts.min())
    number_of_folds = min(5, minimum_class_count)

    classifier = candidate_classifiers()["logistic_regression"]

    predictions = cross_val_predict_with_oversampling(
        frame,
        classifier,
        n_splits=number_of_folds,
    )

    report = classification_report(
        frame["final_label"],
        predictions,
        labels=LABELS,
        target_names=LABELS,
        output_dict=True,
        zero_division=0,
    )

    matrix = confusion_matrix(
        frame["final_label"],
        predictions,
        labels=LABELS,
    )

    print("=== Per-class results ===")
    for label in LABELS:
        row = report[label]
        print(
            f"{label:<25} support={int(row['support']):<4} "
            f"precision={row['precision']:.2f} "
            f"recall={row['recall']:.2f} "
            f"f1={row['f1-score']:.2f}"
        )

    print()
    print("=== Confusion matrix (rows = true label, columns = predicted) ===")
    header = "  ".join(f"{label[:10]:>10}" for label in LABELS)
    print(" " * 12, header)
    for i, label in enumerate(LABELS):
        row_values = "  ".join(f"{matrix[i][j]:>10}" for j in range(len(LABELS)))
        print(f"{label[:10]:>10}  {row_values}")

    print()
    print("=== Diagnosis ===")

    for label in target_classes:
        count = int(class_counts.get(label, 0))
        row = report[label]
        label_index = LABELS.index(label)

        print(f"\n--- {label} (n={count}) ---")

        if count < MIN_RELIABLE_SAMPLE_SIZE:
            per_fold = count // number_of_folds
            print(
                f"  VERDICT: SAMPLING GAP. Only {count} real labelled "
                f"example(s) exist."
            )
            print(
                f"  With {number_of_folds}-fold cross-validation, each "
                f"training fold sees at most {count - per_fold} real "
                "example(s) of this class before oversampling just "
                "duplicates them."
            )
            print(
                "  No feature engineering or model change fixes this — "
                "the recall/precision numbers above are not a "
                "meaningful estimate of anything. The only real fix is "
                "collecting more human-labelled examples."
            )
            continue

        true_row = matrix[label_index]
        misclassified_as = {
            LABELS[j]: int(true_row[j])
            for j in range(len(LABELS))
            if j != label_index and true_row[j] > 0
        }

        print(
            f"  Support ({count}) is above the "
            f"{MIN_RELIABLE_SAMPLE_SIZE}-example floor for a "
            "cross-validated estimate to mean something."
        )
        print(
            f"  Recall={row['recall']:.2f}  "
            f"Precision={row['precision']:.2f}  "
            f"F1={row['f1-score']:.2f}"
        )

        if misclassified_as:
            print(f"  Misclassified as: {misclassified_as}")
            print(
                "  VERDICT: RECALL PROBLEM worth investigating further "
                "(feature representation or decision boundary, not "
                "pure sample size)."
            )
        else:
            print(
                "  VERDICT: classifies cleanly within the current "
                "sample; no confusion detected."
            )


if __name__ == "__main__":
    diagnose(["reflection", "experimentation"])
