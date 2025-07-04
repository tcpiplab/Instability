# JSON Schema Validation Bug in Instability MCP Server

## Problem Description

The Instability MCP server is failing JSON Schema validation in VS Code's GitHub Copilot extension due to improperly defined array parameters in tool schemas. The error specifically mentions the `test_dns_servers` tool, but this issue likely affects multiple tools in the server.

The error message indicates: "Error: tool parameters array type must have items. Please open a Github issue for the MCP server or extension which provides this tool"

## Root Cause

In JSON Schema specification, when a parameter is defined with `"type": "array"`, it must also include an `items` property that defines the schema for the array elements. The current tool definitions are missing this required property.

## Current Broken Schema Example

The current schema likely looks like this:

```json
"servers": {
  "description": "List of DNS server IPs (uses defaults if None)",
  "type": "array"
}
```

## Required Fixed Schema Example

The schema should be corrected to:

```json
"servers": {
  "description": "List of DNS server IPs (uses defaults if None)", 
  "type": "array",
  "items": {
    "type": "string"
  }
}
```

## Tools That Need Fixing

Based on the function signatures visible in the codebase, the following tools likely have array parameters that need the `items` property added:

- `test_dns_servers` - `servers` parameter
- `check_dns_propagation` - `servers` parameter  
- `check_multiple_endpoints` - `urls` parameter
- `network_discovery` - may have array parameters
- `comprehensive_scan` - may have array parameters
- Any other tools with array-type parameters

## How to Fix

1. **Locate tool definitions**: Find where the JSON schemas for tool parameters are defined in the codebase. This is typically in the MCP server's tool registration or schema definition files.

2. **Identify array parameters**: Look for any parameter definitions that have `"type": "array"` but are missing the `items` property.

3. **Add items schema**: For each array parameter, add an appropriate `items` property. Most will likely be arrays of strings, so use `{"type": "string"}`, but some might be arrays of objects or other types.

4. **Common item types**:
   - For DNS servers, URLs, hostnames: `{"type": "string"}`
   - For port numbers: `{"type": "integer"}`
   - For boolean flags: `{"type": "boolean"}`
   - For complex objects: `{"type": "object", "properties": {...}}`

## Example Fix Pattern

Replace patterns like this:
```json
"parameter_name": {
  "description": "Some description",
  "type": "array"
}
```

With patterns like this:
```json
"parameter_name": {
  "description": "Some description", 
  "type": "array",
  "items": {
    "type": "string"
  }
}
```

## Validation

After making changes, test the MCP server with VS Code's GitHub Copilot extension to ensure the validation errors are resolved. The server should load successfully and tools should be callable without schema validation failures.

## Impact

This bug prevents the MCP server from working properly with VS Code's GitHub Copilot extension, which enforces stricter JSON Schema validation than some other MCP clients. Fixing this ensures compatibility across different MCP client implementations. For example, the Instability MCP server works just fine with Claude Desktop, which is known to be more lenient with JSON Schema validation.