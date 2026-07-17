# Behavioural Metric Specification

## 1. Document Purpose

This document defines the behavioural metrics used by the GitHub-Based Learning Analytics System.

The purpose is to ensure that each metric has:

a clear definition;
a reproducible formula;
identified database fields;
minimum data requirements;
documented edge-case rules;
a cautious interpretation linked to entrepreneurial-learning constructs.

These definitions should be reviewed before the final behavioural analytics engine and experimentation intensity score are implemented.

---

## 2. Unit of Analysis

The primary unit of analysis is one GitHub repository.

Metrics will initially be calculated at repository level. Later development may allow results to be grouped by contributor or time period.

---

## 3. Observation Period

Different observation rules will be used for the two planned datasets.

### Controlled experimental repositories

Controlled repositories will be analysed over the complete experimental period.

The observation period will begin on the date of the first planned activity and end on the final date of the controlled experiment.

### Public GitHub repositories

Public repositories will initially be analysed using a fixed 180-day observation period ending on the extraction date.

Using a fixed period will improve comparability between repositories with different creation dates and project lifetimes.

The observation period may be revised following supervisor review and exploratory analysis.

---

## 4. General Calculation Rules

The following rules apply to all metrics:

GitHub timestamps will be processed in UTC.
Durations will be calculated in days.
One day is treated as 86,400 seconds.
Ratios will normally range between 0 and 1.
Records outside the selected observation period will be excluded.
Duplicate records will be removed or prevented using database uniqueness constraints.
Missing or invalid timestamps will be excluded from duration calculations and reported by the data-quality module.
A metric will return `None` when there is insufficient information to calculate it meaningfully.
A metric will return `0` only when the calculation is valid and the actual result is zero.

---

## 5. Commit Behaviour Metrics

Commit metrics represent iterative engagement, persistence, regularity and development continuity.

### Commit metric interpretation

Commit activity is treated as a behavioural proxy for iterative engagement. A high commit count alone will not be interpreted as evidence of high-quality learning.

Commit frequency should be interpreted alongside:

active-day ratio;
interval variability;
inactivity gaps;
issue behaviour;
pull request behaviour;
textual evidence.

---

## 6. Issue Behaviour Metrics

Issue metrics represent documented problem identification, iterative refinement and problem-resolution activity.

### Issue metric interpretation

Issue creation is treated as a proxy for formal problem identification or task definition.

A high number of issues is not automatically positive. It may indicate:

active problem identification;
structured task management;
a high number of software defects;
unresolved project complexity.

Issue metrics must therefore be interpreted together rather than individually.

---

## 7. Pull Request Behaviour Metrics

Pull request metrics represent structured collaboration, review and integration behaviour.


### Pull request metric interpretation

Pull request behaviour is treated as a proxy for collaboration, review and integration.

A high merge rate does not automatically mean that strong collaborative review occurred. A pull request may be merged without any review.

Merge rate must therefore be considered alongside:

reviewed pull request ratio;
reviews per PR;
pull request cycle time;
review text;
contributor information.

---

## 8. Edge-Case Rules

### Commit metrics


### Pull request metrics


## 9. Difference Between `0` and `None`

The analytics engine must distinguish valid zero values from unavailable calculations.

### Use `0` when:

the calculation is valid;
the required data exists;
the calculated result is genuinely zero.


### Use `None` when:

the minimum required data does not exist;
the metric cannot be calculated meaningfully;
calculating zero would create a misleading interpretation.

---

## 10. Expected Controlled Repository Patterns

The controlled experimental repositories will be designed to produce predefined behavioural patterns.

---

## 11. Metric Validation Requirements

Each metric must pass the following checks before it is used in a composite score:

1. The Python implementation matches a manually calculated example.
2. Edge cases do not cause errors or misleading values.
3. Values retrieved from Python match the PostgreSQL source records.
4. Ratios remain within the range 0 to 1.
5. Durations are not negative.
6. Repeated pipeline runs produce identical analytics results when the source repository has not changed.
7. Controlled repositories produce the expected relative patterns.
8. The theoretical interpretation is reviewed against the literature and discussed with the research supervisor.

---

## 12. Composite Score Status

A final experimentation intensity score has not yet been approved or implemented.

The raw commit, issue and pull request metrics will be calculated and validated first.

The following decisions must be justified before a composite score is introduced:

metrics included in the score;
metric normalisation method;
positive and negative metric direction;
weighting method;
treatment of missing metrics;
classification thresholds;
validation procedure.

The composite score must not be treated as validated until these decisions have been reviewed and tested.

---

