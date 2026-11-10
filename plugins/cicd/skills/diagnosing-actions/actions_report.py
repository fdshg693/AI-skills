#!/usr/bin/env python3
"""GitHub Actions の失敗を gh CLI で取得し、temp/actions/ に INDEX 付きで書き出す。

読み取り専用。使うのは gh pr view / gh run view / gh api (GET) のみ。
ワークフローの再実行、watch、コメント投稿、merge は行わない。

使い方:
    python actions_report.py [TARGET] [--gh-repo OWNER/REPO]
                             [--repo PATH] [--output-dir DIR]

    TARGET:
      - Actions の run URL（.../actions/runs/ID、attempts や job 付きも可）
      - PR の URL、または PR 番号（123 / #123）
      - run:ID / run/ID（リポジトリは URL か --gh-repo、なければカレント）
      - 省略時はカレントブランチの PR

出力:
    temp/actions/<timestamp>_<label>/INDEX.md
    temp/actions/<timestamp>_<label>/jobs/001_<job>.md
    標準出力には INDEX.md のパスと、失敗ジョブごとの先頭エラーだけを出す。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# review スキルの分割と同じく、1ファイルを一画面で読める行数に揃える。
MAX_LINES_PER_FILE = 300
# コンパイラやテストの失敗は ##[error] より前に続くことが多いので、後側を厚く取る。
CONTEXT_BEFORE = 8
CONTEXT_AFTER = 40
# マーカーが無いときでも、終了コードは step の末尾に出ることが多い。
TAIL_LINES = 60
# 1 step の抜粋だけでファイル上限を超えないようにする。
MAX_EXCERPT_LINES = 220
# warning annotation は失敗特定の邪魔になりやすいので、少数のときだけ残す。
MAX_WARNING_ANNOTATIONS = 8
# 失敗ログのダウンロードが止まったときに待つ上限（秒）。
GH_TIMEOUT_SECONDS = 180

# ログを取りに行く conclusion。cancelled は他ジョブ失敗の巻き添えであることが多い。
LOG_CONCLUSIONS = frozenset({"failure", "timed_out", "startup_failure", "action_required"})
CANCELLED = "cancelled"
PENDING_STATES = frozenset({"queued", "in_progress", "pending", "waiting", "requested", "expected"})

RUN_JSON_FIELDS = (
    "attempt,conclusion,databaseId,displayTitle,event,headBranch,headSha,"
    "jobs,name,status,url,workflowName"
)

_HOST = r"https?://[^/\s]+"
_RUN_URL = re.compile(
    _HOST + r"/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/actions/runs/(?P<run>\d+)"
    r"(?:/attempts/(?P<attempt>\d+))?(?:/job/(?P<job>\d+))?"
)
_LEGACY_JOB_URL = re.compile(_HOST + r"/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/runs/(?P<job>\d+)\b")
_PR_URL = re.compile(_HOST + r"/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/(?P<pr>\d+)")
_CHECK_RUN_QUERY = re.compile(r"[?&]check_run_id=(\d+)")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\s?")
_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_RUN_TOKEN = re.compile(r"run[:/](\d+)\Z", re.IGNORECASE)
_PR_TOKEN = re.compile(r"#?(\d+)\Z")

_SIGNAL_PATTERNS = (
    re.compile(r"##\[error\]"),
    re.compile(r"(?i)^error(\[[^\]]+\])?:"),
    re.compile(r"^Error:"),
    re.compile(r"^npm ERR!"),
    re.compile(r"^ELIFECYCLE"),
    re.compile(r"^FAILED\b"),
    re.compile(r"^Traceback \(most recent call last\)"),
    re.compile(r"(?i)^panic:"),
    re.compile(r"(?i)^fatal:"),
    re.compile(r"Process completed with exit code"),
    re.compile(r"returned non-zero exit status"),
)


@dataclass(frozen=True)
class Target:
    kind: str
    repo: str | None = None
    pr_number: str | None = None
    run_id: str | None = None
    job_id: str | None = None
    attempt: str | None = None


@dataclass
class ParsedCheck:
    name: str
    workflow: str
    conclusion: str
    url: str
    repo: str | None = None
    run_id: str | None = None
    job_id: str | None = None
    attempt: str | None = None


@dataclass
class RollupSummary:
    failed_actions: list[ParsedCheck] = field(default_factory=list)
    cancelled: list[str] = field(default_factory=list)
    external_failures: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    success_count: int = 0
    skipped_count: int = 0


@dataclass
class JobDocument:
    workflow_name: str
    run_id: str
    run_url: str
    event: str
    head_branch: str
    head_sha: str
    job_name: str
    job_id: str
    job_url: str
    conclusion: str
    failed_steps: list[str]
    annotations: list[dict]
    step_logs: list[tuple[str, list[str]]]
    log_error: str = ""
    annotation_error: str = ""


@dataclass
class Subject:
    title: str
    label: str
    lines: list[str]


@dataclass
class ReportNotes:
    cancelled: list[str] = field(default_factory=list)
    external_failures: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    success_count: int = 0
    skipped_count: int = 0
    unfetched_failures: list[str] = field(default_factory=list)


@dataclass
class WrittenPart:
    path: Path
    steps: list[str]
    line_count: int
    headline: str


@dataclass
class WrittenJob:
    workflow_name: str
    job_name: str
    conclusion: str
    headline: str
    parts: list[WrittenPart]


def reconfigure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def ensure_gh_available() -> None:
    if shutil.which("gh") is None:
        raise SystemExit(
            "エラー: gh CLI が見つかりません。"
            "https://cli.github.com/ からインストールし、`gh auth login` で認証してください。"
        )


def find_base_dir(start: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip())
    return start.resolve()


def repo_args(repo: str | None) -> list[str]:
    return ["-R", repo] if repo else []


def normalize_conclusion(value: str | None) -> str:
    return (value or "").strip().lower()


def clip(text: str, limit: int = 140) -> str:
    collapsed = re.sub(r"\s+", " ", text).strip()
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1] + "…"


def table_cell(text: str) -> str:
    return clip(text, 180).replace("|", "\\|")


def slugify(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return slug[:60] or "job"


def is_generic_exit(line: str) -> bool:
    return "process completed with exit code" in line.lower()


def is_signal_line(line: str) -> bool:
    text = line.strip()
    return any(pattern.search(text) for pattern in _SIGNAL_PATTERNS)


def strip_log_body(body: str) -> str:
    text = body.lstrip("\ufeff")
    text = _ANSI.sub("", text)
    text = _TIMESTAMP.sub("", text)
    return text.rstrip()


def parse_failed_log(text: str) -> dict[tuple[str, str], list[str]]:
    """gh run view --log-failed の TSV を (job, step) ごとの行に分ける。"""
    grouped: dict[tuple[str, str], list[str]] = {}
    for raw in text.splitlines():
        raw = raw.lstrip("\ufeff")
        if raw == "":
            continue
        parts = raw.split("\t", 2)
        if len(parts) < 3:
            job, step, body = "UNKNOWN JOB", "UNKNOWN STEP", raw
        else:
            job, step, body = parts
        grouped.setdefault((job, step), []).append(strip_log_body(body))
    return grouped


def parse_url(text: str) -> Target | None:
    run = _RUN_URL.search(text)
    if run:
        job_id = run.group("job")
        return Target(
            kind="job" if job_id else "run",
            repo=f"{run.group('owner')}/{run.group('repo')}",
            run_id=run.group("run"),
            job_id=job_id,
            attempt=run.group("attempt"),
        )
    legacy = _LEGACY_JOB_URL.search(text)
    if legacy:
        return Target(
            kind="job",
            repo=f"{legacy.group('owner')}/{legacy.group('repo')}",
            job_id=legacy.group("job"),
        )
    pr = _PR_URL.search(text)
    if pr:
        check = _CHECK_RUN_QUERY.search(text)
        job_id = check.group(1) if check else None
        return Target(
            kind="job" if job_id else "pr",
            repo=f"{pr.group('owner')}/{pr.group('repo')}",
            pr_number=pr.group("pr"),
            job_id=job_id,
        )
    return None


def parse_target(raw: str | None) -> Target:
    if raw is None or raw.strip() == "":
        return Target(kind="pr")
    text = raw.strip()
    parsed = parse_url(text)
    if parsed is not None:
        return parsed
    run_token = _RUN_TOKEN.fullmatch(text)
    if run_token:
        return Target(kind="run", run_id=run_token.group(1))
    pr_token = _PR_TOKEN.fullmatch(text)
    if pr_token and int(pr_token.group(1)) > 0:
        return Target(kind="pr", pr_number=pr_token.group(1))
    raise SystemExit(
        "エラー: TARGET には Actions の URL、PR の URL、PR番号（123 / #123）、"
        f"または run:ID を指定してください: {raw}"
    )


def with_repo(target: Target, gh_repo: str | None) -> Target:
    if target.repo or not gh_repo:
        return target
    return Target(
        kind=target.kind,
        repo=gh_repo,
        pr_number=target.pr_number,
        run_id=target.run_id,
        job_id=target.job_id,
        attempt=target.attempt,
    )


def check_name(item: dict) -> str:
    return str(item.get("name") or item.get("context") or "(無名)")


def check_url(item: dict) -> str:
    return str(item.get("detailsUrl") or item.get("targetUrl") or "")


def display_check(name: str, workflow: str, url: str) -> str:
    prefix = f"{workflow} / {name}" if workflow else name
    return f"{prefix} {url}".strip()


def classify_rollup(items: list) -> RollupSummary:
    summary = RollupSummary()
    if not isinstance(items, list):
        return summary
    for item in items:
        if not isinstance(item, dict):
            continue
        name = check_name(item)
        workflow = str(item.get("workflowName") or "")
        url = check_url(item)
        conclusion = normalize_conclusion(item.get("conclusion") or item.get("state"))
        status = normalize_conclusion(item.get("status") or item.get("state"))
        shown = display_check(name, workflow, url)
        if not conclusion and (status in PENDING_STATES or status == ""):
            summary.pending.append(shown)
            continue
        if conclusion in {"success", "neutral", "pass", "passing"}:
            summary.success_count += 1
            continue
        if conclusion == "skipped":
            summary.skipped_count += 1
            continue
        parsed_url = parse_url(url) if url else None
        actions_target = parsed_url if parsed_url and parsed_url.kind in {"run", "job"} else None
        if conclusion == CANCELLED:
            summary.cancelled.append(shown)
            continue
        if conclusion in LOG_CONCLUSIONS or conclusion in {
            "failure",
            "failed",
            "error",
            "timed_out",
        }:
            if actions_target is None:
                summary.external_failures.append(shown)
                continue
            summary.failed_actions.append(
                ParsedCheck(
                    name=name,
                    workflow=workflow,
                    conclusion=conclusion if conclusion in LOG_CONCLUSIONS else "failure",
                    url=url,
                    repo=actions_target.repo,
                    run_id=actions_target.run_id,
                    job_id=actions_target.job_id,
                    attempt=actions_target.attempt,
                )
            )
            continue
        if conclusion:
            summary.external_failures.append(shown)
    if not summary.failed_actions and summary.cancelled:
        # 失敗が cancelled だけのときは、それ以上原因が無いのでログを取りに行く。
        summary.failed_actions = []
        promoted: list[ParsedCheck] = []
        still_cancelled: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            conclusion = normalize_conclusion(item.get("conclusion") or item.get("state"))
            if conclusion != CANCELLED:
                continue
            url = check_url(item)
            parsed_url = parse_url(url) if url else None
            if parsed_url and parsed_url.kind in {"run", "job"}:
                promoted.append(
                    ParsedCheck(
                        name=check_name(item),
                        workflow=str(item.get("workflowName") or ""),
                        conclusion=CANCELLED,
                        url=url,
                        repo=parsed_url.repo,
                        run_id=parsed_url.run_id,
                        job_id=parsed_url.job_id,
                        attempt=parsed_url.attempt,
                    )
                )
            else:
                still_cancelled.append(
                    display_check(check_name(item), str(item.get("workflowName") or ""), url)
                )
        summary.failed_actions = promoted
        summary.cancelled = still_cancelled
    return summary


def extract_excerpt(lines: list[str]) -> tuple[list[str], str]:
    total = len(lines)
    if total == 0:
        return [], "ログ行なし"
    hits = [index for index, line in enumerate(lines) if is_signal_line(line)]
    if not hits:
        tail = lines[-TAIL_LINES:]
        return tail, f"エラー行が無いため末尾 {len(tail)}行（全{total}行）"

    ranges: list[list[int]] = []
    for index in hits:
        start = max(0, index - CONTEXT_BEFORE)
        end = min(total, index + CONTEXT_AFTER + 1)
        if ranges and start <= ranges[-1][1]:
            ranges[-1][1] = max(ranges[-1][1], end)
        else:
            ranges.append([start, end])

    covered = sum(end - start for start, end in ranges)
    selected = ranges
    if covered > MAX_EXCERPT_LINES and len(ranges) > 1:
        selected = [ranges[0], ranges[-1]]

    excerpt: list[str] = []
    previous_end: int | None = None
    for start, end in selected:
        if previous_end is not None and start > previous_end:
            excerpt.append(f"... ({start - previous_end}行省略) ...")
        excerpt.extend(lines[start:end])
        previous_end = end
    if len(excerpt) > MAX_EXCERPT_LINES:
        excerpt = excerpt[:MAX_EXCERPT_LINES]
        excerpt.append("... (抜粋上限で打ち切り) ...")
    shown = sum(1 for line in excerpt if not line.startswith("... ("))
    return excerpt, f"全{total}行からエラー周辺 {shown}行を抜粋"


def headline_from(lines: list[str], annotations: list[dict]) -> str:
    signals = [line.strip() for line in lines if is_signal_line(line)]
    specific = [line for line in signals if not is_generic_exit(line)]
    if specific:
        return clip(specific[0])
    annotation_messages = [
        item["message"].strip()
        for item in annotations
        if item.get("level") == "failure"
        and item.get("message")
        and not is_generic_exit(item["message"])
    ]
    if annotation_messages:
        return clip(annotation_messages[0])
    if signals:
        return clip(signals[0])
    generic_annotations = [
        item["message"].strip()
        for item in annotations
        if item.get("level") == "failure" and item.get("message")
    ]
    if generic_annotations:
        return clip(generic_annotations[0])
    return "エラー行を検出できず"


def visible_annotations(annotations: list[dict]) -> tuple[list[dict], str]:
    failures = [item for item in annotations if item.get("level") == "failure"]
    warnings = [item for item in annotations if item.get("level") == "warning"]
    shown = failures + warnings[:MAX_WARNING_ANNOTATIONS]
    note = ""
    if len(warnings) > MAX_WARNING_ANNOTATIONS:
        note = f"warning annotation は {len(warnings)} 件中 {MAX_WARNING_ANNOTATIONS} 件を表示"
    return shown, note


def fence(text: str) -> str:
    tick = "```"
    while tick in text:
        tick += "`"
    body = text if text.endswith("\n") or text == "" else text + "\n"
    return f"{tick}text\n{body}{tick}\n"


def render_job_markdown(doc: JobDocument) -> str:
    lines = [
        f"# {doc.job_name}",
        "",
        f"- workflow: {doc.workflow_name}",
        f"- run: {doc.run_id} {doc.run_url}".rstrip(),
        f"- job: {doc.job_id} {doc.job_url}".rstrip(),
        f"- conclusion: {doc.conclusion}",
        f"- event: {doc.event}",
        f"- branch: {doc.head_branch}",
        f"- head: {doc.head_sha}",
        f"- 失敗step: {', '.join(doc.failed_steps) if doc.failed_steps else '（step conclusion なし）'}",
        "",
    ]
    shown, warning_note = visible_annotations(doc.annotations)
    lines.append("## annotations")
    lines.append("")
    if doc.annotation_error:
        lines.append(f"取得できませんでした: {doc.annotation_error}")
        lines.append("")
    if not shown and not doc.annotation_error:
        lines.append("（failure / warning の annotation なし）")
        lines.append("")
    for item in shown:
        location = item.get("path") or "(pathなし)"
        if item.get("line"):
            location = f"{location}:{item['line']}"
        message = clip(item.get("message") or "", 500)
        lines.append(f"- {item.get('level') or 'note'} `{location}` {message}")
    if warning_note:
        lines.append(f"- {warning_note}")
    lines.append("")

    if doc.log_error and not doc.step_logs:
        lines += ["## ログ", "", f"取得できませんでした: {doc.log_error}", ""]
        return "\n".join(lines).rstrip() + "\n"

    if not doc.step_logs:
        lines += ["## ログ", "", "失敗stepのログは空でした。", ""]
        return "\n".join(lines).rstrip() + "\n"

    for step_name, step_lines in doc.step_logs:
        excerpt, note = extract_excerpt(step_lines)
        lines.append(f"## step: {step_name}")
        lines.append("")
        lines.append(note)
        lines.append("")
        if excerpt:
            lines.append(fence("\n".join(excerpt)))
        else:
            lines.append("（このstepのログは --log-failed に含まれていなかった）")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def split_markdown(text: str, max_lines: int = MAX_LINES_PER_FILE) -> list[str]:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return [text if text.endswith("\n") else text + "\n"]

    sections: list[list[str]] = []
    start = 0
    for index, line in enumerate(lines):
        if index > 0 and line.startswith("## step:"):
            sections.append(lines[start:index])
            start = index
    sections.append(lines[start:])

    parts: list[list[str]] = []
    current: list[str] = []
    for section in sections:
        if len(section) > max_lines:
            if current:
                parts.append(current)
                current = []
            for offset in range(0, len(section), max_lines):
                parts.append(section[offset : offset + max_lines])
            continue
        if current and len(current) + len(section) > max_lines:
            parts.append(current)
            current = []
        current.extend(section)
    if current:
        parts.append(current)

    rendered: list[str] = []
    for index, part in enumerate(parts):
        body = "\n".join(part).rstrip() + "\n"
        if index > 0:
            body = "（続き）\n\n" + body
        rendered.append(body)
    return rendered


def steps_in_text(text: str) -> list[str]:
    found = []
    for line in text.splitlines():
        if line.startswith("## step:"):
            found.append(line.removeprefix("## step:").strip())
    return found


def part_headline(text: str, fallback: str) -> str:
    signals = [line.strip() for line in text.splitlines() if is_signal_line(line)]
    specific = [line for line in signals if not is_generic_exit(line)]
    if specific:
        return clip(specific[0])
    if signals:
        return clip(signals[0])
    return fallback


def write_jobs(output_dir: Path, docs: list[JobDocument]) -> list[WrittenJob]:
    if not docs:
        return []
    jobs_dir = output_dir / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    width = max(3, len(str(len(docs))))
    written: list[WrittenJob] = []
    for index, doc in enumerate(docs, start=1):
        body = render_job_markdown(doc)
        parts = split_markdown(body)
        all_lines = [line for _, step_lines in doc.step_logs for line in step_lines]
        fallback = headline_from(all_lines, doc.annotations)
        slug = slugify(doc.job_name)
        prefix = f"{index:0{width}d}_{slug}"
        written_parts: list[WrittenPart] = []
        if len(parts) == 1:
            path = jobs_dir / f"{prefix}.md"
            path.write_text(parts[0], encoding="utf-8", newline="\n")
            written_parts.append(
                WrittenPart(
                    path,
                    steps_in_text(parts[0]),
                    count_lines(parts[0]),
                    part_headline(parts[0], fallback),
                )
            )
        else:
            part_width = max(2, len(str(len(parts))))
            for part_index, part in enumerate(parts, start=1):
                path = jobs_dir / f"{prefix}_part{part_index:0{part_width}d}.md"
                path.write_text(part, encoding="utf-8", newline="\n")
                written_parts.append(
                    WrittenPart(
                        path,
                        steps_in_text(part),
                        count_lines(part),
                        part_headline(part, fallback if part_index == 1 else "（続き）"),
                    )
                )
        written.append(
            WrittenJob(
                workflow_name=doc.workflow_name,
                job_name=doc.job_name,
                conclusion=doc.conclusion,
                headline=fallback,
                parts=written_parts,
            )
        )
    return written


def count_lines(text: str) -> int:
    if text == "":
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def build_index(
    subject: Subject, written: list[WrittenJob], notes: ReportNotes, output_dir: Path
) -> str:
    lines = [f"# {subject.title}", "", f"- 出力先: {output_dir.as_posix()}"]
    lines += [f"- {line}" for line in subject.lines]
    problem_count = sum(1 for job in written if is_problem_conclusion(job.conclusion))
    lines.append(f"- 失敗ジョブ: {problem_count}")
    lines.append(
        f"- 成功: {notes.success_count} / スキップ: {notes.skipped_count} / "
        f"未完了: {len(notes.pending)} / cancelled（ログ未取得）: {len(notes.cancelled)} / "
        f"Actions以外の失敗: {len(notes.external_failures)}"
    )
    lines.append("")
    lines.append(
        "失敗ジョブは下の表のファイルだけを開く。先頭列で足りなければ、そのファイルのエラー周辺を読む。"
    )
    lines.append("")
    if not written:
        lines.append("失敗した GitHub Actions ジョブのログはありません。")
        lines.append("")
    else:
        lines += [
            "| # | ファイル | workflow | job | conclusion | このファイルのstep | 行数 | 先頭 |",
            "|---|---|---|---|---|---|---|---|",
        ]
        row = 1
        for job in written:
            for part in job.parts:
                step_label = ", ".join(part.steps) if part.steps else "（step見出しなし）"
                rel = f"jobs/{part.path.name}"
                lines.append(
                    "| "
                    + " | ".join(
                        [
                            str(row),
                            rel,
                            table_cell(job.workflow_name),
                            table_cell(job.job_name),
                            table_cell(job.conclusion),
                            table_cell(step_label),
                            str(part.line_count),
                            table_cell(part.headline),
                        ]
                    )
                    + " |"
                )
                row += 1
        lines.append("")

    def add_section(title: str, entries: list[str]) -> None:
        if not entries:
            return
        lines.append(f"## {title}")
        lines.append("")
        for entry in entries:
            lines.append(f"- {entry}")
        lines.append("")

    add_section("未完了", notes.pending)
    add_section("cancelled（ログ未取得）", notes.cancelled)
    add_section("Actions以外、またはURLからrunを特定できない失敗", notes.external_failures)
    add_section(
        "同じrunにあるが、この指定ではログを取っていない失敗ジョブ", notes.unfetched_failures
    )
    return "\n".join(lines).rstrip() + "\n"


def write_report(
    output_dir: Path,
    subject: Subject,
    docs: list[JobDocument],
    notes: ReportNotes,
) -> tuple[Path, list[WrittenJob]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written = write_jobs(output_dir, docs)
    index_path = output_dir / "INDEX.md"
    index_path.write_text(
        build_index(subject, written, notes, output_dir),
        encoding="utf-8",
        newline="\n",
    )
    return index_path, written


def is_problem_conclusion(conclusion: str) -> bool:
    return conclusion in LOG_CONCLUSIONS or conclusion == CANCELLED


def emit_summary(index_path: Path, written: list[WrittenJob]) -> None:
    print(index_path.as_posix())
    problems = [job for job in written if is_problem_conclusion(job.conclusion)]
    if not problems:
        if written:
            print("指定したジョブは失敗していません。INDEXに conclusion を書いてあります。")
        else:
            print("失敗したGitHub Actionsジョブはありません。")
        return
    print(f"失敗ジョブ: {len(problems)}")
    for job in problems:
        names = ", ".join(f"jobs/{part.path.name}" for part in job.parts)
        print(f"- {job.workflow_name} / {job.job_name}: {job.headline} -> {names}")


def failed_step_names(job: dict) -> list[str]:
    names = []
    for step in job.get("steps") or []:
        if normalize_conclusion(step.get("conclusion")) in LOG_CONCLUSIONS | {CANCELLED}:
            names.append(str(step.get("name") or "(無名step)"))
    return names


def assemble_step_logs(
    failed_steps: list[str], grouped_steps: dict[str, list[str]]
) -> list[tuple[str, list[str]]]:
    ordered: list[tuple[str, list[str]]] = []
    used: set[str] = set()
    for name in failed_steps:
        ordered.append((name, grouped_steps.get(name, [])))
        used.add(name)
    for name, lines in grouped_steps.items():
        if name in used:
            continue
        if any(is_signal_line(line) for line in lines):
            ordered.append((name, lines))
    if not ordered and grouped_steps:
        ordered.extend(grouped_steps.items())
    return ordered


def flatten_grouped_log(grouped: dict[tuple[str, str], list[str]]) -> dict[str, list[str]]:
    steps: dict[str, list[str]] = {}
    for (_job, step), lines in grouped.items():
        steps.setdefault(step, []).extend(lines)
    return steps


def steps_for_job(
    grouped: dict[tuple[str, str], list[str]], job_name: str, only_this_job: bool
) -> dict[str, list[str]]:
    if only_this_job:
        return flatten_grouped_log(grouped)
    steps: dict[str, list[str]] = {}
    for (name, step), lines in grouped.items():
        if name == job_name:
            steps.setdefault(step, []).extend(lines)
    if steps:
        return steps
    job_names = {name for name, _step in grouped}
    if len(job_names) == 1:
        return flatten_grouped_log(grouped)
    return {}


class GhClient:
    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd
        self._repo: str | None = None

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                ["gh", *args],
                cwd=str(self.cwd),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=GH_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"gh {' '.join(args)} が {GH_TIMEOUT_SECONDS} 秒以内に終わりませんでした。"
            ) from exc

    def gh(self, args: list[str]) -> str:
        result = self._run(args)
        if result.returncode != 0:
            raise RuntimeError(
                f"gh {' '.join(args)} failed:\n{result.stderr.strip()}\n"
                "（未認証の場合は `gh auth login`、別リポジトリは URL か --gh-repo OWNER/REPO）"
            )
        return result.stdout

    def gh_allow_empty(self, args: list[str]) -> tuple[str, str]:
        result = self._run(args)
        if result.returncode != 0 and not result.stdout.strip():
            message = result.stderr.strip() or f"終了コード {result.returncode}"
            return "", message
        return result.stdout, ""

    def current_repo(self) -> str:
        if self._repo is None:
            raw = self.gh(["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"])
            self._repo = raw.strip()
        return self._repo

    def view_pr(self, number: str | None, repo: str | None) -> dict:
        selector = [number] if number else []
        raw = self.gh(
            [
                "pr",
                "view",
                *selector,
                *repo_args(repo),
                "--json",
                "number,title,url,headRefOid,headRefName,statusCheckRollup",
            ]
        )
        return json.loads(raw)

    def view_run(self, repo: str, run_id: str, attempt: str | None) -> dict:
        args = ["run", "view", str(run_id), *repo_args(repo), "--json", RUN_JSON_FIELDS]
        if attempt:
            args += ["--attempt", str(attempt)]
        return json.loads(self.gh(args))

    def actions_job(self, repo: str, job_id: str) -> dict:
        raw = self.gh(["api", f"repos/{repo}/actions/jobs/{job_id}"])
        return json.loads(raw)

    def annotations(self, repo: str, job_id: str) -> tuple[list[dict], str]:
        raw, error = self.gh_allow_empty(["api", f"repos/{repo}/check-runs/{job_id}/annotations"])
        if error and not raw.strip():
            return [], error
        try:
            data = json.loads(raw or "[]")
        except json.JSONDecodeError:
            return [], "annotations のJSONを解釈できませんでした"
        if not isinstance(data, list):
            return [], "annotations の形式が配列ではありません"
        normalized = []
        for item in data:
            if not isinstance(item, dict):
                continue
            normalized.append(
                {
                    "level": item.get("annotation_level") or "",
                    "path": item.get("path") or "",
                    "line": item.get("start_line"),
                    "message": (item.get("message") or "").strip(),
                }
            )
        return normalized, ""

    def failed_log(
        self, repo: str, run_id: str, attempt: str | None, job_id: str | None
    ) -> tuple[str, str]:
        args = ["run", "view", str(run_id), *repo_args(repo), "--log-failed"]
        if job_id:
            args += ["--job", str(job_id)]
        if attempt:
            args += ["--attempt", str(attempt)]
        return self.gh_allow_empty(args)


def select_jobs(jobs: list[dict], only_job_ids: list[str] | None) -> list[dict]:
    if only_job_ids is not None:
        wanted = {str(job_id) for job_id in only_job_ids}
        return [job for job in jobs if str(job.get("databaseId")) in wanted]
    selected = [
        job for job in jobs if normalize_conclusion(job.get("conclusion")) in LOG_CONCLUSIONS
    ]
    if selected:
        return selected
    return [job for job in jobs if normalize_conclusion(job.get("conclusion")) == CANCELLED]


def notes_for_other_jobs(jobs: list[dict], selected_ids: set[str]) -> ReportNotes:
    """ログを書かなかったジョブを INDEX の件数と一覧に回す。"""
    notes = ReportNotes()
    for job in jobs:
        job_id = str(job.get("databaseId"))
        if job_id in selected_ids:
            continue
        conclusion = normalize_conclusion(job.get("conclusion"))
        label = f"{job.get('name') or '(無名)'} ({conclusion}) {job.get('url') or ''}".strip()
        if conclusion in {"success", "neutral", "pass", "passing"}:
            notes.success_count += 1
        elif conclusion == "skipped":
            notes.skipped_count += 1
        elif conclusion == CANCELLED:
            notes.cancelled.append(label)
        elif conclusion in LOG_CONCLUSIONS:
            notes.unfetched_failures.append(label)
        elif not conclusion or conclusion in PENDING_STATES:
            notes.pending.append(label)
    return notes


def documents_for_run(
    client: GhClient,
    repo: str,
    run: dict,
    only_job_ids: list[str] | None,
) -> list[JobDocument]:
    jobs = run.get("jobs") or []
    selected = select_jobs(jobs, only_job_ids)
    if not selected:
        return []

    single_job_id = str(selected[0].get("databaseId")) if len(selected) == 1 else None
    log_text, log_error = client.failed_log(
        repo,
        str(run.get("databaseId")),
        str(run.get("attempt")) if run.get("attempt") else None,
        single_job_id,
    )
    grouped = parse_failed_log(log_text)
    workflow = str(run.get("workflowName") or run.get("name") or "")
    docs: list[JobDocument] = []
    for job in selected:
        job_id = str(job.get("databaseId"))
        job_name = str(job.get("name") or "(無名)")
        failed_steps = failed_step_names(job)
        step_map = steps_for_job(grouped, job_name, only_this_job=single_job_id is not None)
        annotations, annotation_error = client.annotations(repo, job_id)
        docs.append(
            JobDocument(
                workflow_name=workflow,
                run_id=str(run.get("databaseId") or ""),
                run_url=str(run.get("url") or ""),
                event=str(run.get("event") or ""),
                head_branch=str(run.get("headBranch") or ""),
                head_sha=str(run.get("headSha") or ""),
                job_name=job_name,
                job_id=job_id,
                job_url=str(job.get("url") or ""),
                conclusion=normalize_conclusion(job.get("conclusion")) or "failure",
                failed_steps=failed_steps,
                annotations=annotations,
                step_logs=assemble_step_logs(failed_steps, step_map),
                log_error=log_error,
                annotation_error=annotation_error,
            )
        )
    return docs


def subject_from_run(run: dict, label: str) -> Subject:
    workflow = str(run.get("workflowName") or run.get("name") or "")
    title = f"GitHub Actions 失敗 INDEX: {workflow}"
    lines = [
        f"対象: run {run.get('databaseId')}",
        f"workflow: {workflow}",
        f"タイトル: {run.get('displayTitle') or ''}",
        f"URL: {run.get('url') or ''}",
        f"event: {run.get('event') or ''}",
        f"branch: {run.get('headBranch') or ''}",
        f"head: {run.get('headSha') or ''}",
        f"run conclusion: {normalize_conclusion(run.get('conclusion')) or run.get('status') or ''}",
    ]
    return Subject(title=title, label=label, lines=lines)


def subject_from_pr(pr: dict, repo: str) -> Subject:
    number = pr.get("number")
    title = f"GitHub Actions 失敗 INDEX: PR #{number}"
    lines = [
        f"対象: PR #{number} {pr.get('title') or ''}".rstrip(),
        f"URL: {pr.get('url') or ''}",
        f"リポジトリ: {repo}",
        f"branch: {pr.get('headRefName') or ''}",
        f"head: {pr.get('headRefOid') or ''}",
    ]
    return Subject(title=title, label=f"pr{number}", lines=lines)


def notes_from_rollup(summary: RollupSummary) -> ReportNotes:
    return ReportNotes(
        cancelled=list(summary.cancelled),
        external_failures=list(summary.external_failures),
        pending=list(summary.pending),
        success_count=summary.success_count,
        skipped_count=summary.skipped_count,
    )


def group_checks(
    checks: list[ParsedCheck],
) -> tuple[dict[tuple[str, str, str | None], list[str | None]], list[ParsedCheck]]:
    grouped: dict[tuple[str, str, str | None], list[str | None]] = {}
    unresolved: list[ParsedCheck] = []
    for check in checks:
        if not check.repo:
            unresolved.append(check)
            continue
        if check.run_id:
            key = (check.repo, check.run_id, check.attempt)
            grouped.setdefault(key, []).append(check.job_id)
            continue
        unresolved.append(check)
    return grouped, unresolved


def collect_run_target(
    client: GhClient, target: Target
) -> tuple[Subject, list[JobDocument], ReportNotes]:
    repo = target.repo or client.current_repo()
    run_id = target.run_id
    attempt = target.attempt
    if target.kind == "job" and target.job_id and not run_id:
        job = client.actions_job(repo, target.job_id)
        run_id = str(job["run_id"])
    if not run_id:
        raise RuntimeError("run id を特定できませんでした。Actions の URL を指定してください。")
    run = client.view_run(repo, run_id, attempt)
    only_job_ids = [target.job_id] if target.job_id else None
    docs = documents_for_run(client, repo, run, only_job_ids)
    label = f"job{target.job_id}" if target.job_id else f"run{run_id}"
    notes = notes_for_other_jobs(run.get("jobs") or [], {doc.job_id for doc in docs})
    if target.pr_number:
        notes_lines = subject_from_run(run, label).lines
        notes_lines.insert(0, f"PR: #{target.pr_number}")
        subject = Subject(
            title=f"GitHub Actions 失敗 INDEX: PR #{target.pr_number}",
            label=label,
            lines=notes_lines,
        )
    else:
        subject = subject_from_run(run, label)
    return subject, docs, notes


def collect_pr_target(
    client: GhClient, target: Target
) -> tuple[Subject, list[JobDocument], ReportNotes]:
    repo = target.repo or client.current_repo()
    pr = client.view_pr(target.pr_number, target.repo)
    summary = classify_rollup(pr.get("statusCheckRollup") or [])
    grouped, unresolved = group_checks(summary.failed_actions)
    docs: list[JobDocument] = []
    for (check_repo, run_id, attempt), job_ids in grouped.items():
        run = client.view_run(check_repo, run_id, attempt)
        only_job_ids = [job_id for job_id in job_ids if job_id]
        if len(only_job_ids) != len(job_ids):
            only_job_ids_arg = None
        else:
            only_job_ids_arg = only_job_ids
        run_docs = documents_for_run(
            client,
            check_repo,
            run,
            only_job_ids_arg,
        )
        docs.extend(run_docs)
    for check in unresolved:
        if not check.repo or not check.job_id:
            summary.external_failures.append(display_check(check.name, check.workflow, check.url))
            continue
        job = client.actions_job(check.repo, check.job_id)
        run = client.view_run(check.repo, str(job["run_id"]), check.attempt)
        run_docs = documents_for_run(
            client,
            check.repo,
            run,
            [check.job_id],
        )
        docs.extend(run_docs)
    deduped: list[JobDocument] = []
    seen: set[str] = set()
    for doc in docs:
        if doc.job_id in seen:
            continue
        seen.add(doc.job_id)
        deduped.append(doc)
    return subject_from_pr(pr, repo), deduped, notes_from_rollup(summary)


def collect(client: GhClient, target: Target) -> tuple[Subject, list[JobDocument], ReportNotes]:
    if target.kind == "pr":
        return collect_pr_target(client, target)
    return collect_run_target(client, target)


def build_output_dir(base_dir: Path, label: str, override: str | None) -> Path:
    if override:
        return Path(override)
    return base_dir / "temp" / "actions" / f"{int(time.time())}_{label}"


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="ActionsのURL、PRのURL、PR番号(123 / #123)、run:ID。省略時はカレントブランチのPR",
    )
    parser.add_argument(
        "--gh-repo",
        default=None,
        help="OWNER/REPO。URLにリポジトリが含まれる場合は不要",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="gh を実行するディレクトリ（出力先の基準）。省略時はカレントディレクトリ",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="出力先。省略時は temp/actions/<timestamp>_<label>/",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    reconfigure_stdout()
    args = parse_args(argv)
    ensure_gh_available()
    base_dir = find_base_dir(Path(args.repo))
    target = with_repo(parse_target(args.target), args.gh_repo)
    client = GhClient(base_dir)
    try:
        subject, docs, notes = collect(client, target)
        output_dir = build_output_dir(base_dir, subject.label, args.output_dir)
        index_path, written = write_report(output_dir, subject, docs, notes)
    except RuntimeError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"エラー: gh のJSONを解釈できませんでした: {exc}", file=sys.stderr)
        return 1
    emit_summary(index_path, written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
