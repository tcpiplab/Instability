"""
Authentication middleware for MCP server.

Provides API key authentication for MCP server endpoints to secure access
to pentesting tools and chatbot functionality.
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import secrets
import json

from config import MCP_AUTH_ENABLED, MCP_API_KEY, MCP_AUTH_HEADER


class MCPAuthenticator:
    """Handles authentication for MCP server requests"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.auth_enabled = MCP_AUTH_ENABLED
        self.api_key = MCP_API_KEY
        self.auth_header = MCP_AUTH_HEADER
        
        # Initialize authentication if enabled
        if self.auth_enabled:
            self._validate_auth_config()
    
    def _validate_auth_config(self):
        """Validate authentication configuration"""
        if not self.api_key:
            self.logger.error("MCP authentication is enabled but no API key is configured")
            raise ValueError("MCP_API_KEY environment variable is required when authentication is enabled")
        
        if len(self.api_key) < 32:
            self.logger.warning("API key is shorter than recommended minimum of 32 characters")
        
        self.logger.info(f"MCP authentication enabled with header: {self.auth_header}")
    
    def authenticate_request(self, headers: Dict[str, str]) -> Tuple[bool, Optional[str]]:
        """
        Authenticate an incoming MCP request.
        
        Args:
            headers: Request headers dictionary
            
        Returns:
            Tuple of (is_authenticated, error_message)
        """
        if not self.auth_enabled:
            return True, None
        
        # Check for API key in headers
        provided_key = headers.get(self.auth_header)
        if not provided_key:
            return False, f"Missing authentication header: {self.auth_header}"
        
        # Validate API key
        if not self._validate_api_key(provided_key):
            return False, "Invalid API key"
        
        self.logger.info("MCP request authenticated successfully")
        return True, None
    
    def _validate_api_key(self, provided_key: str) -> bool:
        """
        Validate the provided API key against the configured key.
        
        Args:
            provided_key: API key from request
            
        Returns:
            True if valid, False otherwise
        """
        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(provided_key, self.api_key)
    
    def generate_api_key(self, length: int = 64) -> str:
        """
        Generate a cryptographically secure API key.
        
        Args:
            length: Length of the API key to generate
            
        Returns:
            Hex-encoded API key
        """
        return secrets.token_hex(length // 2)
    
    def get_auth_info(self) -> Dict[str, Any]:
        """
        Get authentication configuration information.
        
        Returns:
            Dictionary with authentication status and configuration
        """
        return {
            "auth_enabled": self.auth_enabled,
            "auth_header": self.auth_header,
            "api_key_configured": bool(self.api_key),
            "api_key_length": len(self.api_key) if self.api_key else 0
        }


class MCPAuthError(Exception):
    """Exception raised for MCP authentication errors"""
    pass


def create_auth_error_response(message: str) -> Dict[str, Any]:
    """
    Create a standardized authentication error response.
    
    Args:
        message: Error message to include
        
    Returns:
        Error response dictionary
    """
    return {
        "error": "authentication_failed",
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "requires_auth": True
    }


def setup_mcp_auth() -> MCPAuthenticator:
    """
    Set up MCP authentication system.
    
    Returns:
        Configured MCPAuthenticator instance
    """
    return MCPAuthenticator()


def generate_new_api_key() -> str:
    """
    Generate a new API key for MCP authentication.
    
    Returns:
        New API key string
    """
    authenticator = MCPAuthenticator()
    return authenticator.generate_api_key()


def print_auth_setup_instructions():
    """Print instructions for setting up MCP authentication"""
    new_key = generate_new_api_key()
    
    print("\n" + "="*60)
    print("MCP SERVER AUTHENTICATION SETUP")
    print("="*60)
    print("\n1. Generate and set your API key:")
    print(f"   export MCP_API_KEY='{new_key}'")
    print("\n2. Enable authentication (optional, enabled by default):")
    print("   export MCP_AUTH_ENABLED=true")
    print("\n3. Configure Claude Desktop with your API key:")
    print("   Add the following to your Claude Desktop MCP configuration:")
    print('   "authorization_token": "' + new_key + '"')
    print("\n4. Restart the MCP server for changes to take effect")
    print("\n" + "="*60)
    print("SECURITY NOTES:")
    print("- Store your API key securely")
    print("- Never commit API keys to version control")
    print("- Rotate keys regularly")
    print("- Use environment variables for configuration")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Generate setup instructions when run directly
    print_auth_setup_instructions()