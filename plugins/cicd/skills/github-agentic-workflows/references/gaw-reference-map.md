# GAW official reference map

Use the local snapshot first. The URLs below are the canonical source URLs in `llms.txt` and `llms-full.txt`.

## Authoring and design

- `create-agentic-workflow.md`: new workflow design, trigger/tool/output selection, concise prompt skeleton, and quality checklist.
- `create-agentic-workflow-trigger-details.md`: report windows, PR escalation, incident deduplication, compliance, and coverage-specific trigger guidance.
- `github-agentic-workflows.md`: overall file format, core rules, trigger matrix, repository-local overlay, and compile commands.
- `workflow-patterns.md`: reusable patterns for common workflow shapes and high-volume triage.
- `workflow-constraints.md`: single-job limits, security posture, safe alternatives, and when to use traditional Actions.

## Syntax and runtime

- `syntax.md`: compact schema index; use it to select a narrower reference.
- `syntax-core.md`: `on`, permissions, jobs, steps, checkout, environment, and other core Actions fields.
- `syntax-agentic.md`: `strict`, engine, model, sandbox, network, runtime, imports, and GAW-specific fields.
- `syntax-tools-imports.md`: GitHub tools, `gh-proxy`, bash allowlists, MCP/CLI proxy, cache, imports, and permission patterns.
- `triggers.md`: event mappings, fuzzy schedules, workflow-run failure gates, fork policy, slash commands, and label commands.
- `network.md`: ecosystem and domain allowlists. Read this whenever a workflow installs, builds, tests, or calls an external service.

## Outputs and integrations

- `safe-outputs.md`: safe-output index and shared rules.
- `safe-outputs-content.md`: issues, discussions, comments, pull requests, and reviews.
- `safe-outputs-management.md`: labels, updates, milestones, projects, releases, and uploads.
- `safe-outputs-automation.md`: dispatch, checks, code scanning, assignments, and automation.
- `safe-outputs-runtime.md`: staged mode, URL/mention sanitization, custom jobs/scripts/actions, failure reporting, and output variables.
- `reuse.md`: shared workflow imports and `import-schema`.
- `skills.md`: using SKILL.md files in GAW workflows.
- `subagents.md`: inline sub-agent definitions.

## Editing and operations

- `workflow-editing.md`: when to compile, validation commands, and prompt-authoring rules.
- `cli-commands.md`: `gh aw init`, `compile`, `run`, `logs`, `audit`, `status`, `checks`, `fix`, `upgrade`, `add`, `update`, and MCP equivalents.
- `debug-agentic-workflow.md`: focused logs/audit debugging and missing-tool diagnosis.
- `token-optimization.md`: DataOps, cache, sub-agents, and audit-based token reduction.

When a topic is not represented here, search the local `llms.txt` index and fetch the corresponding official URL; do not infer undocumented fields from examples.
