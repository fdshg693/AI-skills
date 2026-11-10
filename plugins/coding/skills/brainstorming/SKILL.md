---
# 新機能追加などの際に、アイデアからスペックファイルに起こすためのスキル。
name: brainstorming
# サブエージェントを多用したりせず（レビューくらい）、オーバーヘッド少なめのシンプルなフロー
# ただし、確実にコンテキストを理解するための探索を行うので、そこのコストはかかる
description: "You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements, and design before implementation, and ends after writing the approved spec."
# 必要エージェント: code-reviewer
# 後続スキル: writing-plans
# 出力: docs/specs/<topic>-design.md
meta:
  tag: []
  requires_repo_tools: none
  requires_env: none
  dependencies: none
  requires_install: none
  requires_hooks: none
  requires_skills: elements-of-style:writing-clearly-and-concisely
  status: stable
  description: no description
  version: 1.0.1
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design, get user approval, and write the approved spec file.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action in this skill. This skill ends after the approved design has been written to a spec file. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but you MUST present it and get approval.

## Checklist

You MUST create a task for each of these items and complete them in order:

1. **Explore project context** — check files, docs, recent commits
2. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Present design** — in sections scaled to their complexity, get user approval after each section
5. **Write design doc** — save to `docs/specs/<topic>-design.md`
6. **Spec review (subagent)** — dispatch a subagent to review the spec for placeholders, contradictions, ambiguity, scope; fix any findings inline (see below)
7. **User reviews written spec** — ask the user to review the spec file before concluding the brainstorming process

## Process Flow

see @flow.dot

**The terminal state is completing the written spec handoff.** Do NOT invoke any implementation skill from this workflow.

## The Process

**Understanding the idea:**

- Check out the current project state first (files, docs, recent commits)
- Before asking detailed questions, assess scope: if the request describes multiple independent subsystems (e.g., "build a platform with chat, file storage, billing, and analytics"), flag this immediately. Don't spend questions refining details of a project that needs to be decomposed first.
- If the project is too large for a single spec, help the user decompose into sub-projects: what are the independent pieces, how do they relate, what order should they be built? Then brainstorm the first sub-project through the normal design flow. Each sub-project gets its own spec cycle.
- For appropriately-scoped projects, ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message - if a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**

- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why

**Presenting the design:**

- Once you believe you understand what you're building, present the design
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

**Design for isolation and clarity:**

- Break the system into smaller units that each have one clear purpose, communicate through well-defined interfaces, and can be understood and tested independently
- For each unit, you should be able to answer: what does it do, how do you use it, and what does it depend on?
- Can someone understand what a unit does without reading its internals? Can you change the internals without breaking consumers? If not, the boundaries need work.
- Smaller, well-bounded units are also easier for you to work with - you reason better about code you can hold in context at once, and your edits are more reliable when files are focused. When a file grows large, that's often a signal that it's doing too much.

**Working in existing codebases:**

- Explore the current structure before proposing changes. Follow existing patterns.
- Where existing code has problems that affect the work (e.g., a file that's grown too large, unclear boundaries, tangled responsibilities), include targeted improvements as part of the design - the way a good developer improves code they're working in.
- Don't propose unrelated refactoring. Stay focused on what serves the current goal.

## After the Design

**Documentation:**

- Write the validated design (spec) to `docs/specs/<topic>-design.md`
  - (User preferences for spec location override this default)
- Use elements-of-style:writing-clearly-and-concisely skill if available

**Spec Review (subagent):**
After writing the spec document, dispatch a subagent to review it with fresh eyes — do NOT review it yourself. Use the Agent tool (e.g. `general-purpose` or `subagents:code-reviewer`) and pass the absolute path to the spec file along with the review criteria below.

The subagent should report findings against:

1. **Placeholder scan:** Any "TBD", "TODO", incomplete sections, or vague requirements?
2. **Internal consistency:** Do any sections contradict each other? Does the architecture match the feature descriptions?
3. **Scope check:** Is this focused enough for a single implementation effort, or does it need decomposition?
4. **Ambiguity check:** Could any requirement be interpreted two different ways?

Ask the subagent to return a concise punch list of concrete issues with file locations — not a rewrite, not a rating. When the report comes back, fix each finding inline in the spec yourself. No need to re-dispatch the subagent — just fix and move on.

Example dispatch prompt:

> "Review the spec at `<absolute path>` against these four criteria: (1) placeholders/TODOs/vague requirements, (2) internal contradictions between sections, (3) scope — is this one implementation effort or does it need decomposition, (4) ambiguous requirements that could be read two ways. Return a punch list of concrete issues with the section/line where each appears. Under 300 words. Do not rewrite the spec."

**User Review Gate:**
After the subagent's findings have been resolved, ask the user to review the written spec before concluding:

> "Spec written to `<path>`. Please review it and let me know if you want to make any changes."

Wait for the user's response. If they request changes, make them and re-dispatch the subagent review on the updated spec. Once the user approves, stop. Do not start implementation or planning from this skill.

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design, get approval before moving on
- **Be flexible** - Go back and clarify when something doesn't make sense
