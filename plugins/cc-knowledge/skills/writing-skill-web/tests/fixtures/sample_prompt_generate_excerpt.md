The text below is the full contents of `sample_llms.txt`, a fixture index
used to test generate_llms_excerpt.py. It lists documentation pages grouped
under `## Section name` headings, each in the form `- [Title](URL): description`.

Your task: identify every entry that is genuinely about getting started and
authentication. Do NOT include:

- Rate limiting or webhook entries -- out of scope for this fixture's test.
- The changelog entry -- release notes are not relevant here.

Output format -- this is important, follow it exactly:

- Output ONLY the URL of each entry you are including, one per line.
- Copy each URL exactly as it appears in the source (character for character).
- Do not include titles, descriptions, section headings, numbering, bullet markers,
  or any other commentary before, between, or after the URLs.
