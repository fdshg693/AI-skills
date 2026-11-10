The text below is the full contents of `ona-docs/output/docs/llms.txt`, the
official Ona (ona.com) technical documentation index. It lists documentation
pages, each in the form `- [Title](URL): description`.

Your task: identify every entry that is genuinely about using the Ona CLI (the
`ona` command) -- installation, authentication (`ona login`, personal access
tokens), managing environments from the terminal (`ona environment ...`),
running commands inside an environment (`ona environment exec`, SSH access),
Automations as Code driven via the CLI (`ona ai automation ...`), CLI
configuration/contexts, shell completion, and the CLI command reference. Do NOT
include:

- Pages about the same features but described purely through the web UI, with
  no CLI command examples (for example UI-based Automation setup, organization
  member management screens).
- The REST/Connect API reference (`api-reference/...` entries) -- that is a
  different integration surface from the CLI, even though both let you manage
  the same resources.
- General product concepts (environments, Automations, agents) that don't
  actually walk through `ona` command usage.

Output format -- this is important, follow it exactly:

- Output ONLY the URL of each entry you are including, one per line.
- Copy each URL exactly as it appears in the source (character for character).
- Do not include titles, descriptions, section headings, numbering, bullet markers,
  or any other commentary before, between, or after the URLs.
