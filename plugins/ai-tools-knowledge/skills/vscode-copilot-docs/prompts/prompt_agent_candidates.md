The list below contains entries from the VS Code official documentation index
(llms.txt) that are NOT present in `output/copilot-excerpt.md` (the curated
GitHub Copilot / AI agent excerpt), but were mechanically flagged as "likely
Copilot/AI-related" by a keyword heuristic (substring matches on words like
copilot, chat, agent, ai, mcp). Entries are grouped under `## Section name`
headings, in the form `- [Title](URL): description`.

For each entry, judge from its title, URL, and description whether it is truly
about GitHub Copilot / AI agent functionality in VS Code (Chat, Agent mode, MCP,
custom instructions, etc.). Flag any entry that only happened to match a keyword
but is actually unrelated, or belongs to a different product than GitHub Copilot
(for example, the Foundry Toolkit / Intelligent Apps extension, which builds and
deploys its own AI models/agents independently of GitHub Copilot).

Output format:

- For each entry, state "relevant" or "not relevant (false positive)" with a one-line reason
- At the end, summarize only the entries you suspect are false positives, if any. If none, say so explicitly.
