---
source: skills/plugins/others/skills/vscode-docs/output/llms.txt
extracted_from_fetched_at: 2026-07-07T16:54:39.235283+00:00
curated_at: 2026-07-08
note: >
  This is a curated subset of vscode-docs/output/llms.txt, containing only
  entries related to GitHub Copilot / AI features in VS Code (Chat, Agent
  mode, agent customization, MCP, inline suggestions, etc.). Section headers
  and entry order follow the source file. Entries about the separate Foundry
  Toolkit / "Intelligent Apps" extension (building/deploying custom AI models)
  are intentionally excluded -- that is a different product from GitHub
  Copilot, even though its docs also use "AI" and "Agent" terminology.
  Regenerate/re-review this file with the vscode-copilot-docs-check skill
  whenever vscode-docs/output/llms.txt is refreshed, since it can drift.
---

## Get Started

- [Overview](https://code.visualstudio.com/docs/getstarted/overview): Get started with Visual Studio Code, the open platform for AI agents. Install on Windows, macOS, or Linux and start building with agentic coding, extensions, and a powerful editor.
- [Tutorial](https://code.visualstudio.com/docs/getstarted/getting-started): Get started with agentic coding in Visual Studio Code. Build an app from a prompt with the Agents window and the Chat view, and learn the VS Code basics.

## Source Control

- [Staging & Committing](https://code.visualstudio.com/docs/sourcecontrol/staging-commits): Master Git staging and commits in VS Code with granular file control, AI-powered commit messages, visual diff reviews, and comprehensive change tracking tools.
- [Merge Conflicts](https://code.visualstudio.com/docs/sourcecontrol/merge-conflicts): Learn how to resolve Git merge conflicts in VS Code using inline editor actions, the 3-way merge editor, and AI-assisted resolution.

## Debugging & Testing

- [Integrated Browser](https://code.visualstudio.com/docs/debugtest/integrated-browser): Use the integrated browser in VS Code to preview and debug web apps, navigate to URLs, and add page elements, screenshots, or console logs as context to AI chat.
- [Test-Driven Development](https://code.visualstudio.com/docs/agents/guides/test-driven-development-guide): Learn how to set up a test-driven development (TDD) workflow in VS Code with Copilot and custom agents and instructions.
- [Test Web Apps with Browser Tools](https://code.visualstudio.com/docs/agents/guides/browser-agent-testing-guide): Learn how to use browser agent tools in VS Code to build and automatically test web applications with AI.

## Enterprise

- [AI Settings](https://code.visualstudio.com/docs/enterprise/ai-settings): Learn how to centrally manage AI settings in VS Code for enterprise environments, including agent mode, MCP servers, and tool approvals.

## Advanced Setup

- [GitHub Copilot Setup](https://code.visualstudio.com/docs/setup/copilot): Access your GitHub Copilot subscription and set up GitHub Copilot in Visual Studio.

## Agents

- [Tutorial](https://code.visualstudio.com/docs/agents/agents-tutorial): Get started with different types of agents in VS Code to run tasks locally, in the background, or in the cloud. Hand off work across agents to use what works best for your workflow.
- [Agents Window](https://code.visualstudio.com/docs/agents/agents-window): Use the Agents window in VS Code for an agent-first coding experience where agents and chat are the primary interface to build with AI.
- [Chat View](https://code.visualstudio.com/docs/agents/chat-view): Use the Chat view in VS Code for a code-first experience where agents assist you while you write and edit code in a single workspace.
- [Remote Agent Sessions](https://code.visualstudio.com/docs/agents/remote-agent-sessions): Connect to remote machines via SSH or dev tunnels to run agent sessions, or use the browser-based Agents window to manage sessions from any device.
- [Session Insights](https://code.visualstudio.com/docs/agents/sessions/session-insights): Use chronicle commands in VS Code to generate standup reports, get personalized tips, and query your Copilot session history with natural language.
- [Sync Sessions](https://code.visualstudio.com/docs/agents/sessions/session-sync): Sync your Copilot chat sessions to GitHub for cross-device access, enterprise policy controls, and sharing with teammates.
- [Local Agents](https://code.visualstudio.com/docs/agents/agent-types/local-agents): Learn how to use local agents in VS Code for interactive coding tasks with full access to your workspace, tools, and models.
- [Copilot CLI](https://code.visualstudio.com/docs/agents/agent-types/copilot-cli): Learn how to use Copilot CLI within VS Code for autonomous coding tasks, terminal integration, and isolated development workflows in VS Code.
- [Cloud Agents](https://code.visualstudio.com/docs/agents/agent-types/cloud-agents): Use cloud agents like GitHub Copilot cloud agent in VS Code to autonomously handle coding tasks with automatic pull request generation and team collaboration workflows.
- [Third-Party Agents](https://code.visualstudio.com/docs/agents/agent-types/third-party-agents): Learn how to use third-party agents like Claude Agent and OpenAI Codex for autonomous coding tasks in VS Code, powered by your GitHub Copilot subscription.
- [Approvals & Permissions](https://code.visualstudio.com/docs/agents/approvals): Learn how to manage tool approvals, configure auto-approval, set permission levels, and sandbox agent commands to control agent autonomy in VS Code.
- [Planning](https://code.visualstudio.com/docs/agents/planning): Learn how to use the plan agent for autonomous planning and task management with the todo list in VS Code chat.
- [Memory](https://code.visualstudio.com/docs/agents/memory): Learn how agents in VS Code use the memory tool and Copilot Memory to retain context, learn preferences, and improve over time across conversations.
- [Subagents](https://code.visualstudio.com/docs/agents/subagents): Learn how to use context-isolated subagents in VS Code to delegate complex tasks to autonomous agents within your chat session.
- [Best Practices](https://code.visualstudio.com/docs/agents/best-practices): Best practices for getting the most out of GitHub Copilot in VS Code, from writing prompts to configuring your project for AI.
- [Security](https://code.visualstudio.com/docs/agents/security): Understand security considerations, built-in protections, and best practices when using AI-powered development features like agents and MCP servers in VS Code.

## Agent Customization

- [Overview](https://code.visualstudio.com/docs/agent-customization/overview): Get started customizing AI in VS Code with custom instructions, prompt files, custom agents, MCP servers, and more to align AI responses with your coding practices.
- [Instructions](https://code.visualstudio.com/docs/agent-customization/custom-instructions): Learn how to create custom instructions for GitHub Copilot Chat in VS Code to ensure AI responses match your coding practices, project requirements, and development standards.
- [Agent Skills](https://code.visualstudio.com/docs/agent-customization/agent-skills): Learn how to use Agent Skills in VS Code to teach GitHub Copilot specialized capabilities that work across VS Code, GitHub Copilot CLI, and GitHub Copilot cloud agent.
- [Custom Agents](https://code.visualstudio.com/docs/agent-customization/custom-agents): Learn how to create custom agents (formerly custom chat modes) to tailor AI chat behavior in VS Code for your specific workflows and development scenarios.
- [Language Models](https://code.visualstudio.com/docs/agent-customization/language-models): Configure AI language models in VS Code, change chat and inline models, set thinking effort, and bring your own API key.
- [MCP](https://code.visualstudio.com/docs/agent-customization/mcp-servers): Learn how to add and manage Model Context Protocol (MCP) servers with GitHub Copilot in Visual Studio Code.
- [Hooks](https://code.visualstudio.com/docs/agent-customization/hooks): Learn how to use hooks in VS Code to execute custom shell commands at key lifecycle points during agent sessions for automation, validation, and policy enforcement.
- [Plugins](https://code.visualstudio.com/docs/agent-customization/agent-plugins): Learn how to discover, install, and manage agent plugins in VS Code to extend GitHub Copilot with pre-packaged commands, skills, agents, hooks, and MCP servers.
- [Prompt Files](https://code.visualstudio.com/docs/agent-customization/prompt-files): Learn how to create reusable prompt files for GitHub Copilot Chat in VS Code to standardize common development tasks and improve your coding workflow efficiency.

## Using Chat

- [Overview](https://code.visualstudio.com/docs/chat/chat-overview): Learn how to use chat in VS Code. Access different chat surfaces, send a request, add context, write effective prompts, and review AI-generated changes.
- [Chat Sessions](https://code.visualstudio.com/docs/chat/chat-sessions): Learn how to create and manage chat sessions in Visual Studio Code, including the sessions list, opening chat in editor tabs, separate windows, and using chat session history.
- [Add Context](https://code.visualstudio.com/docs/chat/copilot-chat-context): Learn how to manage context when using AI in VS Code, including workspace indexing, #-mentions for files and symbols, web content references, and custom instructions.
- [Tools](https://code.visualstudio.com/docs/chat/chat-tools): Learn how to use built-in tools, MCP tools, and extension tools to extend chat in VS Code with specialized functionality.
- [Inline Chat](https://code.visualstudio.com/docs/chat/inline-chat): Use Inline Chat in Visual Studio Code to make edits directly in the editor or get command suggestions in the terminal.
- [Review Edits](https://code.visualstudio.com/docs/chat/review-code-edits): Learn how to review and manage AI-generated code edits in Visual Studio Code chat.
- [Checkpoints](https://code.visualstudio.com/docs/chat/chat-checkpoints): Learn how to edit previous chat requests, restore your workspace to earlier states using checkpoints, and undo changes made by chat in Visual Studio Code.
- [Artifacts Panel](https://code.visualstudio.com/docs/chat/chat-artifacts): Learn how to use the artifacts panel in Visual Studio Code to view important resources surfaced by the AI during a chat session.

## Concepts

- [Overview](https://code.visualstudio.com/docs/agents/concepts/overview): Understand how AI works in VS Code, from inline suggestions to autonomous agents, and how language models, context, and tools fit together.
- [Language Models](https://code.visualstudio.com/docs/agents/concepts/language-models): Understand how large language models power AI features in VS Code, including model characteristics, context windows, and model selection.
- [Context](https://code.visualstudio.com/docs/agents/concepts/context): Learn how VS Code assembles context for AI prompts, including workspace indexing, implicit context, explicit references, and context window management.
- [Tools](https://code.visualstudio.com/docs/agents/concepts/tools): Learn about the different types of tools that extend AI agents in VS Code, including built-in tools, MCP servers, and extension tools.
- [Agents](https://code.visualstudio.com/docs/agents/concepts/agents): Learn about agents in VS Code, including the agent loop, agent types, subagents, memory, and planning.
- [Customization](https://code.visualstudio.com/docs/agents/concepts/customization): Learn about the AI agent customization options in VS Code, including instructions, prompt files, custom agents, skills, hooks, and plugins.
- [Trust & Safety](https://code.visualstudio.com/docs/agents/concepts/trust-and-safety): Learn about AI safety controls in VS Code, including agent sandboxing, tool approval, and security considerations for AI-assisted development.

## Guides

- [Prompt Examples](https://code.visualstudio.com/docs/agents/guides/prompt-examples): Discover effective prompt examples for chat in VS Code across different scenarios including code generation, debugging, testing, and working with notebooks.
- [Context Engineering](https://code.visualstudio.com/docs/agents/guides/context-engineering-guide): Learn how to implement context engineering using VS Code's built-in AI features.
- [Optimize AI Credit Usage](https://code.visualstudio.com/docs/agents/guides/optimize-usage): Tips to optimize your AI credit usage in VS Code by choosing efficient models, managing context, and monitoring consumption.
- [Customize AI](https://code.visualstudio.com/docs/agents/guides/customize-copilot-guide): Step-by-step guide to customizing AI in VS Code with instructions, prompt files, custom agents, and skills.
- [Test-Driven Development](https://code.visualstudio.com/docs/agents/guides/test-driven-development-guide): Learn how to set up a test-driven development (TDD) workflow in VS Code with Copilot and custom agents and instructions.
- [Edit Notebooks with AI](https://code.visualstudio.com/docs/agents/guides/notebooks-with-ai): Learn how to use GitHub Copilot in Visual Studio Code to edit Jupyter notebooks with AI.
- [Test with AI](https://code.visualstudio.com/docs/agents/guides/test-with-copilot): Learn how to use GitHub Copilot in Visual Studio Code to write, debug, and fix tests.
- [Test Web Apps with Browser Tools](https://code.visualstudio.com/docs/agents/guides/browser-agent-testing-guide): Learn how to use browser agent tools in VS Code to build and automatically test web applications with AI.
- [Debug with AI](https://code.visualstudio.com/docs/agents/guides/debug-with-copilot): Learn how to use GitHub Copilot in Visual Studio Code to set up debugging configurations and fix issues during debugging.
- [MCP Dev Guide](https://code.visualstudio.com/docs/agents/guides/mcp-developer-guide): A guide for developers building MCP servers for VS Code.
- [OpenTelemetry Monitoring](https://code.visualstudio.com/docs/agents/guides/monitoring-agents): Learn how to monitor GitHub Copilot agent interactions in VS Code with OpenTelemetry traces, metrics, and events.

## Troubleshooting

- [Debug Chat Interactions](https://code.visualstudio.com/docs/agents/agent-troubleshooting/chat-debug-view): Use Agent Logs and the Chat Debug view to inspect AI requests, tool invocations, and agent interactions in Visual Studio Code.
- [Diagnose Prompt Caching](https://code.visualstudio.com/docs/agents/agent-troubleshooting/cache-explorer): Use the Cache Explorer view in Visual Studio Code to diagnose prompt cache misses and reduce token cost and latency in AI chat sessions.
- [Troubleshooting](https://code.visualstudio.com/docs/agents/agent-troubleshooting/troubleshooting): Troubleshoot GitHub Copilot issues in Visual Studio Code with logs, diagnostics, and debugging tools.
- [FAQ](https://code.visualstudio.com/docs/agents/agent-troubleshooting/faq): Frequently asked questions for using GitHub Copilot in Visual Studio Code.

## Reference

- [Cheat Sheet](https://code.visualstudio.com/docs/agents/reference/ai-features-cheat-sheet): Quick reference for AI features in VS Code, including autonomous agents, multi-file editing, inline suggestions, and enterprise controls.
- [Settings Reference](https://code.visualstudio.com/docs/agents/reference/ai-settings): Overview of the configuration settings for AI features and agents in Visual Studio Code.
- [MCP Configuration](https://code.visualstudio.com/docs/agents/reference/mcp-configuration): Reference for MCP server configuration format, commands, and settings in Visual Studio Code.
- [Hooks Reference](https://code.visualstudio.com/docs/agents/reference/hooks-reference): Reference for agent hook configuration properties and per-event input and output schemas in Visual Studio Code, including PreToolUse, PostToolUse, SessionStart, Stop, and more.
- [Workspace Context](https://code.visualstudio.com/docs/agents/reference/workspace-context): Learn how Copilot agents understand your codebase with semantic search, text search, grep, and other tools to gather context for accurate answers.

## Write code

- [Inline Suggestions](https://code.visualstudio.com/docs/editing/ai-powered-suggestions): Get AI-powered inline suggestions from GitHub Copilot in VS Code, including ghost text completions and next edit suggestions.
- [Smart Actions](https://code.visualstudio.com/docs/editing/copilot-smart-actions): Use smart actions in VS Code to get help from AI for common development tasks, such as generating commit messages, renaming symbols, or fixing coding errors.

## C++

- [C++ Dev Tools for Copilot](https://code.visualstudio.com/docs/cpp/cpp-devtools): Use C++ code understanding and CMake tools to provide Copilot with rich symbol context and knowledge of your build configurations.

## Optional > Extension Guides

- [AI Extensibility](https://code.visualstudio.com/api/extension-guides/ai/ai-extensibility-overview): Overview of how to extend the AI features in your Visual Studio Code extension by using the Language Model, Tools, and Chat APIs.
- [Language Model Tool](https://code.visualstudio.com/api/extension-guides/ai/tools): A guide to creating a language model tool and how to implement tool calling in a chat extension
- [MCP Dev Guide](https://code.visualstudio.com/api/extension-guides/ai/mcp): A comprehensive guide for developers building MCP servers that work with Visual Studio Code.
- [Chat Participant](https://code.visualstudio.com/api/extension-guides/ai/chat): A guide to creating an AI extension in Visual Studio Code
- [Chat Tutorial](https://code.visualstudio.com/api/extension-guides/ai/chat-tutorial): Tutorial that walks you through creating a GitHub Copilot chat participant in VS Code by using the Chat API.
- [Language Model](https://code.visualstudio.com/api/extension-guides/ai/language-model): A guide to adding AI-powered features to a VS Code extension by using language models and natural language understanding.
- [Language Model Tutorial](https://code.visualstudio.com/api/extension-guides/ai/language-model-tutorial): Tutorial that walks you through creating a VS Code extension that uses the Language Model API to generate AI-powered code annotations.
- [Language Model Chat Provider](https://code.visualstudio.com/api/extension-guides/ai/language-model-chat-provider): Learn how to implement a LanguageModelChatProvider to contribute custom language models to VS Code's chat experience for extensions.
- [Prompt TSX](https://code.visualstudio.com/api/extension-guides/ai/prompt-tsx): A guide for how to build language model prompts using the prompt-tsx library
