---
source: skills/plugins/topics/skills/ona-docs/output/docs/llms.txt
extracted_from_fetched_at: 2026-08-11T14:27:39.037476+00:00
curated_at: 2026-08-12
note: >
  This is a curated subset of ona-docs/output/docs/llms.txt (the ona.com/docs
  technical documentation index), containing only entries about using the Ona
  CLI (the `ona` command) -- installation, authentication, managing
  environments and running commands from the terminal, driving Automations as
  Code via the CLI, and the CLI command reference. Unlike vscode-docs'
  llms.txt, ona-docs' llms.txt has no meaningful per-topic `## Section`
  headings of its own (just one flat `## Docs` list), so entries here are kept
  under a single heading in source order rather than grouped by source
  section. The REST/Connect API reference (api-reference/... entries) is
  intentionally excluded -- that is a different integration surface from the
  CLI. Regenerate/re-review this file with check_cli_excerpt.py whenever
  ona-docs/output/docs/llms.txt is refreshed, since it can drift.
---

## CLI

- [Using environments from external agents](https://ona.com/docs/ona/environments/agent-environments.md): Manage Ona environments from external AI agents like Claude Code or Cursor using the Ona CLI.
- [Automations as Code](https://ona.com/docs/ona/automations/automations-as-code.md): Define, version, and share Automations using YAML files and the Ona CLI.
- [CLI](https://ona.com/docs/ona/integrations/cli.md): Manage environments, SSH access, and automations from your terminal.
- [Personal access tokens](https://ona.com/docs/ona/integrations/personal-access-token.md): Authenticate CLI and SDK access for automation and CI/CD.
- [CLI command reference](https://ona.com/docs/ona/reference/cli.md): Common Ona CLI commands for environments, automations, and configuration.
