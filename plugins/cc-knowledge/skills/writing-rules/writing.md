# Creating and Editing a Single Rule File

## General guidelines for writing documentation in this codebase

Focus on discovering the essential knowledge that would help an AI agents be immediately productive in this codebase.
Consider aspects like:

- The "big picture" architecture that requires reading multiple files to understand - major components, service boundaries, data flows, and the "why" behind structural decisions
- Critical developer workflows (builds, tests, debugging) especially commands that aren't obvious from file inspection alone
- Project-specific conventions and patterns that differ from common practices
- Integration points, external dependencies, and cross-component communication patterns

- Write concise, actionable instructions (~20-50 lines) using markdown structure
- Include specific examples from the codebase when describing patterns(keep it short and focused)
- Avoid generic advice ("write tests", "handle errors") - focus on THIS project's specific approaches
- Document only discoverable patterns, not aspirational practices
- Reference key files/directories that exemplify important patterns

## How to write `.claude/rules/*.md` files

All persisted knowledge in this codebase is stored as **rule files** under `.claude/rules/`. Do NOT write `folder/CLAUDE.md` files, and do NOT write to the project-root `CLAUDE.md` either. A rule file is a single Markdown file with frontmatter that lists the source paths it applies to; the body contains the documentation that should be loaded into context whenever those paths are touched.

## File format

Each rule file lives at `.claude/rules/<topic>.md` and has this shape:

```markdown
---
paths:
  - "src/FinLearn.Core/Models/Foo.cs"
  - "tests/FinLearn.Tests/FooTests.cs"
  - "frontend/app/components/Foo.tsx"
---

## <Topic> 関連ドキュメント

<short body — point to the authoritative docs (e.g. `docs/FEATURES/Foo/LOGIC.md`)
and summarize what they cover. Keep it focused; do not duplicate the source docs.>
```

- `paths:` is a list of glob/file patterns. Patterns may use `**/*.cs` etc.
- For **project-wide** notes (what would otherwise go in root `CLAUDE.md`), use `paths: ["**"]` so the rule loads on any file touched. See `.claude/rules/architecture.md` for the canonical example.
- The body should be brief (typically 10–30 lines): a heading, a short pointer to the canonical document(s) under `docs/`, and any non-obvious cross-cutting notes.
- See existing examples: `.claude/rules/API.md`, `.claude/rules/FillResult.md`, `.claude/rules/architecture.md`.

## When to add a rule file

Whenever you discover knowledge that:

1. Spans multiple files or layers (domain ↔ API ↔ UI), AND
2. Is not obvious from reading any single file, AND
3. Is not yet covered by an existing rule,

add a new `.claude/rules/<topic>.md` without asking the user. Pick a topic name that matches the domain concept (e.g. `OrderBook.md`, `TurnProcessor.md`), not the folder.

## Granularity guidelines

- Place each rule at the **narrowest topic scope** — one rule per feature/domain concept, not one rule per folder.
- The rule body itself should stay short (~30 lines). Put the actual long-form documentation under `docs/` (e.g. `docs/FEATURES/<Topic>/LOGIC.md`) and have the rule file point to it.
- Project-wide architecture notes also live under `.claude/rules/` (e.g. `.claude/rules/architecture.md`) with `paths: ["**"]` — never in a root `CLAUDE.md`.
