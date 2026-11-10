# github-agentic-workflows skill

Claude Code plugin skill for authoring and operating GitHub Agentic Workflows (`gh-aw`).

## Design

- `SKILL.md` is the runtime router and security guardrail. It stays below the 500-line skill limit.
- `download_gaw_reference.py` caches the official `llms.txt` and `llms-full.txt` snapshots for 24 hours and supports `--force`.
- `extract_doc_section.py` extracts one official prompt/reference page from `llms-full.txt` after the section-marker pattern has been verified.
- `references/gaw-reference-map.md` maps common tasks to the official topic files.
- `output/` contains generated snapshots and curated material. Do not hand-edit downloaded snapshots.

The source of truth for GAW behavior is the official documentation. The local repository's `.github/aw/instructions.md`, when present, is an intentional repository-specific overlay and takes precedence over general guidance.

## Refresh and inspect

From any working directory, run:

```text
python "${CLAUDE_SKILL_DIR}/download_gaw_reference.py" --force
python "${CLAUDE_SKILL_DIR}/inspect_section_markers.py" "${CLAUDE_SKILL_DIR}/output/llms-full.txt"
```

If the marker check is consistent, extract a page by its source URL:

```text
python "${CLAUDE_SKILL_DIR}/extract_doc_section.py" https://raw.githubusercontent.com/github/gh-aw/main/.github/aw/create-agentic-workflow.md
```

Keep generated outputs out of manual patches. When an excerpt validator reports drift, update the excerpt from the current index and rerun validation rather than regenerating unrelated content.
