import pytest

from hindsight.llm.retry import GENERIC_WAITS, RATE_LIMIT_WAITS, with_retry


class RateLimitError(Exception):
    """Name-matched by the retry wrapper (mirrors openai.RateLimitError)."""


def make_flaky(fail_times: int, exc_factory):
    state = {"calls": 0}

    def transport(request):
        state["calls"] += 1
        if state["calls"] <= fail_times:
            raise exc_factory()
        return {"ok": True, "calls": state["calls"]}

    return transport, state


def test_rate_limit_retries_with_long_waits():
    sleeps = []
    transport, state = make_flaky(2, lambda: RateLimitError("429 code 11210"))
    wrapped = with_retry(transport, sleep=sleeps.append)
    assert wrapped({"m": 1})["ok"] is True
    assert state["calls"] == 3
    assert sleeps == [RATE_LIMIT_WAITS[0], RATE_LIMIT_WAITS[1]]


def test_generic_error_uses_expo_backoff():
    sleeps = []
    transport, state = make_flaky(2, lambda: ConnectionError("boom"))
    wrapped = with_retry(transport, sleep=sleeps.append)
    assert wrapped({"m": 1})["ok"] is True
    assert sleeps == [GENERIC_WAITS[0], GENERIC_WAITS[1]]


def test_exhaustion_reraises():
    sleeps = []
    transport, _ = make_flaky(99, lambda: RateLimitError("429"))
    wrapped = with_retry(transport, sleep=sleeps.append)
    with pytest.raises(RateLimitError):
        wrapped({"m": 1})
    assert sleeps == list(RATE_LIMIT_WAITS)


def test_429_in_message_counts_as_rate_limit():
    sleeps = []
    transport, _ = make_flaky(1, lambda: RuntimeError("HTTP 429 too many requests"))
    wrapped = with_retry(transport, sleep=sleeps.append)
    assert wrapped({"m": 1})["ok"] is True
    assert sleeps == [RATE_LIMIT_WAITS[0]]
