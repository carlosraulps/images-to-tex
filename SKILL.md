---
name: Images to TeX Assistant
description: An Agent Skill providing tools to convert images of textbooks, handwritten equations, and notes into strictly separated Semantic Document layers (Base Content vs. Human Annotations) formatted as LaTeX or Markdown.
---

# Images to TeX Agent Skill

This skill exposes a specialized MCP server for AI Agents to interact with visual data precisely and predictably. It acts as an advanced semantic document parser that uses OCR pipelines and localized Google Gemini models.

## Agent Instructions

When you invoke this capability:

1. Always verify the path string maps to an existing file before submitting it to the tool.
2. Call the tool using explicit definitions. If a JSON schema error occurs (`InputValidationError`), analyze the `details` attribute to identify what constraints failed, self-correct, and invoke it again.
3. The server uses structural stratification. It will return a strictly typed JSON output payload containing two sections: `base_latex_md` for core printed text, and `annotations_metadata` categorizing human additions explicitly. You must parse this return string if you need specific details.

## Tool Contracts & Schemas

The following tools are available to the Agent through this skill's MCP server:

### `convert_image_to_latex`

Converts and processes an academic/mathematical image file.

**Arguments:**

- `image_path` (string): MUST be an absolute file path mapping cleanly to a valid `.jpg`, `.png`, or similar image containing text/math.
- `mode` (string, Optional): The textual mode you require. MUST be exactly one of `["latex", "markdown", "both"]`. Defaults to `latex`.

**Error Handling / Fallbacks:**
If the underlying service encounters faults, it will gracefully catch them and return a standard Error JSON payload formatted as:

```json
{
  "error": "ErrorType",
  "details": "Explanation of the failure."
}
```

If you encounter this payload, DO NOT PANIC. Parse the error visually, adjust the `image_path` or `mode`, and invoke the interface again.

## Available Modules

- **Core Server Interface:** `python -m src.interfaces.mcp_server` (Running this sets up the stdio MCP bridge).
- **Core CLI Usage:** `python -m src.interfaces.cli /path/to/project` (Running the module directly locally).
