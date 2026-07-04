import pytest

from hindsight.llm.recording import RecordingLLMClient, ReplayMissError


def fake_response(text: str) -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": text}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


def test_records_then_replays_without_transport(tmp_path):
    calls = []

    def transport(request: dict) -> dict:
        calls.append(request)
        return fake_response("hello")

    db = tmp_path / "llm_calls.sqlite"
    c1 = RecordingLLMClient(transport=transport, db_path=db, model="m1")
    r1 = c1.chat(messages=[{"role": "user", "content": "hi"}])
    assert r1["choices"][0]["message"]["content"] == "hello"
    assert len(calls) == 1

    # same request again: served from cache, transport NOT called
    r2 = c1.chat(messages=[{"role": "user", "content": "hi"}])
    assert r2 == r1
    assert len(calls) == 1

    # new client on same db, offline: still served
    def exploding_transport(request: dict) -> dict:
        raise AssertionError("offline client must not call transport")

    c2 = RecordingLLMClient(
        transport=exploding_transport, db_path=db, model="m1", offline=True
    )
    r3 = c2.chat(messages=[{"role": "user", "content": "hi"}])
    assert r3["choices"][0]["message"]["content"] == "hello"


def test_offline_miss_raises_with_hash(tmp_path):
    c = RecordingLLMClient(
        transport=lambda req: fake_response("x"),
        db_path=tmp_path / "db.sqlite",
        model="m1",
        offline=True,
    )
    with pytest.raises(ReplayMissError) as exc:
        c.chat(messages=[{"role": "user", "content": "never seen"}])
    assert len(str(exc.value)) > 20  # message carries the request hash


def test_key_varies_with_params(tmp_path):
    responses = iter([fake_response("a"), fake_response("b")])
    c = RecordingLLMClient(
        transport=lambda req: next(responses),
        db_path=tmp_path / "db.sqlite",
        model="m1",
    )
    r1 = c.chat(messages=[{"role": "user", "content": "hi"}], temperature=0.0)
    r2 = c.chat(messages=[{"role": "user", "content": "hi"}], temperature=0.9)
    assert r1["choices"][0]["message"]["content"] == "a"
    assert r2["choices"][0]["message"]["content"] == "b"


def test_temperature_int_float_same_key(tmp_path):
    calls = []

    def transport(request):
        calls.append(request)
        return fake_response("t")

    c = RecordingLLMClient(transport=transport, db_path=tmp_path / "db.sqlite", model="m1")
    c.chat(messages=[{"role": "user", "content": "hi"}], temperature=0)
    c.chat(messages=[{"role": "user", "content": "hi"}], temperature=0.0)
    assert len(calls) == 1


def test_cjk_content_replays_equal(tmp_path):
    db = tmp_path / "db.sqlite"
    c1 = RecordingLLMClient(
        transport=lambda r: fake_response("英伟达数据中心需求强劲，Blackwell 供不应求。"),
        db_path=db,
        model="m1",
    )
    r1 = c1.chat(messages=[{"role": "user", "content": "中文测试 ± émojis 🚀"}])
    c2 = RecordingLLMClient(
        transport=lambda r: (_ for _ in ()).throw(AssertionError("offline")),
        db_path=db,
        model="m1",
        offline=True,
    )
    r2 = c2.chat(messages=[{"role": "user", "content": "中文测试 ± émojis 🚀"}])
    assert r2 == r1


def test_tools_order_changes_key(tmp_path):
    calls = []

    def transport(request):
        calls.append(request)
        return fake_response(f"call-{len(calls)}")

    c = RecordingLLMClient(transport=transport, db_path=tmp_path / "db.sqlite", model="m1")
    tools_a = [{"name": "search"}, {"name": "calc"}]
    tools_b = [{"name": "calc"}, {"name": "search"}]
    c.chat(messages=[{"role": "user", "content": "hi"}], tools=tools_a)
    c.chat(messages=[{"role": "user", "content": "hi"}], tools=tools_b)
    assert len(calls) == 2
