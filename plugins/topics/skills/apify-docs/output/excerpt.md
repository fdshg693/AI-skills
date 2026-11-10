---
source: llms.txt
extracted_from_fetched_at: 2026-09-27T08:35:33.418673+00:00
generated_at: 2026-09-27T08:36:31.653692+00:00
generated_by: generate_apify_excerpt.py (aim --model gemini-3.8-flash)
note: >
  AI-generated draft (generate_apify_excerpt.py), reviewed by hand: added
  the coding-agent integrations (Claude, Claude Code, Codex CLI, Cursor,
  Copilot CLI, VS Code) and MCP connectors. Fix drift by editing this file
  directly and re-running check_apify_excerpt.py (do not re-run the AI model).
---

## Apify API

- [Apify API documentation](https://docs.apify.com/api.md)
- [Apify API](https://docs.apify.com/api/v2.md): The Apify API (version 2) provides programmatic access to the [Apify
- [Get started with Apify API](https://docs.apify.com/api/v2/getting-started.md): The Apify API provides programmatic access to the [Apify platform](https://docs.apify.com).

## Apify API client for JavaScript

- [Overview](https://docs.apify.com/api/client/js/docs.md): The official JavaScript library to access the Apify API, with automatic retries, TypeScript support, and cross-platform compatibility.
- [Quick start](https://docs.apify.com/api/client/js/docs/introduction/quick-start.md): Get started with the Apify API client for JavaScript by running an Actor and retrieving results from its dataset.

## Apify API client for Python

- [Overview](https://docs.apify.com/api/client/python/docs.md): The official Python library to access the Apify API, with automatic retries, async support, and comprehensive API coverage.
- [Quick start](https://docs.apify.com/api/client/python/docs/introduction/quick-start.md): Get started with the Apify API client for Python by running an Actor and retrieving results from its dataset.

## Apify SDK for JavaScript

- [Apify SDK for JavaScript](https://docs.apify.com/sdk/js/docs/overview.md): The official library for creating Apify Actors in JavaScript, providing tools for web crawling, scraping, and automation at scale.
- [Quick start](https://docs.apify.com/sdk/js/docs/introduction/quick-start.md): Get started with the Apify SDK for JavaScript by creating your first Actor.

## Apify SDK for Python

- [Overview](https://docs.apify.com/sdk/python/docs/overview.md): The official library for creating Apify Actors in Python, providing tools for web scraping, automation, and data storage integration.
- [Quick start](https://docs.apify.com/sdk/python/docs/quick-start.md): Get started with the Apify SDK for Python by creating your first Actor.

## Apify CLI

- [Apify CLI overview](https://docs.apify.com/cli/docs.md): An introduction to Apify CLI, a command-line interface for creating, developing, building, and running Apify Actors and managing the Apify cloud platform.
- [Quick start](https://docs.apify.com/cli/docs/quick-start.md): Learn how to create, run, and manage Actors using Apify CLI.
- [Installation](https://docs.apify.com/cli/docs/installation.md): Learn how to install Apify CLI using installation scripts, Homebrew, or NPM.
- [Command reference](https://docs.apify.com/cli/docs/reference.md): The Apify CLI provides tools for managing your Apify projects and resources from the command line.

## Apify Academy

- [Apify Academy](https://docs.apify.com/academy.md): Learn everything about web scraping and automation with our free courses that will turn you into an expert scraper developer.

## account

- [Account](https://docs.apify.com/account.md): Manage your Apify account, billing, security, organization, and access permissions.
- [Billing](https://docs.apify.com/account/billing.md): View invoices, track current billing cycle usage, manage subscriptions and limits, and review historical usage from the Billings page in Console.
- [Apify Console](https://docs.apify.com/account/console.md): Get started with Apify Console: create an account, sign in with email, Google, or GitHub, and manage your web scraping projects from one place.
- [Limits](https://docs.apify.com/account/limits.md): View default resource limits for the Apify platform, including max memory, disk size, and number of Actors and tasks per user per plan tier.
- [Apify subscription plans](https://docs.apify.com/account/subscriptions.md): Learn which Apify plan best fits your needs, how to subscribe, and how usage limits and overage charges work when you exceed your prepaid usage.

## actors

- [Actors](https://docs.apify.com/actors.md): Learn how to develop, run and share serverless cloud programs. Create your own web scraping and automation tools and publish them on the Apify platform.
- [Develop Actors](https://docs.apify.com/actors/development.md): Read about the technical part of building Apify Actors. Learn to define Actor inputs, build new versions, persist Actor state, and choose base Docker images.
- [Actor definition](https://docs.apify.com/actors/development/actor-definition.md): Learn how to define an Actor by adding a .actor directory with actor.json, a Dockerfile, README, and input schema files to your source code.
- [Actor definition file (actor.json)](https://docs.apify.com/actors/development/actor-definition/actor-json.md): Configure your Actor using the .actor/actor.json file to define its name, version number, build tag, and links to input and output schema files.
- [Actor input schema](https://docs.apify.com/actors/development/actor-definition/input-schema.md): Learn how to define and validate a schema for your Actor's input with code examples. Provide an autogenerated input UI for your Actor's users.
- [Actor output schema](https://docs.apify.com/actors/development/actor-definition/output-schema.md): Define an output schema to specify where your Actor stores its results and how Apify Console and the Actor run API endpoint display them to users.
- [Actor deployment](https://docs.apify.com/actors/development/deployment.md): Learn how Actor deployment works. Keep your code on the Apify platform and deploy with the Apify CLI, or host it in Git and build on every push.
- [Develop Actors in Standby mode](https://docs.apify.com/actors/development/programming-interface/standby.md): Develop Actors that run a persistent HTTP server in Standby mode, enabling fast real-time API responses without restarting the Actor each time.
- [Actor development quick start](https://docs.apify.com/actors/development/quick-start.md): Choose how to build your first Actor on Apify - local development with the CLI, the web IDE, AI-assisted coding, or building an AI agent on the platform.
- [Build Actors with AI](https://docs.apify.com/actors/development/quick-start/build-with-ai.md): Build new Actors or improve existing ones using AI coding tools by providing the right context, prompts, Agent Skills, and the Apify MCP server.
- [Develop AI agents on Apify](https://docs.apify.com/actors/development/quick-start/develop-ai-agents.md): Build and deploy AI agents on Apify with framework templates, sandboxes, OpenRouter for LLM access, and pay-per-event pricing.
- [Set up Actor monetization](https://docs.apify.com/actors/monetize/set-up-monetization.md): Learn how to set up and change monetization for your Actor in Apify Console.
- [Publish Actors](https://docs.apify.com/actors/publishing.md): Learn the stages involved in publishing and monetizing Actors on the Apify platform, from development and testing to promotion in Apify Store.
- [Monetize Actors](https://docs.apify.com/actors/publishing/monetize.md): Monetize your Actors on Apify Store and earn regular passive income.
- [Pay-per-event pricing model](https://docs.apify.com/actors/publishing/monetize/pay-per-event.md): Learn how to monetize your Actor with pay-per-event (PPE) pricing, charging users for specific actions like Actor starts, dataset items, or API calls.
- [Actor pricing and costs](https://docs.apify.com/actors/publishing/monetize/pricing-and-costs.md): Learn how to set Actor pricing and calculate your costs, including platform usage rates, discount tiers, and profit formulas for the PPE model.
- [Actor rental pricing model](https://docs.apify.com/actors/publishing/monetize/rental.md): Learn how to monetize your Actor with the rental pricing model, offering a free trial and a flat monthly fee, and understand how profit is calculated.
- [Publish your Actor](https://docs.apify.com/actors/publishing/publish.md): Prepare your Actor for publication on Apify Store.
- [Run Actors](https://docs.apify.com/actors/running.md): Start an Actor from Apify Console or via API. Learn about Actor lifecycles, how to specify settings and version, provide input, and resurrect finished runs.
- [Actors in Store](https://docs.apify.com/actors/running/actors-in-store.md): Browse Apify Store to discover thousands of public Actors, understand their pricing models, and choose the right one for your automation needs.
- [Actor runs and builds](https://docs.apify.com/actors/running/runs-and-builds.md): Learn about Actor builds and runs, including their lifecycle, version tagging, storage assignment, sharing options, and data retention policy.
- [Actor and task schedules](https://docs.apify.com/actors/running/schedules.md): Learn how to automatically start your Actor and task runs and the basics of cron expressions. Set up and manage your schedules from Apify Console or via API.
- [Actor Standby mode](https://docs.apify.com/actors/running/standby.md): Use Actor Standby mode to keep an Actor ready in the background and serve real-time HTTP requests without waiting for a cold start each time.
- [Actor tasks](https://docs.apify.com/actors/running/tasks.md): Create and save reusable configurations of Apify Actors for specific use cases, then run them on a schedule, via the API, or from the console.
- [Actor usage and resources](https://docs.apify.com/actors/running/usage-and-resources.md): Learn about memory and processing power requirements for Apify Actors, their relationship with Docker resources, and how resource allocation affects cost.

## console

- [Apify Store](https://docs.apify.com/console/store.md): Browse thousands of pre-built Actors in Apify Store, filter by category or pricing, and run them immediately or save settings for later use.

## get-started

- [Get started](https://docs.apify.com/get-started.md): Learn how the Apify platform works - what Actors are, how they get to Apify Store, and how to start by running existing Actors or building your own.
- [Apify for AI agents](https://docs.apify.com/get-started/agent-onboarding.md): Connect your AI agent to the Apify platform - scrape the web, run Actors, and retrieve structured data via MCP, Agent Skills, client libraries, or the REST API.
- [Build Actors](https://docs.apify.com/get-started/build-actors.md): Build your own Actor on the Apify platform - create it from a template, understand the Actor model, deploy it, and publish it to Apify Store.
- [Run Actors](https://docs.apify.com/get-started/run-actors.md): Run existing Actors from Apify Store to get data or automate tasks with no code - pick an Actor, configure input, collect results, then automate.

## integrations

- [Integrations](https://docs.apify.com/integrations.md): Connect the Apify platform to external services, data pipelines, and automation workflows using APIs, webhooks, and third-party integrations.
- [AI integrations](https://docs.apify.com/integrations/ai.md): Use Apify Actors with AI providers like Anthropic Claude, OpenAI, and Google - via the Apify MCP server, agent SDKs, frameworks, and vector databases.
- [Claude](https://docs.apify.com/integrations/claude.md): Use Apify Actors with Anthropic Claude - connect the Apify MCP server to Claude Desktop, or install the Apify plugin for the Claude Code CLI.
- [Claude Code CLI integration](https://docs.apify.com/integrations/claude-code-cli.md): Learn how to install the Apify plugin for Claude Code CLI to discover, run, and build Actors with the Apify MCP server, skills, and a routing agent.
- [Codex CLI integration](https://docs.apify.com/integrations/codex-cli.md): Learn how to install the Apify plugin for Codex CLI to discover, run, and build Actors with the Apify MCP server and bundled skills for common workflows.
- [🤖🚀 CrewAI integration](https://docs.apify.com/integrations/crewai.md): Learn how to integrate Apify Actors with CrewAI to equip multi-agent AI crews with real-time web scraping and data extraction capabilities now.
- [Cursor integration](https://docs.apify.com/integrations/cursor.md): Learn how to install the Apify plugin for Cursor to discover, run, and build Actors directly with the Apify MCP server, skills, and a routing agent.
- [GitHub Copilot CLI integration](https://docs.apify.com/integrations/github-copilot-cli.md): Learn how to install the Apify plugin for the GitHub Copilot CLI to discover, run, and build Actors with the Apify MCP server, skills, and a routing agent.
- [LangChain integration](https://docs.apify.com/integrations/langchain.md): Learn how to integrate Apify with LangChain to feed vector databases and large language models with web data crawled from the web using Actors.
- [LangChain ecosystem](https://docs.apify.com/integrations/langchain-ecosystem.md): Use Apify Actors across the LangChain ecosystem - wrap Actors as LangChain tools and document loaders, or bind them to stateful LangGraph agents.
- [LlamaIndex integration](https://docs.apify.com/integrations/llama-index.md): Learn how to integrate Apify with LlamaIndex to feed vector databases and large language models with web data crawled from the web using Actors.
- [Make integration](https://docs.apify.com/integrations/make.md): Connect Apify Actors to Make scenarios to run Actors, monitor run statuses, and receive Actor results directly inside your automated workflows.
- [Apify MCP server](https://docs.apify.com/integrations/mcp.md): Learn how to use the Apify MCP server to integrate Apify's library of Actors into your AI agents or large language model-based applications.
- [MCP connectors](https://docs.apify.com/integrations/mcp-connectors.md): Use MCP connectors to let Apify Actors call third-party services through Model Context Protocol on your behalf, without exposing your credentials to Actor code.
- [n8n integration](https://docs.apify.com/integrations/n8n.md): Connect Apify with n8n to automate workflows by running Actors, extracting structured data, and reacting to Actor or task run events in real time.
- [OpenAI](https://docs.apify.com/integrations/openai.md): Use Apify Actors with OpenAI - call scrapers and crawlers from ChatGPT, Codex, the OpenAI Agents SDK, and OpenAI Assistants to feed models live web data.
- [OpenAI Agents SDK integration](https://docs.apify.com/integrations/openai-agents.md): Learn how to integrate Apify with the OpenAI Agents SDK via the Apify MCP server to give your AI agents real-time web data and Actor access.
- [🔺 Vercel AI SDK integration](https://docs.apify.com/integrations/vercel-ai-sdk.md): Learn how to integrate Apify Actors as tools for AI agents built with Vercel AI SDK to access real-time web data in your TypeScript applications.
- [VS Code integration](https://docs.apify.com/integrations/vscode.md): Learn how to install the Apify agent plugin in VS Code to discover, run, and build Actors with the Apify MCP server, bundled skills, and a routing agent.
- [Webhook integration](https://docs.apify.com/integrations/webhooks.md): Learn how to integrate multiple Apify Actors or external systems with your Actor or task run. Send alerts when your Actor run succeeds or fails.
- [Workflows and notifications](https://docs.apify.com/integrations/workflows-and-notifications.md): Trigger Apify Actors from workflow platforms like n8n, Make, and Zapier, route results to Slack and email, and build no-code flows in Gumloop.
- [Zapier integration](https://docs.apify.com/integrations/zapier.md): Connect Apify Actors to Slack, Google Sheets, Salesforce, and more with Zapier. Trigger workflows when Actor or task runs finish and retrieve results.

## proxy

- [Proxy](https://docs.apify.com/proxy.md): Learn to anonymously access websites in scraping/automation jobs. Improve data outputs and efficiency of bots, and access websites from various geographies.

## security

- [Security](https://docs.apify.com/security.md): Apify's security practices, compliance certifications, and vulnerability disclosure policy for protecting your Actors, data, and the platform.

## storage

- [Storage](https://docs.apify.com/storage.md): Store anything from images and key-value pairs to structured output data. Learn how to access and manage your stored data from the Apify platform or via API.
- [Dataset](https://docs.apify.com/storage/dataset.md): Store and export web scraping, crawling or data processing job results. Learn how to access and manage datasets in Apify Console or via API.
- [Dataset schema specification](https://docs.apify.com/storage/dataset-schema.md): Define a dataset schema to control how your Actor's results are structured, validated, and displayed in Apify Console, the API, and integrations.
- [Key-value store](https://docs.apify.com/storage/key-value-store.md): Store anything from Actor or task run results, JSON documents, or images. Learn how to access and manage key-value stores from Apify Console or via API.
- [Key-value store schema specification](https://docs.apify.com/storage/key-value-store-schema.md): Define a key-value store schema to organize records into collections with content type validation, making your Actor's key-value store easier to navigate.
- [Request queue](https://docs.apify.com/storage/request-queue.md): Queue URLs for an Actor to visit in its run. Learn how to share your queues between Actor runs. Access and manage request queues from Apify Console or via API.
