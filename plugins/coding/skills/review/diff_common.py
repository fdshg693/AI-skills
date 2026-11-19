"""review スキルの各差分レポートスクリプトが共有するヘルパー。

diff_report.py（ブランチ間差分）と uncommitted_report.py（未コミット変更）の
両方から import される。gitラッパー・行数カウント・.diffignore フィルタ・
チャンク分割・INDEX.md 生成など、レビュー種別に依存しない処理のみを置く。
"""

import subprocess
from pathlib import Path

try:
    import pathspec
except ImportError:
    pathspec = None

MAX_LINES_PER_CHUNK = 300
# 1ファイルの差分ブロックがこの行数を超えたら「巨大」とみなし、単独の分割ファイルに隔離して
# INDEX.md で印を付ける（スナップショット・ロックファイル等を読まずに飛ばせるようにする）
HUGE_BLOCK_LINES = 2000
DIFFIGNORE_FILENAME = ".diffignore"


def run_git(repo_root, args, check=True):
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result


def find_repo_root(start):
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise SystemExit(
            f"エラー: {start} はGitリポジトリ内ではありません。\n{result.stderr.strip()}"
        )
    return Path(result.stdout.strip())


def count_lines(text):
    if text == "":
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def load_diffignore_spec(script_dir):
    diffignore_path = script_dir / DIFFIGNORE_FILENAME
    if not diffignore_path.exists():
        return None
    if pathspec is None:
        raise SystemExit(
            f"エラー: {diffignore_path} が存在しますが、pathspec パッケージが見つかりません。"
            "`uv run <script>` で実行すると PEP 723 のメタデータから自動で入る"
            "（uv を使わない場合は `pip install pathspec`）。"
        )
    lines = diffignore_path.read_text(encoding="utf-8").splitlines()
    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def filter_ignored_entries(entries, diffignore_spec):
    """entries は (status, old_path, new_path) のタプル列。"""
    if diffignore_spec is None:
        return entries, []
    kept = []
    ignored = []
    for status, old_path, new_path in entries:
        if diffignore_spec.match_file(new_path) or diffignore_spec.match_file(old_path):
            display_path = new_path if old_path == new_path else f"{old_path} -> {new_path}"
            ignored.append(display_path)
        else:
            kept.append((status, old_path, new_path))
    return kept, ignored


DEFAULT_LINE_LABELS = ("original_lines", "new_lines")


def build_block_meta(
    status,
    old_path,
    new_path,
    original_lines,
    new_lines,
    diff_body,
    line_labels=DEFAULT_LINE_LABELS,
):
    """line_labels: 2つの数値列の見出し。PRレビューでは ("additions", "deletions") を渡す。"""
    display_path = new_path if old_path == new_path else f"{old_path} -> {new_path}"
    header = (
        f"# path: {display_path}\n"
        f"# status: {status}\n"
        f"# {line_labels[0]}: {original_lines}\n"
        f"# {line_labels[1]}: {new_lines}\n\n"
    )
    block_text = header + diff_body
    block_lines = count_lines(block_text)
    return {
        "status": status,
        "old_path": old_path,
        "new_path": new_path,
        "display_path": display_path,
        "original_lines": original_lines,
        "new_lines": new_lines,
        "line_labels": line_labels,
        "block_text": block_text,
        "block_lines": block_lines,
        "huge": block_lines > HUGE_BLOCK_LINES,
    }


def build_chunks(entries, max_lines=MAX_LINES_PER_CHUNK):
    """巨大なブロック(HUGE_BLOCK_LINES超)は前後と混ぜず、単独の分割ファイルにする。"""
    chunks = []
    current = []
    current_lines = 0
    for entry in entries:
        if entry.get("huge"):
            if current:
                chunks.append(current)
                current = []
                current_lines = 0
            chunks.append([entry])
            continue
        current.append(entry)
        current_lines += entry["block_lines"]
        if current_lines > max_lines:
            chunks.append(current)
            current = []
            current_lines = 0
    if current:
        chunks.append(current)
    return chunks


def write_chunk_files(output_dir, chunks):
    width = max(4, len(str(len(chunks))))
    chunk_paths = []
    for i, chunk in enumerate(chunks, start=1):
        filename = f"diff_{i:0{width}d}.diff"
        path = output_dir / filename
        content = "\n".join(entry["block_text"] for entry in chunk)
        path.write_text(content, encoding="utf-8")
        chunk_paths.append(path)
    return chunk_paths


def huge_label(entry):
    return f"⚠ 巨大（{entry['block_lines']}行）" if entry.get("huge") else ""


