# NLP Classifier Validation Results

## Purpose

This document reports the current cross-validated performance of the
repository-text NLP classifier and states plainly where its results are
and are not reliable.

## Training data

The classifier is trained on the manually coded gold-standard set
(`data/nlp_gold_standard.csv`), which contains 101 labelled text
artefacts (commit messages, issue titles/bodies, issue comments, pull
request titles/bodies, and pull request reviews) drawn from the five
pilot repositories.

The class distribution is uneven:

| Label | Examples |
|---|---:|
| refinement | 37 |
| none | 34 |
| problem_identification | 18 |
| experimentation | 10 |
| reflection | 2 |

The `reflection` class has only two examples in the entire dataset. This
is a data-size limit, not a modelling limit: no amount of pipeline tuning
can produce a reliable estimate of performance on a class with two
examples, because cross-validation for that class necessarily trains on a
single example and tests on a single example.

## Pipeline changes evaluated

Three changes were made to the classifier
(`analytics/nlp/classifier.py`) and evaluated against the previous
single-model, word-TF-IDF-only baseline:

1. **Combined feature representation** — word TF-IDF (1–2 grams), character
   TF-IDF (3–5 grams, helps with short code-styled text such as
   `fix(docker):`), and a one-hot encoded `artifact_type` feature
   (commit / issue / issue_comment / pull_request /
   pull_request_review), combined via a `ColumnTransformer`.
2. **In-fold oversampling** — minority-class rows are duplicated up to
   50% of the majority class's size, applied only inside each
   cross-validation training fold (never to the held-out fold), so it
   cannot leak information across the split.
3. **Model comparison** — `LogisticRegression`, `LinearSVC` and
   `ComplementNB` are all cross-validated and the best by mean macro-F1
   is kept. Cross-validation uses `RepeatedStratifiedKFold` (folds =
   min(5, smallest class count), 5 repeats) rather than a single
   2-fold split, since a single run with this little data is noisy.

## Result

| Metric | Previous baseline | Current | Change |
|---|---:|---:|---:|
| Cross-validated accuracy | 0.337 | 0.442 | +0.105 |
| Macro-F1 | 0.244 | 0.340 | +0.096 |
| Weighted-F1 | 0.324 | 0.431 | +0.107 |
| Cohen's kappa | not previously measured | 0.194 ("slight") | — |

`logistic_regression` was selected over `linear_svc` and
`complement_nb` (see `results/nlp/model_comparison.csv` for all three).

### Cohen's kappa: a more honest number than accuracy alone

Accuracy and F1 don't correct for how easy the label distribution
itself makes agreement look — with five uneven classes, a fair amount
of "correct" predictions can come from chance and class imbalance
rather than the classifier actually distinguishing categories.
**Cohen's kappa** measures agreement between the classifier and the
human-coded gold-standard labels after removing the agreement
expected by chance, computed on the same out-of-fold cross-validated
predictions used for the report and confusion matrix above.

The result is **κ = 0.194**, which the standard Landis & Koch (1977)
benchmark scale rates as **"slight"** agreement (0.00–0.20). For
reference, that scale runs: ≤0 poor, 0.01–0.20 slight, 0.21–0.40 fair,
0.41–0.60 moderate, 0.61–0.80 substantial, 0.81–1.00 almost perfect.

This is a materially more cautious picture than the 44.2% accuracy
figure suggests on its own. **Both numbers should be reported
together in the dissertation** — accuracy alone would overstate how
much the classifier agrees with human coding beyond chance. A kappa
in the "slight" range means the classifier's category assignments
should be treated as a rough, exploratory signal, not a
dependable substitute for manual coding, until the training set grows
substantially past its current 101 examples.

### Per-class result (from `results/nlp/classification_report.csv`)

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| problem_identification | 0.53 | 0.56 | 0.54 | 18 |
| experimentation | 0.29 | 0.20 | 0.24 | 10 |
| reflection | 0.00 | 0.00 | 0.00 | 2 |
| refinement | 0.42 | 0.38 | 0.40 | 37 |
| none | 0.43 | 0.53 | 0.47 | 34 |

## Interpretation

The combined feature representation, in-fold oversampling and model
comparison produced a genuine, moderate improvement across accuracy,
macro-F1 and weighted-F1. This is consistent with what the pipeline
changes can realistically deliver: better use of the existing 101
examples, not more information than they contain. The kappa result
above shows that improvement more honestly: the classifier is better
than the previous baseline, but "slight" chance-corrected agreement is
still a long way from a validated measurement instrument.

`reflection` remains at 0.00 across all three metrics. With only two
labelled examples, this is expected and should not be read as a modelling
failure. Any downstream use of this classifier (including the dashboard's
learning-quality indicator) should treat `reflection` predictions as
unreliable until more labelled examples are collected for that class.

`problem_identification` and `none` are the most reliable categories
(support 18 and 34, F1 0.54 and 0.47). `experimentation` and `refinement`
are moderately reliable. These per-class differences should be kept in
mind when discussing the learning-quality indicator in the dissertation —
an aggregate accuracy or F1 number alone would hide this variation.

## Next step to raise the ceiling

The next step that would materially improve these numbers is not further
pipeline tuning but **more labelled data**, particularly for
`reflection` and `experimentation`. `scripts/export_nlp_texts.py` already
supports pulling additional repository text for labelling; expanding
`data/nlp_gold_standard.csv` (especially past 5-10 examples per class)
is the recommended next step before drawing dissertation conclusions from
this classifier's category distributions.

## Reference

Landis, J. R., & Koch, G. G. (1977). The measurement of observer
agreement for categorical data. *Biometrics*, 33(1), 159–174.
