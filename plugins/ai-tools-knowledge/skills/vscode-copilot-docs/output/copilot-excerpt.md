---
source: plugins/others/skills/vscode-docs/output/llms.txt
extracted_from_fetched_at: 2026-11-19T03:23:36.539977+00:00
curated_at: 2026-11-19
note: >
  This is a curated subset of vscode-docs/output/llms.txt, containing only
  entries related to GitHub Copilot / AI features in VS Code. The whole
  "AI in VS Code" section and the Copilot-agent sections of "Learn" are
  included; other sections contribute only their Copilot/AI entries.
  Section headers, entry order, titles, URLs (including the .md suffix) and
  descriptions are copied verbatim from the source; duplicate URLs keep their
  first occurrence. Entries about the separate Foundry Toolkit /
  "Intelligent Apps" extension (building/deploying custom AI models) are
  intentionally excluded -- that is a different product from GitHub Copilot,
  even though its docs also use "AI" and "Agent" terminology. Re-check this
  file with check_copilot_excerpt.py (see README.md in this skill) whenever
  vscode-docs/output/llms.txt is refreshed, since it can drift.
---

## AI in VS Code

- [Overview](https://code.visualstudio.com/docs/agents/overview.md): Choose AI workflows, models, and agents in VS Code, from inline suggestions to remote sessions.
- [Find a Guide](https://code.visualstudio.com/docs/agents/guides/overview.md): Find agent tutorials and guides for VS Code by task, from a first app to testing and project workflows.
- [Choose an AI Feature](https://code.visualstudio.com/docs/agents/reference/ai-features-cheat-sheet.md): Choose AI features in VS Code for coding, planning, testing, and reviewing changes.
- [Set Up GitHub Copilot](https://code.visualstudio.com/docs/setup/copilot.md): Set up GitHub Copilot in VS Code, understand billing and data use, and manage your account.
- [Agents Quickstart](https://code.visualstudio.com/docs/agents/quickstart.md): Build and validate a web app with an AI agent in VS Code, then review and recover changes.
- [Agents Tutorial](https://code.visualstudio.com/docs/agents/agents-tutorial.md): Build an app with AI agents in VS Code and learn editor, browser, and source control workflows.
- [Best Practices](https://code.visualstudio.com/docs/agents/best-practices.md): Use AI effectively in VS Code by choosing the right workflow, writing focused prompts, and reviewing results.
- [Inline Suggestions](https://code.visualstudio.com/docs/editing/ai-powered-suggestions.md): Get AI-powered ghost text completions and next edit suggestions in VS Code.
- [Smart Actions](https://code.visualstudio.com/docs/editing/copilot-smart-actions.md): Use AI smart actions in VS Code to generate commit messages, rename symbols, and fix errors.
- [Chat View and Layout](https://code.visualstudio.com/docs/agents/run/chat-view.md): Use AI beside your code in the Chat view, ask questions, run agents, and choose a layout.
- [Agents Window](https://code.visualstudio.com/docs/agents/run/agents-window.md): Start and manage parallel agent sessions, review changes, and finish pull requests in the Agents window.
- [Inline Chat & Quick Chat](https://code.visualstudio.com/docs/chat/inline-chat.md): Use inline chat and Quick Chat in Visual Studio Code for focused edits, terminal help, and short AI conversations.
- [Chat Interactions](https://code.visualstudio.com/docs/chat/chat-overview.md): Use chat in VS Code to ask about code, send requests, add context, and review AI-generated changes.
- [Canvases](https://code.visualstudio.com/docs/agents/run/canvases.md): Collaborate with agents through interactive canvases in VS Code. Find, open, and manage canvas extensions.
- [Add Prompt Context](https://code.visualstudio.com/docs/chat/copilot-chat-context.md): Add files, symbols, images, browser content, and other context to AI prompts in Visual Studio Code for more relevant responses.
- [Review & Revert Changes](https://code.visualstudio.com/docs/agents/run/review-code-edits.md): Review and undo agent edits in Visual Studio Code with working sets, diffs, and checkpoints.
- [Configure the Agents Window](https://code.visualstudio.com/docs/agents/run/agents-window-configuration.md): Configure accounts, models, layout, settings, extensions, and editors in the Agents window.
- [Plan Work](https://code.visualstudio.com/docs/agents/run/planning.md): Create and review implementation plans with GitHub Copilot in VS Code.
- [Use Tools](https://code.visualstudio.com/docs/agents/run/tools.md): Use agent tools in VS Code to inspect code, run commands, control desktop apps, and manage approvals.
- [Browser Tools](https://code.visualstudio.com/docs/agents/run/browser-tools.md): Use browser tools with agents in VS Code to inspect web apps, test user flows, and fix issues.
- [Subagents](https://code.visualstudio.com/docs/agents/run/subagents.md): Delegate focused tasks to context-isolated subagents in VS Code and review results in the main chat.
- [Automations](https://code.visualstudio.com/docs/agents/run/automations.md): Automate routine agent tasks locally or in GitHub from the Agents window, with schedules, repository triggers, and run history.
- [Manage Sessions](https://code.visualstudio.com/docs/agents/run/sessions/manage-sessions.md): Find, continue, organize, and finish agent sessions in VS Code without losing track of ongoing work.
- [Organize & Triage Sessions](https://code.visualstudio.com/docs/agents/run/sessions/organize-sessions.md): Organize agent sessions and triage work that needs attention in the Agents window without archiving it.
- [Memory](https://code.visualstudio.com/docs/agents/run/memory.md): Use cloud-backed and local memory in VS Code to retain coding preferences and repository knowledge.
- [Artifacts](https://code.visualstudio.com/docs/agents/run/artifacts.md): View and manage artifacts, references, screenshots, plans, and other agent session resources in Visual Studio Code.
- [Approvals & Permissions](https://code.visualstudio.com/docs/agents/run/approvals.md): Manage agent permission levels, tool approvals, terminal auto-approval, and sandboxing in VS Code.
- [Agent Sandboxing](https://code.visualstudio.com/docs/agents/run/agent-sandboxing.md): Configure file system and network isolation for Copilot agents and troubleshoot sandbox failures.
- [AI Security](https://code.visualstudio.com/docs/agents/run/security.md): Protect development environments when using AI agents and MCP servers in VS Code with approvals and sandboxing.
- [Choose and Configure Models](https://code.visualstudio.com/docs/agent-customization/language-models.md): Configure chat, inline, and voice models in VS Code. Use your own API key or run models on your device.
- [Choose an Agent Harness](https://code.visualstudio.com/docs/agents/run/agent-harnesses.md): Compare agent harnesses and built-in agents in Visual Studio Code, select one for a session, and review provider requirements.
- [Move from Local to Copilot](https://code.visualstudio.com/docs/agents/run/move-to-copilot.md): Move from the deprecated Local harness to Copilot in VS Code before February 2027.
- [Compare Models Side by Side](https://code.visualstudio.com/docs/agents/run/compare-models.md): Compare model responses and code changes side by side in the Agents window, then continue with the strongest result.
- [Guide: Choose the Right Model](https://code.visualstudio.com/docs/agents/guides/choose-a-model.md): Decide when to use Copilot Fusion, Auto, or an individual model, and compare models on coding tasks to balance quality, time, and cost.
- [Overview](https://code.visualstudio.com/docs/agent-customization/overview.md): Find, create, and manage agent customizations for a session's harness, workspace, and environment in VS Code.
- [Plugins](https://code.visualstudio.com/docs/agent-customization/agent-plugins.md): Find, install, and manage agent plugins from marketplaces in VS Code.
- [Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills.md): Find, adapt, and create Agent Skills in VS Code for reusable workflows with supported agents.
- [Instructions](https://code.visualstudio.com/docs/agent-customization/custom-instructions.md): Create and test custom instructions in VS Code to guide agents with project conventions.
- [Custom Agents](https://code.visualstudio.com/docs/agent-customization/custom-agents.md): Reuse, create, and manage custom agents in VS Code for specialized development roles and workflows.
- [Copilot Connectors](https://code.visualstudio.com/docs/agent-customization/copilot-connectors.md): Connect external services to Copilot without server setup, use their tools, and manage connections.
- [Add and Use MCP Servers](https://code.visualstudio.com/docs/agent-customization/mcp-servers.md): Add MCP servers to Copilot in VS Code and use their tools.
- [Manage MCP Servers](https://code.visualstudio.com/docs/agents/run/manage-mcp-servers.md): Manage MCP servers in Copilot sessions and distinguish runtime controls from editor-managed connections.
- [Hooks](https://code.visualstudio.com/docs/agent-customization/hooks.md): Reuse and configure agent hooks for personal and shared workflows in VS Code.
- [Prompt Files](https://code.visualstudio.com/docs/agent-customization/prompt-files.md): Use prompt files with the deprecated Local harness in VS Code, or migrate workflows to agent skills.
- [Migrate Existing Customizations](https://code.visualstudio.com/docs/agent-customization/migrate-customizations.md): Migrate agent customizations and resolve harness compatibility gaps in VS Code.
- [Cloud Continuity Tutorial](https://code.visualstudio.com/docs/agents/cloud-continuity-tutorial.md): Explore a private repository in a cloud session, then continue the same session from a terminal with Copilot CLI.
- [Remote Agent Sessions](https://code.visualstudio.com/docs/agents/run/remote-agent-sessions.md): Continue agent work from another machine or start tasks on a remote host with VS Code.
- [Cloud Sessions](https://code.visualstudio.com/docs/agents/run/cloud-sandbox-sessions.md): Run and continue cloud sessions from VS Code without keeping your development machine online.
- [Session History](https://code.visualstudio.com/docs/agents/run/sessions/session-history.md): Save, search, and share session history in Visual Studio Code with exports, sync, and privacy controls.
- [Explore a Codebase](https://code.visualstudio.com/docs/agents/guides/explore-a-codebase.md): Explore a codebase with an agent in VS Code, trace a behavior, and verify explanations against source code.
- [Add a Feature](https://code.visualstudio.com/docs/agents/guides/add-a-feature.md): Add a feature to an existing project with an agent in VS Code, from a reviewed plan to a tested change.
- [Fix an API Bug](https://code.visualstudio.com/docs/agents/guides/fix-a-bug-with-agents.md): Fix an API bug with an agent in VS Code, add regression tests, and verify the result.
- [Refactor Safely](https://code.visualstudio.com/docs/agents/guides/refactor-safely.md): Refactor code with an agent in VS Code while preserving behavior through focused changes and regression checks.
- [Add Tests](https://code.visualstudio.com/docs/agents/guides/test-code-with-ai.md): Add and run tests for existing code with AI in Visual Studio Code, then review assertions, failures, and coverage.
- [Test Web Apps](https://code.visualstudio.com/docs/agents/guides/browser-agent-testing-guide.md): Validate a web app with AI browser tools in VS Code, reproduce a defect, and verify the fix.
- [Test-Driven Development](https://code.visualstudio.com/docs/agents/guides/test-driven-development-guide.md): Practice test-driven development with AI in VS Code, using failing tests and review checkpoints.
- [Run Parallel Tasks](https://code.visualstudio.com/docs/agents/guides/delegate-two-tasks.md): Delegate two independent agent tasks in VS Code, review isolated changes, and integrate and test the result.
- [Get Back on Track](https://code.visualstudio.com/docs/agents/guides/get-agent-back-on-track.md): Recover an AI agent session in VS Code by steering requests, restoring checkpoints, and resetting context.
- [Adapt Agents to Your Project](https://code.visualstudio.com/docs/agents/guides/customize-copilot-guide.md): Improve your project's AI guidance with focused instructions, scoped rules, agents, and skills in VS Code.
- [Context Engineering](https://code.visualstudio.com/docs/agents/guides/context-engineering-guide.md): Learn how to implement context engineering using VS Code's built-in AI features.
- [Jupyter Notebooks](https://code.visualstudio.com/docs/agents/guides/notebooks-with-ai.md): Create, edit, run, and analyze Jupyter notebooks with AI in Visual Studio Code.
- [Reduce Credit Usage](https://code.visualstudio.com/docs/agents/guides/optimize-usage.md): Reduce AI credit usage in VS Code with efficient models, scoped tools, and focused context.
- [Prompt Examples](https://code.visualstudio.com/docs/agents/guides/prompt-examples.md): Use chat prompts in VS Code to explore code, build features, refactor, debug, and test.
- [Agents](https://code.visualstudio.com/docs/agents/concepts/agents.md): Understand how agents in VS Code use models, context, and tools to complete coding tasks.
- [How Models Work](https://code.visualstudio.com/docs/agents/concepts/language-models.md): Understand language models, tokens, context limits, and model choices for AI tasks in VS Code.
- [Context](https://code.visualstudio.com/docs/agents/concepts/context.md): Understand AI context, conversation history, instructions, and memory in VS Code.
- [Tools](https://code.visualstudio.com/docs/agents/concepts/tools.md): Understand how tools let AI agents act in VS Code, including built-in, MCP, and extension tools.
- [Sessions and Chats](https://code.visualstudio.com/docs/agents/concepts/sessions.md): Understand sessions and chats in VS Code, and choose when to start a chat, fork, or create a session.
- [Trust & Safety](https://code.visualstudio.com/docs/agents/concepts/trust-and-safety.md): Understand AI limitations, data handling, approvals, and isolation in VS Code.
- [Agent Harnesses](https://code.visualstudio.com/docs/agents/concepts/agent-harnesses.md): Understand agent harnesses, model access, execution environments, and code isolation in VS Code.
- [Agent Customization](https://code.visualstudio.com/docs/agents/concepts/customization.md): Compare agent customization types and understand their scope and behavior in VS Code.
- [Tools and Context](https://code.visualstudio.com/docs/agents/reference/tools-reference.md): Look up tools and context references for AI chat in VS Code.
- [Workspace Context](https://code.visualstudio.com/docs/agents/reference/workspace-context.md): Understand how Copilot agents search workspace code, gather context, and work within indexing and exclusion limits.
- [Settings Reference](https://code.visualstudio.com/docs/agents/reference/ai-settings.md): Configure AI features and agents in Visual Studio Code, including chat, agent sessions, dictation, and accessibility settings.
- [VS Code Pet](https://code.visualstudio.com/docs/agents/reference/chat-pet.md): Customize Blobby, the VS Code pet, with colors, achievements, movement, and chat reactions.
- [Custom Agent File Reference](https://code.visualstudio.com/docs/agents/reference/custom-agent-file-reference.md): Look up custom agent file locations, syntax, fields, and harness compatibility in VS Code.
- [Custom Instructions Reference](https://code.visualstudio.com/docs/agents/reference/custom-instructions-reference.md): Look up custom instruction formats, locations, activation rules, and settings in VS Code.
- [Agent Plugin Authoring Reference](https://code.visualstudio.com/docs/agents/reference/agent-plugin-reference.md): Package skills, agents, MCP servers, hooks, and automation templates with agent plugins in VS Code.
- [MCP Configuration](https://code.visualstudio.com/docs/agents/reference/mcp-configuration.md): Configure MCP servers for the Copilot harness with portable files, authentication, and tool controls.
- [Hooks Reference](https://code.visualstudio.com/docs/agents/reference/hooks-reference.md): Review legacy Local hook schemas when migrating to Copilot in VS Code.
- [OpenTelemetry Monitoring](https://code.visualstudio.com/docs/agents/guides/monitoring-agents.md): Monitor GitHub Copilot agents in VS Code with OpenTelemetry traces, metrics, events, and identity controls.
- [Agent Host Architecture](https://code.visualstudio.com/docs/agents/concepts/agent-host.md): Understand how the VS Code Agent Host manages sessions, execution environments, and connected clients.
- [Troubleshooting](https://code.visualstudio.com/docs/agents/agent-troubleshooting/troubleshooting.md): Diagnose GitHub Copilot and agent issues in Visual Studio Code with targeted checks, logs, and network diagnostics.
- [Debug Chat Interactions](https://code.visualstudio.com/docs/agents/agent-troubleshooting/chat-debug-view.md): Diagnose agent behavior in Visual Studio Code by inspecting requests, context, tool calls, token usage, and agent flows.
- [Diagnose Prompt Caching](https://code.visualstudio.com/docs/agents/agent-troubleshooting/cache-explorer.md): Diagnose prompt cache misses with Cache Explorer in Visual Studio Code to investigate token use and latency.
- [FAQ](https://code.visualstudio.com/docs/agents/agent-troubleshooting/faq.md): Find answers about GitHub Copilot access, usage, chat, agents, inline suggestions, and troubleshooting in Visual Studio Code.

## Editor

- [Voice Interactions](https://code.visualstudio.com/docs/configure/accessibility/voice.md): Use Voice Mode for spoken agent conversations and built-in dictation for speech input in Visual Studio Code.

## Source Control

- [Staging, Commits & Undo](https://code.visualstudio.com/docs/sourcecontrol/staging-commits.md): Review, stage, and commit changes in VS Code, and choose safe ways to undo or discard work.
- [Merge Conflicts](https://code.visualstudio.com/docs/sourcecontrol/merge-conflicts.md): Resolve Git conflicts in VS Code, review the result, and complete or cancel the operation.

## Debugging & Testing

- [Integrated Browser](https://code.visualstudio.com/docs/debugtest/integrated-browser.md): Preview and debug web apps with the integrated browser in VS Code and configure browser behavior.

## Enterprise

- [Manage AI Settings](https://code.visualstudio.com/docs/enterprise/manage-ai-settings.md): Manage enterprise AI controls that affect VS Code and Copilot.

## C++

- [C++ Dev Tools for Copilot](https://code.visualstudio.com/docs/cpp/cpp-devtools.md): Use C++ code understanding and CMake tools to provide Copilot with rich symbol context and knowledge of your build configurations.

## Extension Guides

- [AI Extensibility](https://code.visualstudio.com/api/extension-guides/ai/ai-extensibility-overview.md): Extend AI workflows with plugins, MCP Apps, and tools, or integrate models into VS Code extensions.
- [Language Model Tool](https://code.visualstudio.com/api/extension-guides/ai/tools.md): A guide to creating a language model tool and how to implement tool calling in a chat extension
- [MCP Integration](https://code.visualstudio.com/api/extension-guides/ai/mcp.md): Integrate MCP servers with Copilot across compatible clients, with configuration and editor guidance.
- [Chat Participants (Deprecated)](https://code.visualstudio.com/api/extension-guides/ai/chat.md): Replace deprecated chat participants with agent plugins, MCP tools and Apps, or editor-specific extension tools.
- [Code-Tutor Migration](https://code.visualstudio.com/api/extension-guides/ai/chat-tutorial.md): Migrate a code-tutor chat participant to an agent plugin with skills, MCP tools, and interactive exercises.
- [Language Model](https://code.visualstudio.com/api/extension-guides/ai/language-model.md): A guide to adding AI-powered features to a VS Code extension by using language models and natural language understanding.
- [Language Model Tutorial](https://code.visualstudio.com/api/extension-guides/ai/language-model-tutorial.md): Tutorial that walks you through creating a VS Code extension that uses the Language Model API to generate AI-powered code annotations.
- [Language Model Chat Provider](https://code.visualstudio.com/api/extension-guides/ai/language-model-chat-provider.md): Learn how to implement a LanguageModelChatProvider to contribute custom language models to VS Code's chat experience for extensions.
- [Prompt TSX](https://code.visualstudio.com/api/extension-guides/ai/prompt-tsx.md): A guide for how to build language model prompts using the prompt-tsx library

## Agent Foundations

- [Introduction to agent-first development](https://code.visualstudio.com/learn/foundations/introduction-to-agent-first-development.md): Learn how harness, model, context, tools, and prompt work together for effective agent-first development in VS Code.
- [Your first agent session](https://code.visualstudio.com/learn/foundations/approvals-autonomy-and-context-budget.md): Manage approvals, autonomy, and context budget for coding agents in VS Code, including scoped approvals and compaction.
- [Reviewing and controlling agent changes](https://code.visualstudio.com/learn/foundations/reviewing-and-controlling-agent-changes.md): Review AI-generated changes in VS Code with diff controls, checkpoints, forks, and session steering for safe agent workflows.
- [Agent sessions and where agents run](https://code.visualstudio.com/learn/foundations/agent-sessions-and-where-agents-run.md): Manage agent sessions in VS Code across local, Copilot, and cloud execution modes, and choose the right session target.
- [Debugging agent work](https://code.visualstudio.com/learn/foundations/debugging-and-whats-happening-behind-the-scenes.md): Diagnose agent behavior in VS Code with Agent Debug Logs, Chat Debug view, debug event snapshots, and troubleshooting.
- [Build your first app with agent mode](https://code.visualstudio.com/learn/foundations/build-your-first-app-with-agent-mode.md): Build a URL shortener with agent mode in VS Code using FastAPI, sqlite3, planning, autopilot, review tools, and forking.

## Agent Customizations

- [Why customization matters](https://code.visualstudio.com/learn/customizations/1-why-customization-matter.md): Learn why GitHub Copilot agent customization in VS Code matters, and how to get started with the Agent Customizations view for more consistent AI results.
- [Instructions](https://code.visualstudio.com/learn/customizations/2-instructions.md): Learn how to create and use custom instructions in VS Code to guide GitHub Copilot behavior, enforce coding standards, and get consistent chat results.
- [Skills](https://code.visualstudio.com/learn/customizations/3-skills.md): Learn how to create and use agent skills in VS Code to automate workflows, extend GitHub Copilot capabilities, and reduce repetitive tasks.
- [Custom agent](https://code.visualstudio.com/learn/customizations/4-custom-agent.md): Learn how to create and use custom agents with GitHub Copilot to define AI roles, maintain consistency, and build specialized workflows in VS Code.
- [Hooks](https://code.visualstudio.com/learn/customizations/5-hooks.md): Run hooks at specific points in an agent's workflow in VS Code to automate tasks and validate changes.
- [Prompt files](https://code.visualstudio.com/learn/customizations/6-prompt-files.md): Learn how to create and use reusable prompt files in VS Code to standardize workflows, reduce repetition, and customize GitHub Copilot behavior.
- [Customization Features Explained](https://code.visualstudio.com/learn/customizations/7-customization-features-explained.md): Understand the differences between custom instructions, agent skills, hooks, custom agents, and prompt files in GitHub Copilot using interactive learning with Copilot.
- [Customization Features In Practice](https://code.visualstudio.com/learn/customizations/8-demo.md): "A hands-on demo of GitHub Copilot customization features: custom agents, skills, instructions, prompt files, and hooks working together in a real project."

## Agent Extensions

- [Using tools with agents](https://code.visualstudio.com/learn/agents/1-using-tools-with-agents.md): Practice choosing agent tools, tool sets, approvals, and sandboxing settings for focused AI workflows in VS Code.
- [Extending agents with MCP servers](https://code.visualstudio.com/learn/agents/2-extending-agents-with-mcp-servers.md): Install, use, and configure MCP servers to give agents in VS Code focused external capabilities.
- [Agent plugins](https://code.visualstudio.com/learn/agents/3-agent-plugins.md): Practice installing, reviewing, using, and recommending agent plugins for repeatable AI workflows in VS Code.
- [Using third-party agents in VS Code](https://code.visualstudio.com/learn/agents/4-using-third-party-agents-in-vs-code.md): Start Claude and Codex agent sessions in VS Code and choose local or cloud workflows for coding tasks.
