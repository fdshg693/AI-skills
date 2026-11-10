# CodeGraph docs index

Generated from `colbymchenry/codegraph` `site/src/content/docs` (`main`).
This file is not upstream; it is built from each page's `title` / `description`.

## root

- [Troubleshooting](troubleshooting.md) — Fixes for the most common CodeGraph issues.

## core-concepts

- [How It Works](core-concepts/how-it-works.md) — The extraction, storage, resolution, and auto-sync pipeline.
- [The Knowledge Graph](core-concepts/knowledge-graph.md) — The node and edge kinds the graph is built from.
- [Resolution & Frameworks](core-concepts/resolution.md) — How CodeGraph connects references and links routes to handlers.

## getting-started

- [Configuration](getting-started/configuration.md) — CodeGraph is zero-config by default, with one optional codegraph.json for custom extensions, excluding tracked directories, indexing gitignored source, and indexing nested git repositories.
- [Installation](getting-started/installation.md) — Install CodeGraph and configure your AI coding agents.
- [Introduction](getting-started/introduction.md) — What CodeGraph is, and why it makes AI coding agents faster and more precise.
- [Next Steps](getting-started/next-steps.md) — Where to go once CodeGraph is installed and indexing.
- [Get Started](getting-started/quickstart.md) — Get up and running with CodeGraph in seconds.
- [Your First Graph](getting-started/your-first-graph.md) — Build an index and run your first queries against it.

## guides

- [Affected Tests in CI](guides/affected-tests.md) — Run only the tests a change actually touches.
- [Framework Routes](guides/framework-routes.md) — CodeGraph links URL patterns to the handlers that serve them.
- [Indexing a Project](guides/indexing.md) — Full index, incremental sync, and the file watcher.
- [Reading Your Graph in the Browser](guides/viewer.md) — codegraph ui opens a local viewer for an indexed project — callers, source, and callees on one screen.

## reference

- [API](reference/api.md) — Use CodeGraph as a TypeScript library.
- [CLI](reference/cli.md) — Every CodeGraph command and the flags it accepts.
- [Integrations](reference/integrations.md) — Supported agents, and manual MCP setup.
- [Languages](reference/languages.md) — Every language CodeGraph parses, and the extensions it recognizes.
- [MCP Server](reference/mcp-server.md) — The tools CodeGraph exposes to AI agents over MCP.
