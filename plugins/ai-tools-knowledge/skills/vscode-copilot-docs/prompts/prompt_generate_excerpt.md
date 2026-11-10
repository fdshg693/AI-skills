The text below is the full contents of `skills/plugins/others/skills/vscode-docs/output/llms.txt`,
the official VS Code documentation index. It lists documentation pages grouped under
`## Section name` headings, each in the form `- [Title](URL): description`.

Your task: identify every entry that is genuinely about GitHub Copilot / AI agent
functionality in VS Code -- Chat, Agent mode, agent customization (custom
instructions, prompt files, custom agents, Agent Skills, hooks, plugins), MCP
servers, subagents, inline/AI-powered code suggestions, and the related concepts,
guides, troubleshooting, and reference pages for these features. Do NOT include:

- Plain editor/tooling features that do not involve Copilot or AI (for example
  terminal profiles, plain Git operations, remote development via SSH, debugging in
  general) even if the page happens to mention "AI" or "agent" in passing.
- Entries about the separate Foundry Toolkit / "Intelligent Apps" extension (for
  building/deploying custom AI models). This is a different product from GitHub
  Copilot even though its docs also use "AI" and "Agent" terminology.

Output format -- this is important, follow it exactly:

- Output ONLY the URL of each entry you are including, one per line.
- Copy each URL exactly as it appears in the source (character for character).
- Do not include titles, descriptions, section headings, numbering, bullet markers,
  or any other commentary before, between, or after the URLs.
