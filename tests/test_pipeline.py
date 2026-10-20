import asyncio
from pathlib import Path

import pytest

from judge_audit import data, judges, report, run

DATASET = Path(__file__).parents[1] / "datasets" / "finance"


def test_finance_dataset_loads_and_is_balanced_enough():
    items = data.load(DATASET)
    passes = sum(i.label for i in items)
    assert len(items) >= 60
    assert 0.35 < passes / len(items) < 0.75
    # Every rubric has at least one passing and one failing response.
    by_rubric = {}
    for i in items:
        by_rubric.setdefault((i.task, i.rubric), set()).add(i.label)
    assert all(s == {True, False} for s in by_rubric.values()), by_rubric


def test_kinds_match_labels():
    for i in data.load(DATASET):
        assert i.label == (i.kind != "minimal-fail"), i.id


def test_invariance_groups_point_at_references():
    items = data.load(DATASET)
    groups = data.invariance_groups(items)
    ids = {i.id for i in items}
    assert groups and all(r in ids and set(v) <= ids for r, v in groups.items())
    assert all("/reference/" in r for r in groups)


def test_loader_rejects_a_label_for_an_unknown_rubric(tmp_path):
    (tmp_path / "t.toml").write_text('prompt = "p"\n[rubrics]\na = "c"\n'
                                     '[[response]]\nid = "r"\nkind = "reference"\n'
                                     'labels = { b = true }\ntext = "x"\n')
    with pytest.raises(ValueError, match="unknown rubric 'b'"):
        data.load(tmp_path)


@pytest.mark.parametrize("reply,expected", [
    ("Meets every clause.\nVERDICT: PASS", True),
    ("**VERDICT: FAIL**", False),
    ("VERDICT: PASS ... on reflection\nVERDICT: FAIL", False),  # last one wins
    ("I think it passes.", None),
])
def test_parse_verdict(reply, expected):
    assert judges.parse_verdict(reply) is expected


def test_judge_argv_isolates_the_cli():
    argv = judges.ClaudeCLI("haiku").argv("hi")
    for flag in ("--tools", "--strict-mcp-config", "--setting-sources", "--system-prompt",
                 "--no-session-persistence"):
        assert flag in argv
    assert argv[-1] == "hi"


def test_collect_resumes_and_report_renders(tmp_path, monkeypatch):
    items = [i for i in data.load(DATASET) if i.task == "debt-build"]

    class Fake:
        def __init__(self, model):
            self.calls = 0

        async def judge(self, item):
            self.calls += 1
            # Always passes: right on PASS items, wrong on FAIL items, every time.
            return judges.Judgment(True, "VERDICT: PASS", "fake-1", 0.001)

    monkeypatch.setattr(run, "ClaudeCLI", Fake)
    log = tmp_path / "v.jsonl"
    n1 = asyncio.run(run.collect(items, ["fake"], 3, log, progress=lambda s: None))
    n2 = asyncio.run(run.collect(items, ["fake"], 3, log, progress=lambda s: None))
    assert (n1, n2) == (3 * len(items), 0)

    rows = run.read_log(log)
    s = report.summarize(report.votes_by_judge(rows, items)["fake"], items)
    fails = sum(not i.label for i in items)
    assert s["false_pass"] == 1 and s["false_fail"] == 0
    assert s["accuracy"] == pytest.approx(1 - fails / len(items))
    assert s["flip_rate"] == 0 and s["majority_accuracy"] == s["accuracy"]
    md = report.markdown(rows, items)
    assert "| fake | fake-1 |" in md and "debt-build/double-counted/components" in md
