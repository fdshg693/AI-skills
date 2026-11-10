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
            "`pip install pathspec` でグローバルにインストールしてください。"
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
    return {
        "status": status,
        "old_path": old_path,
        "new_path": new_path,
        "display_path": display_path,
        "original_lines": original_lines,
        "new_lines": new_lines,
        "line_labels": line_labels,
        "block_text": block_text,
        "block_lines": count_lines(block_text),
    }


def build_chunks(entries, max_lines=MAX_LINES_PER_CHUNK):
    chunks = []
    current = []
    current_lines = 0
    for entry in entries:
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


def build_index_md(
    chunk_paths, chunks, title, meta_lines, output_dir, total_entries, ignored_paths=()
):
    """title: INDEX.md の見出し。meta_lines: merge-base 等、レビュー種別固有の追加行(文字列のリスト)。"""
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
    lines.append("\n")
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
        lines.append(f"| {i} | {chunk_path.name} | {path_range} | {len(chunk)} | {total_lines} |\n")

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
            lines.append(
                f"| {entry['status']} | {entry['display_path']} | "
                f"{entry['original_lines']} | {entry['new_lines']} |\n"
            )
        lines.append("\n")

    if ignored_paths:
        lines.append("## .diffignore により除外されたファイル\n\n")
        for path in ignored_paths:
            lines.append(f"- {path}\n")
        lines.append("\n")

    return "".join(lines)
