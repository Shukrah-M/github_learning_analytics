# Controlled Repository Ground-Truth Specification

The controlled repositories contain deliberately created synthetic
GitHub activity. They do not represent real learners or real software
development projects.

Their purpose is to test whether the behavioural analytics engine
detects predefined development patterns.

| Repository | Designed behaviour | Expected results |
|---|---|---|
| controlled_regular | Commits evenly distributed over time | Moderate commit frequency, high active-day ratio, zero or low interval variation, short inactivity gap |
| controlled_burst | Most commits concentrated in one day followed by a long gap | Low active-day ratio, high interval variation, long inactivity gap |
| controlled_refinement | Several issues created, discussed and closed | High issue closure rate, several comments, measurable resolution time |
| controlled_collaboration | Changes submitted through reviewed pull requests | High merge rate, high reviewed-PR ratio, several formal reviews |
| controlled_low_activity | Few commits, unresolved issues and unmerged PR | Low activity, low issue closure rate, zero review activity |