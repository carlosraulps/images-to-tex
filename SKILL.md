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

### `process_document`

Converts and processes an academic/mathematical PDF or image directory into LaTeX or Markdown.

**Arguments:**

- `document_path` (string): MUST be an absolute file path mapping cleanly to a valid `.pdf` or directory containing images.
- `mode` (string, Optional): The textual mode you require. MUST be exactly one of `["latex", "markdown", "both"]`. Defaults to `latex`.
- `threshold_pages` (integer, Optional): Page count to trigger background processing. Defaults to 50.

**Behavior:**

- **Synchronous Path:** If the document has fewer pages than `threshold_pages`, the tool processes all pages synchronously utilizing Gemini API **Context Caching** to reduce token costs and returns the extracted content immediately.
- **Asynchronous Path (Batch API):** If the document is massive, the system acts as a traffic controller and routes the file to the Gemini Batch API. It will immediately return:

```json
{
  "status": "processing_background",
  "job_id": "batch_job_12345",
  "message": "The document is very large and has been queued for background processing..."
}
```

### `check_document_status`

Checks the status of an asynchronous background job triggered by `process_document`.

**Arguments:**

- `job_id` (string): The Gemini Batch API job ID to check.

**Error Handling / Fallbacks:**
If the underlying service encounters faults (e.g., input validation failures), it will gracefully catch them and return a standard Error JSON:

```json
{
  "error": "InputValidationError",
  "details": "Explanation of the failure."
}
```

If you encounter this payload, DO NOT PANIC. Parse the error visually, adjust the arguments, and invoke the interface again.

## Available Modules

- **Core Server Interface:** `python -m src.interfaces.mcp_server` (Running this sets up the stdio MCP bridge).
- **Core CLI Usage:** `python -m src.interfaces.cli /path/to/project` (Running the module directly locally).
