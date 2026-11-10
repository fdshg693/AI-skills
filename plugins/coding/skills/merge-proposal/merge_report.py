#!/usr/bin/env python3
"""現在のブランチに別ブランチを取り込む(マージする)と仮定し、
コンフリクト一覧と取り込み内容の差分を2ファイルに出力する。

読み取り専用: git merge-tree --write-tree / diff / show / log / merge-base /
rev-parse / status のみを使用し、checkout・merge・commit・push・stash など
ブランチ・インデックス・作業ツリーを変更する操作は一切行わない。
(merge-tree はマージ結果のblob/treeをオブジェクトDBに書き込むが、どのrefからも
参照されない一時オブジェクトであり、git gc で回収される。)

使い方:
    python merge_report.py <incoming-branch> [--current BRANCH] [--repo REPO] [--output-dir DIR]

出力(temp/merge/<timestamp>_<hash(current,incoming)>/ 配下):
    - CONFLICTS.md: コンフリクトするファイルごとに、種別・両側の変更(merge-base からの
      diff)・コンフリクト箇所(zdiff3形式のマーカー付き、マージ結果ファイルの行番号付き)
    - INCOMING.md: 取り込まれるコミット一覧、現在のブランチ側の変更ファイル一覧、
      取り込み側の変更ファイルごとの差分(両側変更/コンフリクトのフラグ付き)
    どちらも冒頭のサマリ表に各セクションの開始行番号を載せるので、
    大きい場合は Read の offset で必要なセクションだけを読める。
    標準出力には2ファイルのパスと件数サマリのみを出す。

依存関係:
    git 2.38 以上(merge-tree --write-tree)。
    同階層の .diffignore(.gitignore と同じ書式)にマッチするパスは INCOMING.md の
    差分本文から除外する(コンフリクトは解消が必須なので CONFLICTS.md からは除外しない)。
    実パターンがある場合のみ `pathspec` パッケージが必要。
"""

import argparse
import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    import pathspec
except ImportError:
    pathspec = None

DIFFIGNORE_FILENAME = ".diffignore"
CONFLICT_CONTEXT_LINES = 3
CONFLICT_START = re.compile(r"^<{7}( |$)")
CONFLICT_END = re.compile(r"^>{7}( |$)")


