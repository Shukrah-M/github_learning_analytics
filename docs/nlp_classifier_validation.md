# NLP Classifier Validation Results

## Purpose

This document reports the current cross-validated performance of the
repository-text NLP classifier and states plainly where its results are
and are not reliable.

## Training data

The classifier is trained on the manually coded gold-standard set
(`data/nlp_gold_standard.csv`), which contains 100 labelled text
artefacts (commit messages, issue titles/bodies, issue comments, pull
request titles/bodies, and pull request reviews) drawn from the five
pilot repositories.

The class distribution is uneven:

| Label | Examples |
|---|---:|
| refinement | 39 |
| none | 38 |
| problem_identification | 18 |
| experimentation | 3 |
| reflection | 2 |

`experimentation` and `reflection` both have very few examples. This is
a data-size limit, not a modelling limit: no amount of pipeline tuning
can produce a reliable performance estimate for a class with 2-3
examples, because cross-validation for that class necessarily trains on
essentially none of it and tests on essentially all of it.

## Coding-consistency check: a real data-quality fix, not a modelling one

A systematic diagnostic (`scripts/diagnose_classifier.py`) was built to
distinguish two different reasons a class can be under-detected:

- a **sampling gap** — too few real examples for cross-validation to
  measure anything meaningful, however good the model is;
- a **recall problem** — enough examples exist, but the model isn't
  learning the distinguishing signal, which pipeline changes can fix.

Running this against the original 101-row gold standard flagged
`experimentation` (support 10) as having enough examples to
investigate as a possible recall problem. Inspecting the actual 10
rows against the category's own operational definition (Table 16)
found that **6 of the 10 were miscoded**:

| Issue found | Rows | Correction |
|---|---:|---|
| Not development text — spam unrelated to the repository | 1 | Removed from the dataset |
| Routine merge commits, matching the `none` pattern used elsewhere in the same dataset | 3 | Relabelled `none` |
| Contained the category's own listed `refinement` markers ("harden", "polish") | 2 | Relabelled `refinement` |

Only 3 of the original 10 rows were genuinely `experimentation`
(and even those are near-duplicates of the same automated "smoke
test" template from one repository, so the real independent signal
was smaller still). This is why `experimentation` support drops to 3
in the current dataset rather than increasing — the original count of
10 was partly an artefact of coding errors, not real signal. The
corrected labels are a more accurate gold standard, even though the
class now more honestly falls into the same "sampling gap" category
as `reflection`.

**This is worth reporting as a positive methodological step in the
dissertation, not a setback.** Building a systematic check that
distinguishes coding errors from genuine model limitations, and using
it to catch and correct 6 real labelling errors, is itself evidence of
data-quality control — directly relevant to the "data preparation and
quality control" methodology already documented for this project.

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

| Metric | Original baseline | After pipeline changes | After label correction | Total change |
|---|---:|---:|---:|---:|
| Cross-validated accuracy | 0.337 | 0.442 | 0.496 | +0.159 |
| Macro-F1 | 0.244 | 0.340 | 0.429 | +0.185 |
| Weighted-F1 | 0.324 | 0.431 | 0.493 | +0.169 |
| Cohen's kappa | not measured | 0.194 ("slight") | 0.212 ("fair") | — |

`linear_svc` was selected over `logistic_regression` and
`complement_nb` on this corrected dataset (see
`results/nlp/model_comparison.csv` — note `logistic_regression` still
wins on raw accuracy, but `linear_svc` was kept because model
selection is by macro-F1, which better reflects performance across
all five classes rather than being dominated by the largest ones).

### Cohen's kappa: a more honest number than accuracy alone

Accuracy and F1 don't correct for how easy the label distribution
itself makes agreement look — with five uneven classes, a fair amount
of "correct" predictions can come from chance and class imbalance
rather than the classifier actually distinguishing categories.
**Cohen's kappa** measures agreement between the classifier and the
human-coded gold-standard labels after removing the agreement
expected by chance, computed on the same out-of-fold cross-validated
predictions used for the report and confusion matrix below.

The result is **κ = 0.212**, which the standard Landis & Koch (1977)
benchmark scale rates as **"fair"** agreement (0.21–0.40) — an
improvement on the pre-correction value of 0.194 ("slight"). For
reference, that scale runs: ≤0 poor, 0.01–0.20 slight, 0.21–0.40 fair,
0.41–0.60 moderate, 0.61–0.80 substantial, 0.81–1.00 almost perfect.

**Both accuracy and kappa should be reported together in the
dissertation** — accuracy alone would overstate how much the
classifier agrees with human coding beyond chance. "Fair" agreement is
real progress over "slight," but is still far from a validated
measurement instrument.

### Per-class result (from `results/nlp/classification_report.csv`)

| Label | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| problem_identification | 0.50 | 0.33 | 0.40 | 18 |
| experimentation | 0.00 | 0.00 | 0.00 | 3 |
| reflection | 0.00 | 0.00 | 0.00 | 2 |
| refinement | 0.52 | 0.41 | 0.46 | 39 |
| none | 0.52 | 0.66 | 0.58 | 38 |

## Interpretation

Two different kinds of improvement are stacked here, and it matters to
keep them distinct. The **pipeline changes** (combined features,
oversampling, model comparison) improved how well the classifier uses
whatever data it's given. The **label correction** improved the data
itself — catching real coding errors, not tuning the model to fit
them. Both moved the numbers in the same direction, but only the first
is a "modelling" achievement; the second is a data-quality one, and is
arguably the more defensible of the two for a dissertation, since it
came from checking labels against the coding scheme's own definitions
rather than from adjusting anything to make a metric look better.

`experimentation` and `reflection` now both sit at 0.00 across
precision, recall and F1, for the same reason: 3 and 2 real labelled
examples respectively is too little for cross-validation to produce a
meaningful estimate, regardless of model quality. This is not a
modelling failure and further pipeline tuning will not change it. Any
downstream use of this classifier (including the dashboard's
learning-quality indicator) should treat `experimentation` and
`reflection` predictions as unreliable until more labelled examples
are collected for both.

`none` and `refinement` are the most reliable categories (support 38
and 39, F1 0.58 and 0.46). `problem_identification` is moderately
reliable (F1 0.40, though recall dropped to 0.33 after the label
correction — worth a further look if time permits, though it is well
above the sampling-gap floor and so a legitimate target for further
modelling work, unlike the two classes above).

## Next step to raise the ceiling

The next step that would materially improve `experimentation` and
`reflection` is not further pipeline tuning but **more labelled
data**. `scripts/export_nlp_texts.py` already supports pulling
additional repository text for labelling; expanding
`data/nlp_gold_standard.csv` for these two categories specifically
(aiming past 10 genuine, non-duplicate examples each) is the
recommended next step before drawing dissertation conclusions from
this classifier's category distributions for those classes.

## Reference

Landis, J. R., & Koch, G. G. (1977). The measurement of observer
agreement for categorical data. *Biometrics*, 33(1), 159–174.
