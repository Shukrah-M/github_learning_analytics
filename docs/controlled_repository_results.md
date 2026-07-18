## Repository: controlled_low_activity

### Designed behaviour

This repository was deliberately created to represent low and
incomplete development activity.

It contains:

two commits separated by a long inactivity period;
three open issues;
one closed but unmerged pull request;
no pull-request reviews.

### Results

| Metric | Expected result | Observed result | Assessment |
|---|---:|---:|---|
| Total commits | 2 | 2 | Pass |
| Project duration | 31 days | 31 days | Pass |
| Active commit days | 2 | 2 | Pass |
| Active-day ratio | Approximately 0.065 | 0.065 | Pass |
| Commit frequency per week | Approximately 0.45 | 0.45 | Pass |
| Mean commit interval | 30 days | 30.0 days | Pass |
| Longest inactivity gap | Approximately 30 days | 30.0 days | Pass |
| Total issues | 3 | 3 | Pass |
| Closed issues | 0 | 0 | Pass |
| Issue closure rate | 0.0 | 0.0 | Pass |
| Mean issue resolution time | Not applicable | None | Pass |
| Total issue comments | 0 | 0 | Pass |
| Total pull requests | 1 | 1 | Pass |
| Merged pull requests | 0 | 0 | Pass |
| Pull-request merge rate | 0.0 | 0.0 | Pass |
| Pull-request reviews | 0 | 0 | Pass |
| Reviewed pull-request ratio | 0.0 | 0.0 | Pass |
| Mean pull-request cycle time | Same-day closure | 0.0 days | Pass |

### Interpretation

The repository contained only two commits across a 31-day development
period. This produced a low active-day ratio of 0.065 and a low weekly
commit frequency of 0.45.

The 30-day mean commit interval and longest inactivity gap correctly
identified the deliberately created period of inactivity.

All three issues remained open, resulting in an issue closure rate of
0.0 and no measurable issue-resolution duration.

The repository contained one closed but unmerged pull request with no
formal reviews. This produced a pull-request merge rate of 0.0 and a
reviewed pull-request ratio of 0.0.

### Conclusion

The controlled_low_activity repository passed the behavioural
validation. The analytics engine correctly identified low commit
activity, a long inactivity period, unresolved issues, an unmerged
pull request, and no formal review activity.

The result provides evidence that the behavioural metrics can detect
the predefined low-activity development pattern.

## Repository: controlled_regular

### Designed behaviour

This repository was deliberately created to represent regular and
continuous development activity.

The main commits were distributed at approximately two-day intervals
across a 15-day period. An additional README commit was created on the
same day as the final development commit.

### Results

| Metric | Expected result | Observed result | Assessment |
|---|---:|---:|---|
| Total commits | 9 | 9 | Pass |
| Project duration | 15 days | 15 days | Pass |
| Active commit days | 8 | 8 | Pass |
| Active-day ratio | Approximately 0.533 | 0.533 | Pass |
| Commit frequency per week | Approximately 4.2 | 4.2 | Pass |
| Mean commit interval | Approximately 1.76 days | 1.76 days | Pass |
| Commit interval standard deviation | Low | 0.65 days | Pass |
| Longest inactivity gap | Approximately 2 days | 2.0 days | Pass |
| Total issues | 0 | 0 | Pass |
| Issue closure rate | Not applicable | None | Pass |
| Total pull requests | 0 | 0 | Pass |
| Pull-request merge rate | Not applicable | None | Pass |
| Reviewed pull-request ratio | Not applicable | None | Pass |

### Interpretation

The repository contained nine commits across a 15-day period. Eight
separate calendar days contained commit activity, producing an
active-day ratio of 0.533.

The weekly commit frequency of 4.2 and longest inactivity gap of two
days indicate that development activity was distributed regularly
throughout the controlled period.

The mean commit interval was 1.76 days rather than exactly two days
because the README documentation commit was created one hour after the
final development commit. This introduced one short interval into the
otherwise regular two-day sequence.

The commit interval standard deviation of 0.65 days remained low,
showing that most commit intervals were close to the designed regular
pattern.

The repository contained no issues or pull requests. Therefore, the
issue closure rate, pull-request merge rate and reviewed pull-request
ratio were correctly reported as `None`, because these metrics were
not applicable.

### Conclusion

The controlled_regular repository passed the behavioural validation.
The analytics engine correctly identified regular commit activity,
a relatively high active-day ratio, short inactivity gaps and low
variation between commit intervals.

The result demonstrates that the commit metrics can detect a
predefined pattern of continuous and regularly distributed
development activity.

## Repository: controlled_burst

### Designed behaviour

This repository was deliberately created to represent burst-based
development activity.

Most commits were created within a short period on the same day,
followed by a long period of inactivity before the final commit.

### Results

