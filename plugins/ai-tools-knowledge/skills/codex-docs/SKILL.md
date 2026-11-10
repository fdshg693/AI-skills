---
name: codex-docs
description: Use when answering questions about Codex, including the Codex CLI, IDE extension, cloud/app, SDK, configuration, skills, plugins, MCP, subagents, sandboxing, approvals, permissions, security, pricing, and workflows. Ground answers in the latest official Codex docs from developers.openai.com/codex instead of training-data memory, which may be stale.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: requests
  requires_install: python
  requires_hooks: none
  requires_skills: none
  status: stable
  description: no description
  version: 1.0.4
---

# Codex Documentation Reference

Use this skill to answer Codex questions from current official documentation at
`developers.openai.com/codex` instead of relying on training-data memory.

## Workflow

1. **Download the official docs bundle**

   ```bash
   python skills/plugins/ai-tools-knowledge/skills/codex-docs/download_codex_reference.py
   ```

   - This writes `output/llms.txt` and `output/llms-full.txt`
   - Files fetched within the last 24 hours are reused. Pass `--force` to refresh

2. **Find the relevant page**

   - Search `output/llms.txt` first to identify relevant page titles, URLs, or slugs
   - `llms-full.txt` is a concatenated Markdown file keyed by `# Title` headings, so extract full content by title instead of by URL

3. **Extract the matching section**

   ```bash
   python skills/plugins/ai-tools-knowledge/skills/codex-docs/extract_doc_section.py "<title/url/slug>" ["<title/url/slug>"...]
   ```

   - Example: `python skills/plugins/ai-tools-knowledge/skills/codex-docs/extract_doc_section.py "Agent Skills" "Configuration Reference"`
   - Example: `python skills/plugins/ai-tools-knowledge/skills/codex-docs/extract_doc_section.py skills config-reference`
   - When a URL or slug is provided, the script resolves it to a page title through `llms.txt`, then finds that title in `llms-full.txt`
   - Extracted sections are written to `output/temp/<slug-or-title>.txt`

4. **Answer with sources**

   - Base the answer on the extracted text and cite the official URL used
   - If no matching title is present in `llms-full.txt`, say so and, when necessary, check the official page or Markdown twin URL directly

## Notes

- Scripts read and write `output/` relative to this skill directory
- `output/temp/` is scratch space and same-name files may be overwritten
- Each page in `llms.txt` has a `/codex/<slug>.md` Markdown twin that can be checked directly for a single-page source
