"""Memo language option + LLM provenance counters.

The load-bearing invariant: language="en" must produce BYTE-IDENTICAL analyst
prompts to the pre-language era, or every committed recording (the offline
demo) silently goes stale.
"""
from datetime import date

from hindsight.agents import prompts
from hindsight.llm.recording import RecordingLLMClient
from hindsight.schemas import RunConfig


def make_meta():
    from hindsight.data.models import CaseMeta

    return CaseMeta(
        case_id="c",
        title="T",
        ticker="NVDA",
        as_of=date(2025, 5, 22),
        outcome_window_days=40,
        description="desc",
    )


# ---------- language plumbing ----------

def test_en_prompt_is_byte_identical_to_pre_language_era():
    """Reconstruct the exact pre-language prompt and compare byte-for-byte."""
    meta = make_meta()
    legacy = (
        prompts.case_brief(meta)
        + "\nMarket snapshot (price_history tool output):\nMKT\n"
        + "\nEvidence blocks (cite chunk_ids exactly as shown):\nEV\n"
        + "\nWrite the memo JSON now."
    )
    assert prompts.analyst_user_prompt(meta, "EV", "MKT") == legacy
    assert prompts.analyst_user_prompt(meta, "EV", "MKT", language="en") == legacy


def test_zh_prompt_adds_only_the_language_line():
    meta = make_meta()
    en = prompts.analyst_user_prompt(meta, "EV", "MKT", language="en")
    zh = prompts.analyst_user_prompt(meta, "EV", "MKT", language="zh")
    assert zh != en
    assert "Simplified Chinese" in zh
    # keys/enums stay English per instruction — the structural validator relies on it
    assert "chunk_ids exactly as specified" in zh
    # the zh prompt is the en prompt with one block inserted before the closer
    assert zh.replace(prompts.MEMO_LANGUAGE_LINES["zh"], "") == en


def test_run_config_language_defaults_en_and_accepts_legacy_json():
    assert RunConfig().language == "en"
    # config_json recorded before the field existed must still parse
    legacy = RunConfig.model_validate_json('{"memory_on": true, "max_steps": 8}')
    assert legacy.language == "en"
    assert RunConfig(language="zh").language == "zh"


# ---------- provenance counters ----------

def fake_response(text: str) -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": text}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def test_counters_track_live_calls_and_cache_hits(tmp_path):
    def transport(request: dict) -> dict:
        return fake_response("ok")

    c = RecordingLLMClient(
        transport=transport, db_path=tmp_path / "rec.sqlite", model="m", offline=False
    )
    assert (c.cache_hits, c.cache_misses) == (0, 0)
    c.chat(messages=[{"role": "user", "content": "a"}])
    assert (c.cache_hits, c.cache_misses) == (0, 1)  # live call, recorded
    c.chat(messages=[{"role": "user", "content": "a"}])
    assert (c.cache_hits, c.cache_misses) == (1, 1)  # replayed, no network
    c.chat(messages=[{"role": "user", "content": "b"}])
    assert (c.cache_hits, c.cache_misses) == (1, 2)


def test_offline_replay_counts_as_hit(tmp_path):
    def transport(request: dict) -> dict:
        return fake_response("ok")

    db = tmp_path / "rec.sqlite"
    rec = RecordingLLMClient(transport=transport, db_path=db, model="m", offline=False)
    rec.chat(messages=[{"role": "user", "content": "a"}])

    replay = RecordingLLMClient(transport=transport, db_path=db, model="m", offline=True)
    replay.chat(messages=[{"role": "user", "content": "a"}])
    assert (replay.cache_hits, replay.cache_misses) == (1, 0)
