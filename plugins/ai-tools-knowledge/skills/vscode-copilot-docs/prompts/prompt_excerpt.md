The list below is the full contents of `output/copilot-excerpt.md`, a human-curated
subset of the VS Code official documentation index (llms.txt) that is supposed to
contain only entries about GitHub Copilot / AI agent functionality inside VS Code
(Chat, Agent mode, MCP, custom instructions, etc.). Entries are grouped under
`## Section name` headings, in the form `- [Title](URL): description`.

For each entry, judge from its title, URL, and description whether it truly belongs
in this curated list, i.e. whether it is genuinely about GitHub Copilot / AI agent
features in VS Code. Flag any entry that looks like it was miscurated: for example,
an entry about a different product that happens to mention AI/agent terminology
(such as the Foundry Toolkit / Intelligent Apps extension, which is a separate
product from GitHub Copilot), or a plain editor feature that does not actually
involve Copilot or AI agents.

Output format:

- For each entry, state "belongs" or "does not belong (needs review)" with a one-line reason
- At the end, summarize only the entries you flagged as not belonging, if any. If none, say so explicitly.
