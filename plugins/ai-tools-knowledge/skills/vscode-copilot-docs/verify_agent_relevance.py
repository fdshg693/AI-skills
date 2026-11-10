#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""Ask an AI model (via the `aim` CLI) whether the curation scope of copilot-excerpt.md
looks right -- not just whether its titles/URLs still match the source, which is all
check_copilot_excerpt.py can tell you.

This is a 3-step verification:

  1. Run check_copilot_excerpt.py. If it reports drift (MISSING/TITLE MISMATCH),
     abort -- fix output/copilot-excerpt.md first, since the steps below assume the
     excerpt's URLs are already trustworthy.
  2. Run extract_uncurated_entries.py to get every source entry not in the excerpt,
     split by keyword heuristic into "agent candidates" and "non candidates".
  3. Call the `aim` CLI once per list (3 calls total), asking the model for a
     natural-language second opinion:
       - on copilot-excerpt.md itself: does every already-curated entry actually
         belong (catches entries that were miscurated in)?
       - on the agent-candidate list: which entries are likely false positives
         (matched a keyword like "ai"/"chat"/"agent" but aren't actually about
         GitHub Copilot / AI agents in VS Code)?
       - on the non-candidate list: which entries, if any, look like false
         negatives (actually Copilot/AI-agent related despite missing the
         keyword heuristic)?

The prompt for each call lives in its own markdown file next to this script
(prompt_excerpt.md, prompt_agent_candidates.md, prompt_non_candidates.md) since
prompt wording tends to change independently of the driver logic. Each model
response is written to its own output file. This script's scope ends at producing
those files -- a human reads them and decides whether to edit
output/copilot-excerpt.md. It does not modify copilot-excerpt.md or SKILL.md itself.

This script does not import check_copilot_excerpt.py directly, but it invokes it (and
extract_uncurated_entries.py) as subprocesses using the *same* interpreter that ran
this script (sys.executable) -- so this script also depends on PyYAML being available
in that interpreter. Run it via `uv run verify_agent_relevance.py`, not bare `python`.

Usage: uv run verify_agent_relevance.py [--model {mini-m3,gpt-120b,glm-5.2,gpt-luna}] [--verify-dir PATH]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
DEFAULT_VERIFY_DIR = SKILL_DIR / "output" / "verification"
DEFAULT_EXCERPT = SKILL_DIR / "output" / "copilot-excerpt.md"

PROMPT_EXCERPT = SKILL_DIR / "prompts" / "prompt_excerpt.md"
PROMPT_AGENT_CANDIDATES = SKILL_DIR / "prompts" / "prompt_agent_candidates.md"
PROMPT_NON_CANDIDATES = SKILL_DIR / "prompts" / "prompt_non_candidates.md"


def run_subprocess(args: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    return result


def call_aim(model: str, prompt: str, entries_text: str) -> str:
    full_prompt = f"{prompt}\n---\n\n{entries_text}"
    result = subprocess.run(
        ["aim", "--model", model],
        input=full_prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(f"aim CLI failed (exit {result.returncode}): {result.stderr.strip()}")
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default="mini-m3",
        choices=["mini-m3", "gpt-120b", "glm-5.2", "gpt-luna"],
    )
    parser.add_argument("--excerpt", type=Path, default=DEFAULT_EXCERPT)
    parser.add_argument("--verify-dir", type=Path, default=DEFAULT_VERIFY_DIR)
    args = parser.parse_args()

    print("Step 1/3: running check_copilot_excerpt.py ...")
    check_result = run_subprocess([sys.executable, str(SKILL_DIR / "check_copilot_excerpt.py")])
    if check_result.returncode != 0:
        print(
            "ERROR: check_copilot_excerpt.py reported drift (MISSING/TITLE MISMATCH). "
            "Fix output/copilot-excerpt.md first, then re-run this script.",
            file=sys.stderr,
        )
        return 2

    print("\nStep 2/3: extracting uncurated entries ...")
    extract_result = run_subprocess(
        [
            sys.executable,
            str(SKILL_DIR / "extract_uncurated_entries.py"),
            "--out-dir",
            str(args.verify_dir),
        ]
    )
    if extract_result.returncode != 0:
        print("ERROR: extract_uncurated_entries.py failed.", file=sys.stderr)
        return 2

    candidates_path = args.verify_dir / "uncurated_agent_candidates.md"
    non_candidates_path = args.verify_dir / "uncurated_non_candidates.md"

    print(f"\nStep 3/3: asking {args.model} to judge relevance (3 calls) ...")
    jobs = [
        (args.excerpt, PROMPT_EXCERPT, args.verify_dir / "llm_judgement_excerpt.md"),
        (
            candidates_path,
            PROMPT_AGENT_CANDIDATES,
            args.verify_dir / "llm_judgement_agent_candidates.md",
        ),
        (
            non_candidates_path,
            PROMPT_NON_CANDIDATES,
            args.verify_dir / "llm_judgement_non_candidates.md",
        ),
    ]
    for source_path, prompt_path, out_path in jobs:
        if not source_path.is_file():
            print(f"ERROR: {source_path} not found", file=sys.stderr)
            return 2
        if not prompt_path.is_file():
            print(f"ERROR: prompt file not found: {prompt_path}", file=sys.stderr)
            return 2
        prompt = prompt_path.read_text(encoding="utf-8")
        entries_text = source_path.read_text(encoding="utf-8")
        print(
            f"  calling aim --model {args.model} for {source_path.name} (prompt: {prompt_path.name}) ..."
        )
        try:
            judgement = call_aim(args.model, prompt, entries_text)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        args.verify_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_text(judgement, encoding="utf-8")
        print(f"    -> {out_path}")

    print(
        "\nDone. A human should read the llm_judgement_*.md files in "
        f"{args.verify_dir} and update output/copilot-excerpt.md accordingly "
        "(this script does not modify it)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
