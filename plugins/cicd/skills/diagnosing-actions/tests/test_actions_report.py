import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "actions_report.py"


def load_module():
    spec = importlib.util.spec_from_file_location("diagnosing_actions_report", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


report = load_module()


def test_parse_target_urls_and_tokens():
    run = report.parse_target("https://github.com/acme/app/actions/runs/99/attempts/2")
    assert run.kind == "run"
    assert run.repo == "acme/app"
    assert run.run_id == "99"
    assert run.attempt == "2"
    assert run.job_id is None

    job = report.parse_target("https://github.com/acme/app/actions/runs/99/job/50")
    assert job.kind == "job"
    assert job.run_id == "99"
    assert job.job_id == "50"

    legacy = report.parse_target("https://github.com/acme/app/runs/50")
    assert legacy.kind == "job"
    assert legacy.job_id == "50"
    assert legacy.run_id is None

    pr = report.parse_target("https://github.com/acme/app/pull/12/checks?check_run_id=50")
    assert pr.kind == "job"
    assert pr.pr_number == "12"
    assert pr.job_id == "50"

    assert report.parse_target("#12").pr_number == "12"
    assert report.parse_target("run:99").kind == "run"
    assert report.parse_target(None).kind == "pr"
    assert report.parse_target(None).pr_number is None

    with pytest.raises(SystemExit):
        report.parse_target("not-a-target")


def test_parse_failed_log_strips_noise():
    text = (
        "discover\tRead release targets\t\ufeff2026-10-20T00:27:07.6159400Z error: Failed to build `pywinpty`\n"
        "discover\tRead release targets\t2026-10-20T00:26:51.9665071Z \x1b[36;1mimport json\x1b[0m\n"
        "discover\tRead release targets\t2026-10-20T00:27:07.6244995Z ##[error]Process completed with exit code 1.\n"
    )
    grouped = report.parse_failed_log(text)
    lines = grouped[("discover", "Read release targets")]
    assert lines[0] == "error: Failed to build `pywinpty`"
    assert lines[1] == "import json"
    assert lines[2] == "##[error]Process completed with exit code 1."


def test_excerpt_keeps_error_window_and_headline_skips_generic_exit():
    lines = [f"noise {index}" for index in range(30)]
    lines.append("error: Failed to build `pywinpty==3.0.5`")
    lines.extend(
        [
            "  cause: The build backend returned an error",
            "error[E0425]: cannot find function `command_ok` in this scope",
            "##[error]Process completed with exit code 1.",
        ]
    )
    excerpt, note = report.extract_excerpt(lines)
    assert "error: Failed to build `pywinpty==3.0.5`" in excerpt
    assert "error[E0425]: cannot find function `command_ok` in this scope" in excerpt
    assert note.startswith("全34行からエラー周辺")
    assert report.headline_from(lines, []) == "error: Failed to build `pywinpty==3.0.5`"


def test_classify_rollup_separates_actions_external_and_pending():
    summary = report.classify_rollup(
        [
            {
                "name": "discover",
                "status": "COMPLETED",
                "conclusion": "FAILURE",
                "workflowName": "Tool release",
                "detailsUrl": "https://github.com/acme/app/actions/runs/10/job/20",
            },
            {
                "name": "lint",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
                "workflowName": "CI",
                "detailsUrl": "https://github.com/acme/app/actions/runs/11/job/21",
            },
            {
                "name": "setup",
                "status": "COMPLETED",
                "conclusion": "SKIPPED",
                "workflowName": "CI",
                "detailsUrl": "https://github.com/acme/app/actions/runs/11/job/22",
            },
            {
                "context": "codecov",
                "state": "FAILURE",
                "targetUrl": "https://codecov.io/build",
            },
            {
                "name": "deploy",
                "status": "IN_PROGRESS",
                "conclusion": "",
                "workflowName": "Deploy",
                "detailsUrl": "https://github.com/acme/app/actions/runs/12/job/30",
            },
            {
                "name": "other",
                "status": "COMPLETED",
                "conclusion": "CANCELLED",
                "workflowName": "CI",
                "detailsUrl": "https://github.com/acme/app/actions/runs/11/job/23",
            },
        ]
    )
    assert [check.job_id for check in summary.failed_actions] == ["20"]
    assert summary.failed_actions[0].run_id == "10"
    assert summary.success_count == 1
    assert summary.skipped_count == 1
    assert len(summary.pending) == 1
    assert len(summary.cancelled) == 1
    assert any("codecov" in line for line in summary.external_failures)


def test_cancelled_only_rollup_is_fetched():
    summary = report.classify_rollup(
        [
            {
                "name": "build",
                "status": "COMPLETED",
                "conclusion": "CANCELLED",
                "workflowName": "CI",
                "detailsUrl": "https://github.com/acme/app/actions/runs/10/job/20",
            }
        ]
    )
    assert len(summary.failed_actions) == 1
    assert summary.failed_actions[0].conclusion == "cancelled"
    assert summary.cancelled == []


def test_write_report_index_points_at_job_file(tmp_path):
    doc = report.JobDocument(
        workflow_name="Tool release",
        run_id="10",
        run_url="https://github.com/acme/app/actions/runs/10",
        event="push",
        head_branch="main",
        head_sha="abc",
        job_name="discover",
        job_id="20",
        job_url="https://github.com/acme/app/actions/runs/10/job/20",
        conclusion="failure",
        failed_steps=["Read release targets"],
        annotations=[
            {
                "level": "failure",
                "path": ".github",
                "line": 212,
                "message": "Process completed with exit code 1.",
            }
        ],
        step_logs=[
            (
                "Read release targets",
                [
                    "preparing",
                    "error: Failed to build `pywinpty==3.0.5`",
                    "##[error]Process completed with exit code 1.",
                ],
            )
        ],
    )
    subject = report.Subject(
        title="GitHub Actions 失敗 INDEX: Tool release", label="run10", lines=["対象: run 10"]
    )
    index_path, written = report.write_report(tmp_path, subject, [doc], report.ReportNotes())
    index = index_path.read_text(encoding="utf-8")
    assert "jobs/001_discover.md" in index
    assert "error: Failed to build `pywinpty==3.0.5`" in index
    job_file = (tmp_path / "jobs" / "001_discover.md").read_text(encoding="utf-8")
    assert "error: Failed to build `pywinpty==3.0.5`" in job_file
    assert written[0].headline.startswith("error: Failed to build")


def test_notes_for_other_jobs_counts_skip_and_lists_cancelled():
    notes = report.notes_for_other_jobs(
        [
            {
                "databaseId": 1,
                "name": "discover",
                "conclusion": "failure",
                "url": "https://example/1",
            },
            {
                "databaseId": 2,
                "name": "release",
                "conclusion": "skipped",
                "url": "https://example/2",
            },
            {
                "databaseId": 3,
                "name": "notify",
                "conclusion": "cancelled",
                "url": "https://example/3",
            },
        ],
        {"1"},
    )
    assert notes.skipped_count == 1
    assert notes.success_count == 0
    assert notes.unfetched_failures == []
    assert any("notify" in line and "cancelled" in line for line in notes.cancelled)


def test_split_markdown_breaks_on_step_heading():
    header = ["# job", ""] + ["- meta"] * 20
    step_a = ["## step: one", ""] + ["error: one"] * 200
    step_b = ["## step: two", ""] + ["error: two"] * 200
    text = "\n".join(header + step_a + step_b) + "\n"
    parts = report.split_markdown(text, max_lines=250)
    assert len(parts) == 2
    assert "## step: one" in parts[0]
    assert "## step: two" in parts[1]
    assert parts[1].startswith("（続き）")
