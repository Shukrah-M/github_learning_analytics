# Public Repository Pilot Results

## Observation window

- Start: 2026-01-02T00:00:00+00:00
- End: 2026-07-01T00:00:00+00:00
- Duration: 180 days
- Start boundary: inclusive
- End boundary: exclusive

## Extraction results

| Sample | Category | Commits | Issues | Comments | Pull requests | Reviews | Outside-window records | Result |
|---|---|---:|---:|---:|---:|---:|---:|---|
| P001 | mvp | 56 | 4 | 1 | 7 | 7 | 0 | Pass |
| P002 | saas | 34 | 1 | 2 | 6 | 1 | 0 | Pass |
| P003 | web-application | 7 | 31 | 15 | 58 | 17 | 0 | Pass |
| P004 | prototype | 59 | 0 | 0 | 3 | 0 | 0 | Pass |
| P005 | startup | 12 | 1 | 1 | 4 | 1 | 0 | Pass |

## Pilot outcome

Repositories passing automatic extraction validation: 5/5.

A repository passed when its extracted commit, issue and pull-request
counts matched the preliminary activity check and no retained records
fell outside the fixed observation window.

The repositories are reported using pseudonymous identifiers P001 to
P005. Actual owner and repository names remain in the private research
manifest.

## Conclusion

The pilot evaluated whether the extraction pipeline could collect and
store activity from naturally occurring public GitHub repositories
using a consistent 180-day observation period.

The pilot results should be reviewed before scaling the collection
workflow to the complete public repository sample.
