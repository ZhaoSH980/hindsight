from hindsight.store.db import Store


def test_run_upsert_and_get(tmp_path):
    s = Store(tmp_path / "h.db")
    s.upsert_run("r1", "case_a", '{"model":"m"}', "running")
    s.upsert_run("r1", "case_a", '{"model":"m"}', "done", scores_json='{"hit_rate":1.0}')
    rows = s.get_runs()
    assert len(rows) == 1
    assert rows[0]["run_id"] == "r1"
    assert rows[0]["status"] == "done"
    assert rows[0]["scores_json"] == '{"hit_rate":1.0}'


def test_runs_filter_by_suite(tmp_path):
    s = Store(tmp_path / "h.db")
    s.upsert_run("r1", "c", "{}", "done", suite_id="s1")
    s.upsert_run("r2", "c", "{}", "done", suite_id="s2")
    assert [r["run_id"] for r in s.get_runs(suite_id="s1")] == ["r1"]


def test_experience_time_gate_and_leave_one_out(tmp_path):
    s = Store(tmp_path / "h.db")
    s.insert_experience("e1", "case_a", "r1", "2025-03-01", "2025-04-15", "NVDA earnings", "{}")
    s.insert_experience("e2", "case_b", "r2", "2025-05-01", "2025-06-30", "TSLA delivery", "{}")
    s.insert_experience("e3", "case_c", "r3", "2025-02-01", "2025-03-10", "SMCI filing", "{}")

    rows = s.query_experiences(as_of="2025-05-22", exclude_case_id="case_c")
    ids = {r["exp_id"] for r in rows}
    assert ids == {"e1"}  # e2 window not closed by as_of; e3 excluded (same case)


def test_experience_created_before_snapshot(tmp_path):
    s = Store(tmp_path / "h.db")
    s.insert_experience("e1", "case_a", "r1", "2025-03-01", "2025-04-15", "NVDA", "{}")
    future = "9999-01-01T00:00:00+00:00"
    past = "2000-01-01T00:00:00+00:00"
    assert s.query_experiences("2025-05-22", "other", created_before=future)
    assert s.query_experiences("2025-05-22", "other", created_before=past) == []
