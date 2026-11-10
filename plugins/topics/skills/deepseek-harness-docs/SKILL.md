---
name: deepseek-harness-docs
description: Use when answering questions about DeepSeek Harness (`dsh`) - its Web UI, CLI profiles, Python SDK, model providers, permissions, sessions, plugins, Cordis APIs, tools, or architecture. Grounds answers in the current English-only official documentation at deepseek-harness.github.io instead of training-data memory, which may be stale.
allowed-tools: Bash(uv run --with requests --with typer python ${CLAUDE_SKILL_DIR}/*.py *)
# The bundled downloader refreshes the English-only index at skill startup.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: requests, typer
  requires_install: none
  requires_hooks: none
  requires_skills: none
  status: stable
  description: Official English DeepSeek Harness documentation index
  version: 1.0.0
---

!`uv run --with requests --with typer python "${CLAUDE_SKILL_DIR}/webref_cli.py" download`

# DeepSeek Harness Official Documentation

Use the current English DeepSeek Harness documentation as the source of truth for `dsh`, its Web UI, SDKs, plugin system, Cordis framework, and runtime architecture. Do not answer from the Chinese documentation or from stale training-data knowledge.

## English-Only Index

`${CLAUDE_SKILL_DIR}/output/llms.en.txt` is a freshness-checked snapshot of **only** the `## English` section from the official `llms.txt`.

- The upstream `llms.txt` also contains `## 简体中文`. The downloader verifies that exactly one `## English` heading exists and writes from that heading until the next level-two heading, so Chinese entries cannot enter this index.
- It is an index of canonical page URLs and brief categories, not a full-text dump. `llms-full.txt` does not exist.
- The source uses raw Markdown URLs ending in `.md`. Its links are root-relative, so prepend `https://deepseek-harness.github.io` when fetching the page body.

## Procedure

1. Search `${CLAUDE_SKILL_DIR}/output/llms.en.txt` with Grep for the question's feature, API, or subsystem. Read nearby lines to identify the smallest relevant set of English page URLs.
2. Fetch only those official `.md` URLs with WebFetch when the index is insufficient. Prepend `https://deepseek-harness.github.io` to the root-relative URL, and do not infer or fetch the corresponding path without `/en/`.
3. Answer from the fetched English page content and cite its canonical `https://deepseek-harness.github.io/deepseek-harness/en/...` URL. Keep distinct concepts separate, especially profiles versus bundles, durable session events versus live agent events, and plugins versus the Cordis framework.

## Reference Areas

- `guide/`: Web UI, models/providers, network proxy, Python SDK, GitHub review sessions, reminders, and Memory MCP.
- `develop/`: plugin basics, tools, configuration, services, events, LLM adapters, and the Cordis tutorial.
- `reference/`: architecture, lifecycle, execution pipeline, generated catalogues, Cordis APIs, subsystem behaviour, permissions, and client/server components.

## Refreshing

The startup download skips a snapshot fetched within 24 hours. To refresh it explicitly, run:

```sh
uv run --with requests --with typer python "${CLAUDE_SKILL_DIR}/webref_cli.py" download --force
```
