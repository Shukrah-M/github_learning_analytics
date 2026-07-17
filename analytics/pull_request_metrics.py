from statistics import mean


def calculate_pull_request_metrics(pull_requests, reviews):
    total_pull_requests = len(pull_requests)

    merged_pull_requests = [
        pull_request
        for pull_request in pull_requests
        if pull_request.merged is True
    ]

    reviewed_pr_ids = {
        review.pull_request_id
        for review in reviews
    }

    cycle_times = []

    for pull_request in pull_requests:
        end_time = (
            pull_request.merged_at
            or pull_request.closed_at
        )

        if pull_request.created_at and end_time:
            cycle_days = (
                end_time - pull_request.created_at
            ).total_seconds() / 86400

            cycle_times.append(cycle_days)

    merge_rate = (
    len(merged_pull_requests) / total_pull_requests
    if total_pull_requests > 0
    else None
)

    reviewed_pr_ratio = (
    len(reviewed_pr_ids) / total_pull_requests
    if total_pull_requests > 0
    else None
)

    return {
    "total_pull_requests": total_pull_requests,
    "merged_pull_requests": len(merged_pull_requests),

    "pull_request_merge_rate": (
        round(merge_rate, 3)
        if merge_rate is not None
        else None
    ),

    "total_pull_request_reviews": len(reviews),

    "reviewed_pull_request_ratio": (
        round(reviewed_pr_ratio, 3)
        if reviewed_pr_ratio is not None
        else None
    ),

    "mean_pull_request_cycle_days": (
        round(mean(cycle_times), 2)
        if cycle_times
        else None
    ),
}