def build_index_md(
    chunk_paths,
    chunks,
    title,
    meta_lines,
    output_dir,
    total_entries,
    ignored_paths=(),
    extra_sections=(),
):
    """title: INDEX.md の見出し。meta_lines: merge-base 等、レビュー種別固有の追加行(文字列のリスト)。
    extra_sections: (見出し, 本文) のタプル列。分割ファイル一覧の前に出す(サブモジュールの変更など)。"""
    lines = [f"# {title}\n\n"]
    lines += [f"- {line}\n" for line in meta_lines]
    lines.append(f"- 出力先: {output_dir}\n")
    lines.append(f"- 対象ファイル数: {total_entries}\n")
    lines.append(
        f"- 分割ファイル数: {len(chunks)}"
        f"（1ファイルあたり最大{MAX_LINES_PER_CHUNK}行を目安に分割。"
        f"1つの変更ファイルの差分が複数ファイルにまたがることはない）\n"
    )
    if ignored_paths:
        lines.append(f"- .diffignore により除外: {len(ignored_paths)}件\n")
    huge_entries = [e for chunk in chunks for e in chunk if e.get("huge")]
    if huge_entries:
        lines.append(
            f"- 巨大な差分（{HUGE_BLOCK_LINES}行超）: {len(huge_entries)}件。"
            "単独の分割ファイルに隔離している。生成物・ロックファイルなら本文は読まずに飛ばしてよい\n"
        )
    lines.append("\n")
    for heading, body in extra_sections:
        lines.append(f"## {heading}\n\n{body.rstrip()}\n\n")
    lines += [
        "## 分割ファイル一覧\n\n",
        "| # | diff file | 含まれるパス範囲 | 収録ファイル数 | 行数(概算) |\n",
        "|---|---|---|---|---|\n",
    ]

    for i, (chunk, chunk_path) in enumerate(zip(chunks, chunk_paths), start=1):
        first_path = chunk[0]["display_path"]
        last_path = chunk[-1]["display_path"]
        path_range = first_path if first_path == last_path else f"{first_path} ～ {last_path}"
        total_lines = sum(entry["block_lines"] for entry in chunk)
        mark = f" {huge_label(chunk[0])}" if len(chunk) == 1 and chunk[0].get("huge") else ""
        lines.append(
            f"| {i} | {chunk_path.name}{mark} | {path_range} | {len(chunk)} | {total_lines} |\n"
        )

    lines.append("\n## ファイル別詳細\n\n")

    for i, (chunk, chunk_path) in enumerate(zip(chunks, chunk_paths), start=1):
        first_path = chunk[0]["display_path"]
        last_path = chunk[-1]["display_path"]
        path_range = first_path if first_path == last_path else f"{first_path} ～ {last_path}"
        lines.append(f"### {chunk_path.name}（{path_range}）\n\n")
        label_a, label_b = chunk[0]["line_labels"]
        lines.append(f"| status | path | {label_a} | {label_b} |\n")
        lines.append("|---|---|---|---|\n")
        for entry in chunk:
            mark = f" {huge_label(entry)}" if entry.get("huge") else ""
            lines.append(
                f"| {entry['status']} | {entry['display_path']}{mark} | "
                f"{entry['original_lines']} | {entry['new_lines']} |\n"
            )
        lines.append("\n")

    if ignored_paths:
        lines.append("## .diffignore により除外されたファイル\n\n")
        for path in ignored_paths:
            lines.append(f"- {path}\n")
        lines.append("\n")

    return "".join(lines)


GITLINK_MODE = "160000"


def parse_raw_gitlinks(raw_output):
    """`git diff --raw --no-abbrev` の出力から、サブモジュール(gitlink)の変更を取り出す。
    戻り値: {path: (old_sha, new_sha)}。追加・削除では片側が 0 埋めの sha になる。"""
    result = {}
    for line in raw_output.splitlines():
        meta, _, paths = line.partition("\t")
        fields = meta.lstrip(":").split()
        if len(fields) < 5:
            continue
        old_mode, new_mode, old_sha, new_sha = fields[:4]
        if GITLINK_MODE in (old_mode, new_mode):
            path = paths.split("\t")[-1]
            result[path] = (old_sha, new_sha)
    return result


def describe_submodule_change(repo_root, path, old_sha, new_sha, max_commits=50):
    """サブモジュールのポインタ変更を、コミット一覧とリモート反映状況つきで説明する。
    読み取り専用(fetch しない)。リモートの状況は手元の remote-tracking ブランチに基づく。
    戻り値: (差分ブロック本文, INDEX 用の1行要約)"""
    sub_dir = Path(repo_root) / path
    zero = set("0")
    lines = [f"Subproject commit {old_sha[:12]} -> {new_sha[:12]}\n"]
    if set(new_sha) == zero:
        return "".join(lines) + "(サブモジュールの削除)\n", f"`{path}`: 削除"
    if not (sub_dir / ".git").exists():
        lines.append("(サブモジュールが未初期化のため、中身とリモートへの反映は確認できない)\n")
        return "".join(lines), f"`{path}`: {new_sha[:7]}（未初期化で確認不可）"

    def sub_git(*args):
        return run_git(sub_dir, list(args), check=False)

    if sub_git("cat-file", "-e", f"{new_sha}^{{commit}}").returncode != 0:
        lines.append("(新しい commit が手元のサブモジュールに無い。fetch していない可能性がある)\n")
        return "".join(lines), f"`{path}`: {new_sha[:7]}（手元に無く確認不可）"

    if set(old_sha) == zero:
        log_range = [new_sha]
    else:
        log_range = [f"{old_sha}..{new_sha}"]
    log = sub_git("log", "--oneline", f"--max-count={max_commits}", *log_range).stdout
    commits = [c for c in log.splitlines() if c.strip()]
    lines.append(f"\n## サブモジュール内のコミット（最大{max_commits}件）\n")
    lines += [f"  {c}\n" for c in commits] or ["  (なし。巻き戻しの可能性がある)\n"]

    remotes = [
        r.strip() for r in sub_git("branch", "-r", "--contains", new_sha).stdout.splitlines()
    ]
    remotes = [r for r in remotes if r and "->" not in r]
    if remotes:
        status = f"リモートにあり（{', '.join(remotes[:3])}）"
    else:
        status = "⚠ リモートのどのブランチにも無い（未push の可能性。fetch していない情報に基づく）"
    lines.append(f"\n## リモートへの反映\n  {status}\n")
    lines.append(f"\n(中身の差分を見るには: git -C {path} diff {old_sha[:12]} {new_sha[:12]})\n")
    summary = f"`{path}`: {old_sha[:7]} → {new_sha[:7]}、{len(commits)} commit、{status}"
    return "".join(lines), summary
