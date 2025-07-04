# MCP Server Authentication

This document explains how to set up authentication for the Instability MCP server to secure access to pentesting tools and chatbot functionality.

## Quick Setup

1. **Generate API Key and Configuration**:
   ```bash
   python setup_mcp_auth.py
   ```

2. **Configure Claude Desktop**:
   - Copy the generated configuration to your Claude Desktop MCP settings
   - The configuration will include the API key for authentication

3. **Start the MCP Server**:
   ```bash
   python mcp_server.py
   ```

## Authentication Methods

### Environment Variable Authentication (Recommended)

The MCP server uses environment variables for authentication configuration:

- `MCP_AUTH_ENABLED`: Set to `true` to enable authentication (default: `true`)
- `MCP_API_KEY`: Your secure API key (required when authentication is enabled)

### Claude Desktop Configuration

Add this to your Claude Desktop MCP configuration file:

```json
{
  "mcpServers": {
    "instability-chatbot": {
      "command": "python",
      "args": ["/full/path/to/instability/mcp_server.py"],
      "env": {
        "MCP_AUTH_ENABLED": "true",
        "MCP_API_KEY": "your-generated-api-key-here"
      }
    }
  }
}
```

## Manual Configuration

### 1. Create .env File

Create a `.env` file in your project root:

```env
MCP_AUTH_ENABLED=true
MCP_API_KEY=your-secure-api-key-here
```

### 2. Generate API Key

You can generate a secure API key using Python:

```python
import secrets
api_key = secrets.token_hex(32)  # 64-character hex string
print(f"Generated API Key: {api_key}")
```

### 3. Configure Claude Desktop

Update your Claude Desktop configuration with the API key in the `env` section.

## Security Features

### API Key Security
- Uses cryptographically secure random generation
- Constant-time comparison to prevent timing attacks
- Configurable key length (default: 64 characters)

### Authentication Flow
1. MCP server starts with authentication enabled
2. Claude Desktop provides API key via environment variables
3. Server validates API key before processing requests
4. Invalid/missing keys result in authentication errors

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_AUTH_ENABLED` | `true` | Enable/disable authentication |
| `MCP_API_KEY` | `""` | API key for authentication |
| `MCP_AUTH_HEADER` | `X-API-Key` | Header name for API key (for future HTTP support) |

### Authentication Status

Check authentication status programmatically:

```python
from instability_mcp.auth import MCPAuthenticator

auth = MCPAuthenticator()
status = auth.get_auth_info()
print(f"Auth enabled: {status['auth_enabled']}")
print(f"API key configured: {status['api_key_configured']}")
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check that `MCP_API_KEY` is set correctly
   - Verify the API key matches between server and Claude Desktop

2. **Server Won't Start**
   - Ensure `MCP_API_KEY` is configured when authentication is enabled
   - Check for typos in environment variable names

3. **Claude Desktop Connection Issues**
   - Verify the path to `mcp_server.py` is correct
   - Check that environment variables are properly set in Claude Desktop config

### Debug Mode

Enable debug logging to troubleshoot authentication issues:

```bash
python mcp_server.py --log-level DEBUG
```

## Security Best Practices

1. **Key Management**
   - Generate unique API keys for each deployment
   - Store keys securely (never in code or version control)
   - Rotate keys regularly

2. **Environment Security**
   - Use `.env` files for local development
   - Add `.env` to your `.gitignore`
   - Use secure environment variable management in production

3. **Access Control**
   - Only share API keys with authorized users
   - Monitor authentication logs for suspicious activity
   - Implement key rotation policies

## Future Enhancements

The current implementation provides basic API key authentication. Future versions may include:

- OAuth 2.1 support (MCP specification standard)
- Role-based access control
- Session management
- Rate limiting
- Audit logging

## Support

If you encounter issues with authentication:

1. Check this documentation
2. Review the authentication logs
3. Verify your configuration matches the examples
4. Test with a fresh API key

For security concerns, ensure you follow all best practices and keep your API keys secure.