#!/usr/bin/env python3
"""
Setup script for MCP server authentication.

This script helps configure API key authentication for the Instability MCP server.
Run this script to generate API keys and set up authentication configuration.
"""

import os
import json
import secrets
from pathlib import Path
from instability_mcp.auth import MCPAuthenticator


def generate_api_key(length: int = 64) -> str:
    """Generate a cryptographically secure API key."""
    return secrets.token_hex(length // 2)


def create_env_file(api_key: str, auth_enabled: bool = True):
    """Create or update .env file with MCP authentication settings."""
    env_file = Path(".env")
    
    # Read existing .env file if it exists
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Update with new MCP settings
    env_vars['MCP_AUTH_ENABLED'] = 'true' if auth_enabled else 'false'
    env_vars['MCP_API_KEY'] = api_key
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.write("# MCP Server Authentication Configuration\n")
        f.write(f"MCP_AUTH_ENABLED={env_vars['MCP_AUTH_ENABLED']}\n")
        f.write(f"MCP_API_KEY={env_vars['MCP_API_KEY']}\n")
        f.write("\n# Other environment variables\n")
        for key, value in env_vars.items():
            if not key.startswith('MCP_'):
                f.write(f"{key}={value}\n")
    
    return env_file


def create_claude_desktop_config(api_key: str) -> dict:
    """Create Claude Desktop MCP configuration with authentication."""
    config = {
        "mcpServers": {
            "instability-chatbot": {
                "command": "python",
                "args": [str(Path.cwd() / "mcp_server.py")],
                "env": {
                    "MCP_AUTH_ENABLED": "true",
                    "MCP_API_KEY": api_key
                }
            }
        }
    }
    return config


def print_setup_instructions(api_key: str, env_file: Path):
    """Print setup instructions for the user."""
    print("\n" + "="*70)
    print("MCP SERVER AUTHENTICATION SETUP COMPLETE")
    print("="*70)
    
    print(f"\n📁 Configuration file created: {env_file}")
    print(f"🔑 Generated API key: {api_key}")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Start the MCP server:")
    print("   python mcp_server.py")
    
    print("\n2. Configure Claude Desktop:")
    print("   Add this to your Claude Desktop MCP configuration:")
    
    config = create_claude_desktop_config(api_key)
    print(json.dumps(config, indent=2))
    
    print("\n3. Test the authentication:")
    print("   The server will now require the API key for all requests")
    
    print("\n⚠️  SECURITY REMINDERS:")
    print("• Keep your API key secure and don't share it")
    print("• Never commit .env files to version control")
    print("• Add .env to your .gitignore file")
    print("• Rotate your API key regularly")
    
    print("\n📋 AUTHENTICATION STATUS:")
    try:
        authenticator = MCPAuthenticator()
        auth_info = authenticator.get_auth_info()
        print(f"• Authentication enabled: {auth_info['auth_enabled']}")
        print(f"• API key configured: {auth_info['api_key_configured']}")
        print(f"• API key length: {auth_info['api_key_length']} characters")
    except Exception as e:
        print(f"• Status check failed: {e}")
    
    print("\n" + "="*70)


def main():
    """Main setup function."""
    print("🔐 Setting up MCP Server Authentication...")
    
    # Generate new API key
    api_key = generate_api_key()
    
    # Create .env file
    env_file = create_env_file(api_key)
    
    # Create .gitignore entry for .env
    gitignore_path = Path(".gitignore")
    gitignore_content = ""
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
    
    if ".env" not in gitignore_content:
        with open(gitignore_path, 'a') as f:
            f.write("\n# Environment variables\n.env\n")
    
    # Print setup instructions
    print_setup_instructions(api_key, env_file)


if __name__ == "__main__":
    main()