| Metric | Expected result | Observed result | Assessment |
|---|---:|---:|---|
| Total commits | 8 | 8 | Pass |
| Project duration | 15 days | 15 days | Pass |
| Active commit days | 2 | 2 | Pass |
| Active-day ratio | Approximately 0.133 | 0.133 | Pass |
| Commit frequency per week | Approximately 3.73 | 3.73 | Pass |
| Mean commit interval | Approximately 2 days | 2.0 days | Pass |
| Commit interval standard deviation | High | 4.88 days | Pass |
| Longest inactivity gap | Approximately 14 days | 13.96 days | Pass |
| Total issues | 0 | 0 | Pass |
| Issue closure rate | Not applicable | None | Pass |
| Total pull requests | 0 | 0 | Pass |
| Pull-request merge rate | Not applicable | None | Pass |
| Reviewed pull-request ratio | Not applicable | None | Pass |

### Interpretation

The repository contained eight commits across a 15-day period, but
commit activity occurred on only two calendar days. This produced a
low active-day ratio of 0.133.

The longest inactivity gap was 13.96 days, which closely matches the
designed 14-day inactivity period.

The commit interval standard deviation was 4.88 days. This is
substantially higher than the 0.65-day interval standard deviation
observed in the controlled_regular repository. The result shows that
the analytics engine detected the uneven distribution of commits.

Although the mean commit interval was 2.0 days, this value alone does
not represent the burst pattern accurately. Most commits occurred only
minutes apart, while one interval lasted almost 14 days. The high
standard deviation and long inactivity gap therefore provide stronger
evidence of burst-based development.

The repository contained no issues or pull requests. The related rates
were correctly reported as `None` because those metrics were not
applicable.

### Comparison with controlled_regular

| Metric | controlled_regular | controlled_burst | Interpretation |
|---|---:|---:|---|
| Total commits | 9 | 8 | Similar overall activity volume |
| Project duration | 15 days | 15 days | Same observation period |
| Active commit days | 8 | 2 | Burst activity occurred on fewer days |
| Active-day ratio | 0.533 | 0.133 | Regular activity was more continuous |
| Interval standard deviation | 0.65 days | 4.88 days | Burst activity was much less consistent |
| Longest inactivity gap | 2.0 days | 13.96 days | Burst repository contained a long pause |

### Conclusion

The controlled_burst repository passed the behavioural validation.

The analytics engine correctly identified concentrated commit activity,
a low active-day ratio, high interval variation and a long inactivity
gap.

The comparison with controlled_regular demonstrates that repositories
with similar commit counts and identical project durations can still
produce clearly different temporal development patterns.

## Repository: controlled_refinement

### Designed behaviour

This repository was deliberately created to represent issue-based
problem identification, discussion and refinement.

Six issues were created. Each issue received one comment, five issues
were closed, and one issue remained open.

### Results

| Metric | Expected result | Observed result | Assessment |
|---|---:|---:|---|
| Total commits | 1 | 1 | Pass |
| Active commit days | 1 | 1 | Pass |
| Total issues created | 6 | 6 | Pass |
| Total issues closed | 5 | 5 | Pass |
| Total issues open | 1 | 1 | Pass |
| Issue closure rate | Approximately 0.833 | 0.833 | Pass |
| Total issue comments | 6 | 6 | Pass |
| Mean comments per issue | 1.0 | 1.0 | Pass |
| Mean issue resolution time | Based on actual timestamps | 0.0 days | Pass |
| Total pull requests | 0 | 0 | Pass |
| Pull-request merge rate | Not applicable | None | Pass |
| Reviewed pull-request ratio | Not applicable | None | Pass |

### Interpretation

The repository contained six issues, of which five were closed and one
remained open.

The issue closure rate was calculated as:

```text
5 closed issues ÷ 6 total issues = 0.833

## Repository: controlled_collaboration

### Designed behaviour

This repository was deliberately created to represent collaborative
development through pull requests, formal reviews and integration of
proposed changes.

Four pull requests were created. Three received formal reviews and were
merged, while one pull request was closed without merging or review.

### Results

| Metric | Expected result | Observed result | Assessment |
|---|---:|---:|---|
| Total commits | Based on repository activity | 9 | Informational |
| Project duration | Based on actual timestamps | 2 days | Informational |
| Active commit days | Based on actual timestamps | 2 | Informational |
| Total pull requests | 4 | 4 | Pass |
| Merged pull requests | 3 | 3 | Pass |
| Closed without merging | 1 | 1 | Pass |
| Pull-request merge rate | 0.75 | 0.75 | Pass |
| Total formal reviews | At least 3 | 4 | Pass |
| Pull requests receiving reviews | 3 | 3 | Pass |
| Reviewed pull-request ratio | 0.75 | 0.75 | Pass |
| Mean pull-request cycle time | Based on actual timestamps | 0.03 days | Informational |
| Total issues | 0 | 0 | Pass |
| Issue closure rate | Not applicable | None | Pass |

### Interpretation

The repository contained four pull requests, of which three were
merged and one was closed without merging.

The pull-request merge rate was calculated as:

```text
3 merged pull requests ÷ 4 total pull requests = 0.75