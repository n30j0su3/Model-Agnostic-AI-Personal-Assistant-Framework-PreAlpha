---
id: mcp-builder
name: MCP Builder
description: Guides creation of MCP servers with strong tool design, schemas, and evaluation practices.
category: core
type: core
version: 1.0.0
license: MIT
metadata:
  author: FreakingJSON
  source: OBSOLETE/migration
compatibility: [OpenCode, Claude, Gemini, Codex]
---

# MCP Builder Skill

Build high-quality MCP (Model Context Protocol) servers that expose reliable tools for LLMs.

## Instructions

### 1. Planning

- Balance full API coverage with workflow tools.
- Use descriptive tool names with consistent prefixes (e.g. github_create_issue).
- Keep tool descriptions concise and actionable.
- Design outputs that are focused, paginated, and easy to parse.
- Provide actionable error messages with next steps.

### 2. Architecture

- Prefer TypeScript with the MCP SDK when possible.
- Use streamable HTTP for remote servers and stdio for local servers.
- Define shared utilities: auth, error handling, pagination, response formatters.

### 3. Tool Design

- Define input schemas (Zod or Pydantic) with constraints and examples.
- Define output schemas when possible for structured results.
- Include annotations: readOnlyHint, destructiveHint, idempotentHint, openWorldHint.
- Return both text and structured content when supported.

### 4. Implementation

- Use async I/O and consistent error handling.
- Ensure pagination on list endpoints.
- Keep tools atomic and predictable.

### 5. Review and Test

- Compile/build the server and run basic checks.
- Test with MCP Inspector or client smoke tests.
- Verify tool discoverability and error paths.

### 6. Evaluation

- Create 10 realistic, read-only evaluation questions.
- Ensure each question is verifiable and stable.
- Use a simple XML format with qa pairs.

## References

- MCP spec sitemap: https://modelcontextprotocol.io/sitemap.xml
- MCP TS SDK: https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/README.md
- MCP Python SDK: https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/README.md

## Output Format

- Provide a build plan, tool list, schemas, and testing checklist.

## Supported Commands

- "Design an MCP server for: <service>"
- "Draft tool schemas for: <api>"