def run_git(repo_root, args, check=True, config=()):
    cmd = ["git", "-C", str(repo_root)]
    for item in config:
        cmd += ["-c", item]
    result = subprocess.run(
        [*cmd, *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
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


def resolve_branch(repo_root, name, label):
    for candidate in (name, f"origin/{name}"):
        result = run_git(repo_root, ["rev-parse", "--verify", "--quiet", candidate], check=False)
        if result.returncode == 0:
            return candidate, result.stdout.strip()
    raise SystemExit(
        f"エラー: {label} '{name}' が見つかりません（ローカル・origin/{name} のどちらにも存在しません）。"
    )


def load_diffignore_spec(script_dir):
    path = script_dir / DIFFIGNORE_FILENAME
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    if not any(line.strip() and not line.lstrip().startswith("#") for line in lines):
        return None
    if pathspec is None:
        raise SystemExit(
            f"エラー: {path} にパターンがありますが、pathspec パッケージが見つかりません。"
            "`pip install pathspec` でインストールしてください。"
        )
    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def is_ignored(spec, *paths):
    return spec is not None and any(spec.match_file(p) for p in paths)


def parse_name_status(output):
    entries = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status[0] in "RC":
            entries.append((status, parts[1], parts[2]))
        else:
            entries.append((status, parts[1], parts[1]))
    return entries


def parse_numstat(output):
    """{new_path: (added, deleted)}。バイナリは ('-', '-')。"""
    stats = {}
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        path = parts[-1]
        if " => " in path:
            # "dir/{old => new}/f" / "old => new" 形式は新パスへ正規化する
            path = re.sub(r"\{[^{}]* => ([^{}]*)\}", r"\1", path)
            path = path.split(" => ")[-1].replace("//", "/")
        stats[path] = (parts[0], parts[1])
    return stats


def changed_files(repo_root, base, ref):
    rng = f"{base}..{ref}"
    entries = parse_name_status(run_git(repo_root, ["diff", "-M", "--name-status", rng]).stdout)
    stats = parse_numstat(run_git(repo_root, ["diff", "-M", "--numstat", rng]).stdout)
    entries.sort(key=lambda e: e[2])
    return entries, stats


def display_path(old_path, new_path):
    return new_path if old_path == new_path else f"{old_path} -> {new_path}"


def run_merge_tree(repo_root, current_ref, incoming_ref):
    """(tree_oid, {path: {stage: oid}}, [(paths, type, message)]) を返す。"""
    result = run_git(
        repo_root,
        ["merge-tree", "--write-tree", "-z", "--messages", current_ref, incoming_ref],
        check=False,
        config=("merge.conflictStyle=zdiff3",),
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"git merge-tree failed:\n{result.stderr.strip()}")

    fields = result.stdout.split("\0")
    tree_oid = fields[0]
    i = 1
    stages = {}
    while i < len(fields) and fields[i] != "":
        meta, path = fields[i].split("\t", 1)
        _mode, oid, stage = meta.split(" ")
        stages.setdefault(path, {})[int(stage)] = oid
        i += 1
    i += 1  # 空フィールド(区切り)

    messages = []
    while i < len(fields) and fields[i] != "":
        count = int(fields[i])
        paths = fields[i + 1 : i + 1 + count]
        ctype = fields[i + 1 + count]
        message = fields[i + 2 + count].strip()
        messages.append((paths, ctype, message))
        i += 3 + count
    return tree_oid, stages, messages


def show_blob(repo_root, spec):
    result = run_git(repo_root, ["show", spec], check=False)
    return result.stdout if result.returncode == 0 else None


def extract_conflict_hunks(text):
    """マーカー付きテキストから [(start_line, end_line, numbered_lines)] を返す(1始まり)。"""
    lines = text.splitlines()
    hunks = []
    i = 0
    while i < len(lines):
        if not CONFLICT_START.match(lines[i]):
            i += 1
            continue
        start = i
        end = start
        while end < len(lines) and not CONFLICT_END.match(lines[end]):
            end += 1
        end = min(end, len(lines) - 1)
        lo = max(0, start - CONFLICT_CONTEXT_LINES)
        hi = min(len(lines) - 1, end + CONFLICT_CONTEXT_LINES)
        width = len(str(hi + 1))
        numbered = [f"{n + 1:>{width}}: {lines[n]}" for n in range(lo, hi + 1)]
        hunks.append((start + 1, end + 1, numbered))
        i = end + 1
    return hunks


def fenced(lang, body):
    body = body.rstrip("\n")
    fence = "```"
    while fence in body:
        fence += "`"
    return [f"{fence}{lang}", *body.splitlines(), fence]


def file_diff(repo_root, base, ref, path):
    body = run_git(repo_root, ["diff", "-M", base, ref, "--", path], check=False).stdout
    return body if body.strip() else "(差分なし)\n"


def _rstrip_blank(lines):
    lines = list(lines)
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def assemble(title_lines, summary_builder, sections):
    """sections: [(key, lines)]。summary_builder(start_line_by_key) -> lines。
    サマリ表の行数は行番号の値に依存しないので、1度組んで長さを測ってから確定させる。"""
    sections = [(key, _rstrip_blank(lines)) for key, lines in sections]
    placeholder = summary_builder({key: 0 for key, _ in sections})
    # 各セクションの前に空行を1つ挟む。行番号は1始まり
    offset = len(title_lines) + len(placeholder) + 2
    starts = {}
    for key, lines in sections:
        starts[key] = offset
        offset += len(lines) + 1
    out = [*title_lines, *summary_builder(starts)]
    for _key, lines in sections:
        out.append("")
        out.extend(lines)
    return "\n".join(out) + "\n"


def build_conflicts_md(ctx, conflicts):
    title = [
        f"# コンフリクト一覧: {ctx['incoming_ref']} -> {ctx['current_ref']}",
        "",
        *ctx["meta_lines"],
        f"- コンフリクトファイル数: {len(conflicts)}",
        "- コンフリクト箇所は zdiff3 形式: `<<<<<<< 現在のブランチ` / `||||||| merge-base` / "
        "`=======` / `>>>>>>> 取り込むブランチ`",
        "",
    ]
    if not conflicts:
        return "\n".join([*title, "コンフリクトはありません。"]) + "\n"

    sections = []
    for n, c in enumerate(conflicts, start=1):
        lines = [f"## [{n}/{len(conflicts)}] {c['path']}", ""]
        lines.append(f"- 種別: {', '.join(c['types'])}")
        for message in c["messages"]:
            lines.append(f"- git: {message}")
        lines.append(f"- 存在するステージ: {c['stage_desc']}")
        lines += ["", "### 現在のブランチ側の変更 (merge-base → 現在)", ""]
        lines += fenced("diff", c["ours_diff"])
        lines += ["", "### 取り込み側の変更 (merge-base → 取り込み)", ""]
        lines += fenced("diff", c["theirs_diff"])
        lines += ["", "### コンフリクト箇所 (マージ結果ファイルの行番号)", ""]
        if c["hunks"]:
            for h, (start, end, numbered) in enumerate(c["hunks"], start=1):
                lines += [f"#### ハンク {h} (L{start}-L{end})", ""]
                lines += fenced("text", "\n".join(numbered))
                lines.append("")
        else:
            lines += ["(テキストのマーカー無し。種別を見て、どちらの版を残すかを判断する)", ""]
        sections.append((c["path"], lines))

    def summary(starts):
        rows = ["## サマリ", "", "| # | path | 種別 | ハンク数 | 開始行 |", "|---|---|---|---|---|"]
        for n, c in enumerate(conflicts, start=1):
            rows.append(
                f"| {n} | {c['path']} | {', '.join(c['types'])} | {len(c['hunks'])} | "
                f"{starts[c['path']]} |"
            )
        return rows

    return assemble(title, summary, sections)


def build_incoming_md(ctx, commits, ours_entries, ours_stats, entries, ignored):
    title = [
        f"# 取り込み内容: {ctx['incoming_ref']} -> {ctx['current_ref']}",
        "",
        *ctx["meta_lines"],
        f"- 取り込み側の変更ファイル数: {len(entries)}",
    ]
    if ignored:
        title.append(f"- .diffignore により差分本文を省略: {len(ignored)}件 ({', '.join(ignored)})")
    title += ["", f"## 取り込まれるコミット ({len(commits)}件、古い順)", ""]
    title += [f"- {c}" for c in commits] or ["(なし)"]
    title += [
        "",
        f"## 現在のブランチ側の変更ファイル (merge-base → 現在、{len(ours_entries)}件)",
        "",
    ]
    if ours_entries:
        title += ["| status | path | + | - |", "|---|---|---|---|"]
        for status, old, new in ours_entries:
            add, dele = ours_stats.get(new, ("?", "?"))
            title.append(f"| {status} | {display_path(old, new)} | {add} | {dele} |")
    else:
        title.append("(なし)")
    title.append("")

    sections = []
    for n, e in enumerate(entries, start=1):
        lines = [f"## [{n}/{len(entries)}] {e['display']}", ""]
        lines.append(
            f"- status: {e['status']} / +{e['add']} -{e['del']} / "
            f"現在のブランチでも変更: {'あり' if e['both'] else 'なし'} / "
            f"コンフリクト: {'あり' if e['conflict'] else 'なし'}"
        )
        lines.append("")
        lines += fenced("diff", e["diff"])
        sections.append((e["display"], lines))

    def summary(starts):
        rows = [
            "## 取り込み側の変更ファイル (merge-base → 取り込み)",
            "",
            "両側変更=現在のブランチでも同じファイルを変更している(自動マージされても意味的な衝突に注意)",
            "",
            "| # | status | path | + | - | 両側変更 | コンフリクト | 開始行 |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for n, e in enumerate(entries, start=1):
            rows.append(
                f"| {n} | {e['status']} | {e['display']} | {e['add']} | {e['del']} | "
                f"{'●' if e['both'] else ''} | {'●' if e['conflict'] else ''} | "
                f"{starts[e['display']]} |"
            )
        return rows

    if not entries:
        return "\n".join([*title, "取り込み側に変更ファイルはありません。"]) + "\n"
    return assemble(title, summary, sections)


STAGE_NAMES = {1: "merge-base", 2: "現在", 3: "取り込み"}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("incoming", help="現在のブランチに取り込むブランチ名 (例: main)")
    parser.add_argument(
        "--current", default=None, help="取り込み先ブランチ名。省略時は現在のブランチ(HEAD)"
    )
    parser.add_argument("--repo", default=".", help="対象リポジトリのパス")
    parser.add_argument(
        "--output-dir", default=None, help="出力先。省略時は temp/merge/<timestamp>_<hash>/"
    )
    args = parser.parse_args()

    repo_root = find_repo_root(Path(args.repo))

    current = args.current
    if current is None:
        current = run_git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
        if current == "HEAD":
            raise SystemExit(
                "エラー: detached HEAD のため現在のブランチを特定できません。--current で指定してください。"
            )
    current_ref, current_sha = resolve_branch(repo_root, current, "取り込み先ブランチ")
    incoming_ref, incoming_sha = resolve_branch(repo_root, args.incoming, "取り込むブランチ")

    if current_sha == incoming_sha:
        print(f"{current_ref} と {incoming_ref} は同じコミットです。取り込む内容はありません。")
        return

    mb = run_git(repo_root, ["merge-base", current_ref, incoming_ref], check=False)
    if mb.returncode != 0:
        raise SystemExit(
            f"エラー: {current_ref} と {incoming_ref} の共通の祖先が見つかりません（履歴が無関係な可能性があります）。"
        )
    base = mb.stdout.strip()
    if base == incoming_sha:
        print(
            f"{incoming_ref} は既に {current_ref} に取り込まれています。取り込む内容はありません。"
        )
        return

    dirty = run_git(repo_root, ["status", "--porcelain"]).stdout.strip() != ""
    fast_forward = base == current_sha

    tree, stages, messages = run_merge_tree(repo_root, current_ref, incoming_ref)

    # --- コンフリクト ---
    conflict_messages = {}
    for paths, ctype, message in messages:
        if not ctype.startswith("CONFLICT"):
            continue
        for p in paths:
            conflict_messages.setdefault(p, []).append((ctype, message))
    conflict_paths = sorted(set(stages) | set(conflict_messages))

    conflicts = []
    for path in conflict_paths:
        st = stages.get(path, {})
        merged = show_blob(repo_root, f"{tree}:{path}")
        hunks = extract_conflict_hunks(merged) if merged else []
        types = sorted(
            {t.replace("CONFLICT ", "").strip("()") for t, _ in conflict_messages.get(path, [])}
        )
        conflicts.append(
            {
                "path": path,
                "types": types or ["unknown"],
                "messages": [m for _, m in conflict_messages.get(path, [])],
                "stage_desc": ", ".join(STAGE_NAMES[s] for s in sorted(st)) or "-",
                "ours_diff": file_diff(repo_root, base, current_sha, path),
                "theirs_diff": file_diff(repo_root, base, incoming_sha, path),
                "hunks": hunks,
            }
        )

    # --- 取り込み内容 ---
    ours_entries, ours_stats = changed_files(repo_root, base, current_sha)
    ours_paths = {p for _, old, new in ours_entries for p in (old, new)}
    theirs_entries, theirs_stats = changed_files(repo_root, base, incoming_sha)

    spec = load_diffignore_spec(Path(__file__).resolve().parent)
    entries = []
    ignored = []
    for status, old, new in theirs_entries:
        disp = display_path(old, new)
        add, dele = theirs_stats.get(new, ("?", "?"))
        if is_ignored(spec, old, new):
            ignored.append(disp)
            diff = "(.diffignore により省略)\n"
        elif add == "-":
            diff = "(バイナリファイルのため差分は省略)\n"
        else:
            diff = (
                run_git(
                    repo_root, ["diff", "-M", base, incoming_sha, "--", *{old, new}], check=False
                ).stdout
                or "(差分なし)\n"
            )
        entries.append(
            {
                "status": status,
                "display": disp,
                "add": add,
                "del": dele,
                "both": old in ours_paths or new in ours_paths,
                "conflict": old in conflict_paths or new in conflict_paths,
                "diff": diff,
            }
        )

    commits = run_git(
        repo_root,
        [
            "log",
            "--reverse",
            "--format=%h %s (%an, %ad)",
            "--date=short",
            f"{base}..{incoming_sha}",
        ],
    ).stdout.splitlines()

    meta_lines = [
        f"- 現在のブランチ(取り込み先): {current_ref} ({current_sha[:12]})",
        f"- 取り込むブランチ: {incoming_ref} ({incoming_sha[:12]})",
        f"- merge-base: {base[:12]}",
        f"- fast-forward 可能: {'はい' if fast_forward else 'いいえ'}",
        "- 作業ツリーの未コミット変更: "
        + ("あり(この結果はコミット済みの状態のみを対象にしている)" if dirty else "なし"),
    ]
    ctx = {"current_ref": current_ref, "incoming_ref": incoming_ref, "meta_lines": meta_lines}

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        digest = hashlib.sha1(f"{current_ref}|{incoming_ref}".encode("utf-8")).hexdigest()[:8]
        output_dir = repo_root / "temp" / "merge" / f"{int(time.time())}_{digest}"
    output_dir.mkdir(parents=True, exist_ok=True)

    conflicts_path = output_dir / "CONFLICTS.md"
    incoming_path = output_dir / "INCOMING.md"
    conflicts_path.write_text(build_conflicts_md(ctx, conflicts), encoding="utf-8")
    incoming_path.write_text(
        build_incoming_md(ctx, commits, ours_entries, ours_stats, entries, ignored),
        encoding="utf-8",
    )

    both = sum(1 for e in entries if e["both"])
    print(f"# マージ提案用レポート: {incoming_ref} -> {current_ref}")
    print(f"出力先: {output_dir}")
    print(f"CONFLICTS.md: {conflicts_path} (コンフリクト {len(conflicts)}件)")
    print(
        f"INCOMING.md: {incoming_path} (取り込みコミット {len(commits)}件 / 変更ファイル "
        f"{len(entries)}件 / うち両側変更 {both}件)"
    )
    if ignored:
        print(f".diffignore により差分本文を省略: {len(ignored)}件")
    if dirty:
        print("注意: 作業ツリーに未コミット変更があります(レポートはコミット済みの状態が対象)。")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
