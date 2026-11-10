The text below is the full contents of `output/llms.txt`, the official Apify
documentation index (docs.apify.com). It lists documentation pages grouped
under `## Section name` headings, each in the form `- [Title](URL): description`
(entries may be indented to show nesting).

Your task: identify the entries that serve as **entry points** a developer
would open first to understand or use Apify. Include:

- The top-level overview / "get started" / quick start page of every area:
  Apify API (v2 overview and getting started), API client for JavaScript,
  API client for Python, SDK for JavaScript, SDK for Python, Apify CLI
  (overview, installation, quick start, command reference), platform
  sections (actors, storage, proxy, integrations, account, security,
  console, get-started).
- Core concept pages under actors and storage: Actor definition
  (actor.json, input schema, output schema, dataset schema), Actor
  development, deployment, running Actors, Actors in Store and their
  pricing models (pay per event / pay per result / rental), Actor tasks,
  schedules, webhooks, Standby mode, monetization / publishing, limits,
  usage and billing concepts, datasets, key-value stores, request queues.
- AI-agent related pages: the Apify MCP server, Agent Skills, and the
  overview pages for LLM/agent framework integrations (e.g. LangChain,
  LlamaIndex, CrewAI, OpenAI Agents, Vercel AI SDK) and for workflow
  tools (Make, n8n, Zapier).

Do NOT include:

- Individual REST API endpoint pages (e.g. `api/v2/actor-run-abort-post`,
  `api/v2/dataset-items-get`, "Get default store's record"). Keep only the
  API overview / getting-started / top-level group pages.
- Apify Academy lessons and courses (web scraping tutorials, anti-scraping,
  Puppeteer/Playwright lessons). Keep at most the Academy root page.
- Legal documents, changelogs, telemetry, promo codes, and
  per-class/per-method reference pages of the SDKs and API clients
  (e.g. individual `ActorClient` / `DatasetClient` class pages).
- Niche third-party integrations (individual CRMs, storage buckets,
  messaging apps) beyond the ones named above.

Output format -- this is important, follow it exactly:

- Output ONLY the URL of each entry you are including, one per line.
- Copy each URL exactly as it appears in the source (character for character).
- Do not include titles, descriptions, section headings, numbering, bullet markers,
  or any other commentary before, between, or after the URLs.
