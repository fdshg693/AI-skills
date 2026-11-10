<!--
Copy-and-adapt template for generate_llms_excerpt.py. Save an adapted copy in
the new skill as prompts/prompt_generate_excerpt.md and fill in every <<...>>
placeholder (generate_llms_excerpt.py refuses to run while any remains).
Delete this comment block from the copy.

Do NOT change the "Output format" section: the URLs-only, copied-verbatim
contract is what lets the driver script assemble the excerpt from the original
entries and lets check_llms_excerpt.py validate the result mechanically.
-->

The text below is the full contents of `<<relative path of the source index,
e.g. output/llms.txt>>`, the official <<site/product name>> documentation
index. It lists documentation pages grouped under `## Section name` headings,
each in the form `- [Title](URL): description`.

Your task: identify every entry that is genuinely about <<the skill's topic --
name the feature areas concretely, e.g. "X, Y, Z, and the related concepts,
guides, troubleshooting, and reference pages for these features">>. Do NOT
include:

- <<Exclusion 1: a nearby topic that shares keywords with the target topic but
  is out of scope, with a concrete example.>>
- <<Exclusion 2: another confusable product/feature that the AI is likely to
  include by mistake. Add or remove bullets as needed.>>

Output format -- this is important, follow it exactly:

- Output ONLY the URL of each entry you are including, one per line.
- Copy each URL exactly as it appears in the source (character for character).
- Do not include titles, descriptions, section headings, numbering, bullet markers,
  or any other commentary before, between, or after the URLs.
