---
# Sources (fetched 2026-07-20 via the antigravity-docs skill):
#   https://antigravity.google/docs/skills
#   https://antigravity.google/docs/ide/skills
#   https://antigravity.google/docs/plugins
# Depends on: antigravity-docs skill — re-fetch the sources above to refresh this reference when the docs change.
name: antigravity-skills
description: Use when creating, placing, invoking, or troubleshooting agent skills in Google Antigravity — SKILL.md format and frontmatter fields, workspace vs global vs plugin skill locations, how the agent discovers and activates skills, and official best practices. Grounded in the official Antigravity documentation; refresh against the latest docs via the antigravity-docs skill.
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: antigravity-docs
  status: stable
  description: no description
  version: 1.0.3
---

# Antigravity Skills Reference

How agent skills work in Google Antigravity, grounded in the official documentation:

- https://antigravity.google/docs/skills
- https://antigravity.google/docs/ide/skills
- https://antigravity.google/docs/plugins

## What skills are

Skills are an [open standard](https://agentskills.io/home) for extending agent
capabilities. A skill is a folder containing a `SKILL.md` file with instructions
the agent follows for a specific type of task. Each skill packages:

- **Instructions** for how to approach a specific type of task
- **Best practices** and conventions to follow
- **Optional scripts and resources** the agent can use

## Where skills live

| Location                                          | Scope                   |
| :------------------------------------------------ | :---------------------- |
| `<workspace-root>/.agents/skills/<skill-folder>/` | Workspace-specific      |
| `~/.gemini/config/skills/<skill-folder>/`         | Global (all workspaces) |

- **Workspace skills** fit project-specific workflows (team deployment process,
  testing conventions). **Global skills** fit personal utilities wanted
  everywhere.
- Backward compatibility: `.agent/skills` (singular) is still supported, but
  `.agents/skills` is the default.
- **Discrepancy in the official docs**: the IDE skills page lists the global
  location as `~/.gemini/antigravity/skills/` instead of
  `~/.gemini/config/skills/`. If a global skill is not picked up, check both.

### Skills bundled in plugins

Plugins bundle skills under a `skills/` subdirectory, next to a required
`plugin.json` marker file:

```text
plugins/<plugin-name>/
├── plugin.json       # Required marker file ({ "name": "..." }, name defaults to the directory name)
├── skills/
│   └── <skill-name>/
│       └── SKILL.md
└── rules/            # Optional rules (<rule-name>.md); plugins can also ship mcp_config.json and hooks.json
```

Antigravity scans these plugin locations automatically:

- **Workspace**: `.agents/plugins/` (or `_agents/plugins/`) at the workspace root
- **Global**: `~/.gemini/config/plugins/`

This skill itself ships inside a workspace plugin
(`.agents/plugins/antigravity-meta/skills/antigravity-skills/`).

## SKILL.md format

YAML frontmatter at the top, instructions below:

```markdown
---
name: my-skill
description: Helps with a specific task. Use when you need to do X or Y.
---

# My Skill

Detailed instructions for the agent go here.

## When to use this skill

- Use this when...
- This is helpful for...

## How to use it

Step-by-step guidance, conventions, and patterns the agent should follow.
```

Frontmatter fields (only these two are documented for Antigravity):

| Field         | Required | Description                                                                                                                                                                                                                                                            |
| :------------ | :------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`        | No       | Unique identifier (lowercase, hyphens for spaces). Defaults to the folder name.                                                                                                                                                                                        |
| `description` | Yes      | What the skill does and when to use it — this is what the agent sees when deciding whether to apply the skill. Write it in third person with keywords that help the agent recognize relevance (e.g. "Generates unit tests for Python code using pytest conventions."). |

Note: Claude Code-style frontmatter extensions (arguments, invocation control,
`` !`command` `` dynamic context injection, `context: fork`) are **not**
documented for Antigravity — do not rely on them in Antigravity skills.

## Skill folder structure

`SKILL.md` is the only required file; additional resources are optional and read
by the agent only when the instructions call for them:

```text
.agents/skills/my-skill/
├── SKILL.md       # Main instructions (required)
├── scripts/       # Helper scripts (optional)
├── examples/      # Reference implementations (optional)
└── resources/     # Templates and other assets (optional)
```

## How the agent uses skills

Skills follow a **progressive disclosure** pattern:

1. **Discovery** — at conversation start the agent sees only the list of
   available skills with their names and descriptions
2. **Activation** — if a skill looks relevant to the task, the agent reads the
   full `SKILL.md`
3. **Execution** — the agent follows the skill's instructions while working

The agent decides on its own based on context; to force a skill, mention it by
name in the prompt.

## Best practices (official)

- **Keep skills focused** — one skill per distinct task, not a "do everything" skill
- **Write clear descriptions** — the description alone drives the agent's decision to activate
- **Use scripts as black boxes** — tell the agent to run scripts with `--help` first instead of reading the entire source
- **Include decision trees** — for complex skills, add a section that maps situations to the right approach

## Minimal example (from the official docs)

```markdown
---
name: code-review
description: Reviews code changes for bugs, style issues, and best practices. Use when reviewing PRs or checking code quality.
---

# Code Review Skill

When reviewing code, follow these steps:

## Review checklist

1. **Correctness**: Does the code do what it's supposed to?
2. **Edge cases**: Are error conditions handled?
3. **Style**: Does it follow project conventions?
4. **Performance**: Are there obvious inefficiencies?

## How to provide feedback

- Be specific about what needs to change
- Explain why, not just what
- Suggest alternatives when possible
```

## Keeping this reference fresh

This skill is a snapshot of the official docs. When details matter (or something
here no longer matches observed behavior), use the **antigravity-docs** skill to
re-fetch the source pages listed at the top and update this file.
