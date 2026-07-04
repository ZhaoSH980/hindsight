import json
from pathlib import Path

from hindsight.eval.suite import PRESETS, run_suite
from hindsight.schemas import RunConfig
from hindsight.store.db import Store


def test_suite_passes_one_snapshot_and_orders_cases(case_dir, tmp_path):
    calls = []

    def fake_run(case_dir, config, *, llm, store, runs_root, suite_id, suite_started_at):
        calls.append(
            {"case": Path(case_dir).name, "config": config.model_dump(),
             "suite_id": suite_id, "snap": suite_started_at}
        )

        class R:
            scores = {"outcome": {"hit_rate": 1.0}}
            run_id = f"r{len(calls)}"

        return R()

    store = Store(tmp_path / "h.db")
    suite_id = run_suite(
        [case_dir],
        {"base": RunConfig(model="m"), "memory": RunConfig(model="m", memory_on=True)},
        llm=None,
        store=store,
        runs_root=tmp_path / "runs",
        run_fn=fake_run,
    )
    assert len(calls) == 2  # 1 case x 2 configs
    snaps = {c["snap"] for c in calls}
    assert len(snaps) == 1 and None not in snaps  # single shared snapshot
    assert {c["suite_id"] for c in calls} == {suite_id}
    summary = json.loads(
        (tmp_path / "runs" / "suites" / f"{suite_id}.json").read_text(encoding="utf-8")
    )
    assert summary["configs"] == ["base", "memory"]
    assert summary["results"]["fixture_case"]["base"]["outcome"]["hit_rate"] == 1.0


def test_presets_exist():
    assert set(PRESETS) == {"base", "memory", "tight"}
    assert PRESETS["memory"].memory_on is True
    assert PRESETS["tight"].context_budget == 2000


def test_suite_id_can_be_preassigned(case_dir, tmp_path):
    def fake_run(case_dir, config, *, llm, store, runs_root, suite_id, suite_started_at):
        class R:
            scores = {"outcome": {"hit_rate": 1.0}}
            run_id = "r1"

        return R()

    store = Store(tmp_path / "h.db")
    returned_id = run_suite(
        [case_dir],
        {"base": RunConfig(model="m")},
        llm=None,
        store=store,
        runs_root=tmp_path / "runs",
        run_fn=fake_run,
        suite_id="suite_preassigned_001",
    )
    assert returned_id == "suite_preassigned_001"
    assert (tmp_path / "runs" / "suites" / "suite_preassigned_001.json").exists()
