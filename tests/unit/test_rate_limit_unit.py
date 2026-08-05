from dashboard.rate_limit import RateLimiter


def test_rate_limiter_allows_up_to_the_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)

    assert limiter.is_allowed("client-a") is True
    assert limiter.is_allowed("client-a") is True
    assert limiter.is_allowed("client-a") is True
    assert limiter.is_allowed("client-a") is False


def test_rate_limiter_tracks_keys_independently():
    limiter = RateLimiter(max_requests=1, window_seconds=60)

    assert limiter.is_allowed("client-a") is True
    assert limiter.is_allowed("client-b") is True
    assert limiter.is_allowed("client-a") is False


def test_rate_limiter_allows_again_after_window_expires():
    limiter = RateLimiter(max_requests=1, window_seconds=0.05)

    assert limiter.is_allowed("client-a") is True
    assert limiter.is_allowed("client-a") is False

    import time

    time.sleep(0.1)

    assert limiter.is_allowed("client-a") is True
