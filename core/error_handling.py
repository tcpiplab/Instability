"""
Core Error Handling Module for Instability v3

Provides standardized error types, messages, and recovery strategies
for consistent error handling across all tools and modules.
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum

# Standardized error type taxonomy
class ErrorType(str, Enum):
    """Standard error type categories"""
    NETWORK = "network"
    SYSTEM = "system" 
    INPUT = "input"
    EXECUTION = "execution"
    CONFIGURATION = "configuration"

class ErrorCode(str, Enum):
    """Specific error codes within categories"""
    # Network errors
    CONNECTION_FAILED = "connection_failed"
    TIMEOUT = "timeout"
    DNS_RESOLUTION = "dns_resolution"
    UNREACHABLE = "unreachable"
    
    # System errors
    PERMISSION_DENIED = "permission_denied"
    TOOL_MISSING = "tool_missing"
    INVALID_PLATFORM = "invalid_platform"
    
    # Input errors
    INVALID_TARGET = "invalid_target"
    INVALID_PORT = "invalid_port"
    INVALID_FORMAT = "invalid_format"
    MISSING_PARAMETER = "missing_parameter"
    
    # Execution errors
    COMMAND_FAILED = "command_failed"
    PARSING_ERROR = "parsing_error"
    UNEXPECTED_ERROR = "unexpected_error"
    
    # Configuration errors
    FILE_NOT_FOUND = "file_not_found"
    INVALID_CONFIG = "invalid_config"
    PERMISSION_ERROR = "permission_error"

# Standardized timeout values by operation type
TIMEOUTS = {
    "ping": 5,
    "dns_query": 10,
    "web_request": 15,
    "port_scan": 30,
    "network_discovery": 120,
    "comprehensive_scan": 600,
    "traceroute": 30,
    "nmap_basic": 60,
    "nmap_service": 120,
    "nmap_os": 180
}

# Error message templates with contextual help
ERROR_MESSAGES = {
    f"{ErrorType.NETWORK}.{ErrorCode.TIMEOUT}": {
        "message": "Operation timed out after {timeout}s",
        "suggestions": [
            "Check your internet connection",
            "Try increasing timeout value with appropriate parameter",
            "Verify target is reachable manually (ping/traceroute)",
            "Check if firewall is blocking the connection"
        ]
    },
    f"{ErrorType.NETWORK}.{ErrorCode.CONNECTION_FAILED}": {
        "message": "Failed to establish connection to {target}",
        "suggestions": [
            "Verify target IP/hostname is correct",
            "Check if target service is running",
            "Test basic connectivity with ping first",
            "Check firewall and network configuration"
        ]
    },
    f"{ErrorType.NETWORK}.{ErrorCode.DNS_RESOLUTION}": {
        "message": "Failed to resolve hostname {target}",
        "suggestions": [
            "Check if hostname is spelled correctly",
            "Test DNS resolution with 'nslookup' or 'dig'",
            "Try using IP address instead of hostname",
            "Check DNS server configuration"
        ]
    },
    f"{ErrorType.SYSTEM}.{ErrorCode.TOOL_MISSING}": {
        "message": "Required tool '{tool}' not found on system",
        "suggestions": [
            "Install {tool} using your package manager",
            "Verify {tool} is in your PATH environment variable", 
            "Run 'instability.py test' to check tool availability",
            "Check tool installation documentation"
        ]
    },
    f"{ErrorType.SYSTEM}.{ErrorCode.PERMISSION_DENIED}": {
        "message": "Permission denied for operation: {operation}",
        "suggestions": [
            "Run command with appropriate privileges (sudo)",
            "Check file/directory permissions",
            "Verify user has necessary access rights",
            "For network scans, try TCP connect scan (-sT) instead"
        ]
    },
    f"{ErrorType.INPUT}.{ErrorCode.INVALID_TARGET}": {
        "message": "Invalid target format: {target}",
        "suggestions": [
            "Use valid IP address (e.g., 192.168.1.1)",
            "Use valid hostname (e.g., google.com)",
            "For network ranges, use CIDR notation (e.g., 192.168.1.0/24)",
            "Check target format requirements in tool documentation"
        ]
    },
    f"{ErrorType.INPUT}.{ErrorCode.INVALID_PORT}": {
        "message": "Invalid port specification: {port}",
        "suggestions": [
            "Use port number between 1-65535",
            "Use port ranges like '80,443' or '1-1000'",
            "Check port format documentation for the specific tool"
        ]
    },
    f"{ErrorType.EXECUTION}.{ErrorCode.COMMAND_FAILED}": {
        "message": "Command execution failed: {command}",
        "suggestions": [
            "Check command syntax and parameters",
            "Verify all required tools are installed",
            "Run command manually to debug issues",
            "Check system logs for more details"
        ]
    }
}

def create_error_response(
    error_type: ErrorType,
    error_code: ErrorCode,
    message: str = None,
    details: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[str]] = None,
    tool_name: str = None,
    execution_time: float = 0.0,
    target: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create standardized error response with helpful context and suggestions.
    
    Args:
        error_type: Category of error (network, system, input, execution, configuration)
        error_code: Specific error code within the category
        message: Custom error message (will use template if not provided)
        details: Additional error details dictionary
        suggestions: Custom suggestions list (will use defaults if not provided)
        tool_name: Name of the tool that encountered the error
        execution_time: Time spent before error occurred
        target: Target that was being processed when error occurred
        **kwargs: Additional context for message formatting
        
    Returns:
        Standardized error response dictionary
    """
    error_key = f"{error_type}.{error_code}"
    template = ERROR_MESSAGES.get(error_key, {})
    
    # Use template message if none provided
    if message is None:
        message = template.get("message", f"Unknown error: {error_code}")
        # Format message with provided kwargs
        try:
            message = message.format(target=target, tool_name=tool_name, **kwargs)
        except KeyError:
            # If formatting fails, use message as-is
            pass
    
    # Use template suggestions if none provided
    if suggestions is None:
        suggestions = template.get("suggestions", [])
        # Format suggestions with provided kwargs
        formatted_suggestions = []
        for suggestion in suggestions:
            try:
                formatted_suggestions.append(suggestion.format(target=target, tool_name=tool_name, **kwargs))
            except KeyError:
                formatted_suggestions.append(suggestion)
        suggestions = formatted_suggestions
    
    return {
        "success": False,
        "error": {
            "type": error_type.value,
            "code": error_code.value,
            "message": message,
            "details": details or {},
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        },
        "tool_name": tool_name,
        "execution_time": execution_time,
        "target": target,
        "command_executed": details.get("command") if details else "",
        "stdout": "",
        "stderr": details.get("stderr", "") if details else "",
        "parsed_data": {},
        "error_type": error_type.value,
        "error_message": message,
        "exit_code": details.get("exit_code", 1) if details else 1,
        "options_used": details.get("options", {}) if details else {},
        "timestamp": datetime.now().isoformat()
    }

def get_timeout(operation_type: str, default: int = 30) -> int:
    """
    Get standardized timeout value for operation type.
    
    Args:
        operation_type: Type of operation (ping, dns_query, web_request, etc.)
        default: Default timeout if operation type not found
        
    Returns:
        Timeout value in seconds
    """
    return TIMEOUTS.get(operation_type, default)

class ErrorRecovery:
    """Automatic error recovery strategies and utilities"""
    
    @staticmethod
    def retry_with_backoff(
        operation: Callable,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ) -> Any:
        """
        Retry operation with exponential backoff.
        
        Args:
            operation: Function to retry
            max_attempts: Maximum number of attempts
            base_delay: Initial delay between attempts
            backoff_factor: Multiplier for delay on each attempt
            exceptions: Tuple of exceptions to catch and retry
            
        Returns:
            Result of successful operation
            
        Raises:
            Last exception if all attempts fail
        """
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return operation()
            except exceptions as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    delay = base_delay * (backoff_factor ** attempt)
                    time.sleep(delay)
                    continue
                raise last_exception
    
    @staticmethod
    def find_available_tool(primary_tool: str, fallback_tools: List[str]) -> Optional[str]:
        """
        Find the first available tool from a list of options.
        
        Args:
            primary_tool: Preferred tool to try first
            fallback_tools: List of fallback tools to try
            
        Returns:
            Name of first available tool, or None if none found
        """
        import subprocess
        
        for tool in [primary_tool] + fallback_tools:
            try:
                # Check if tool is available in PATH
                subprocess.run(["which", tool], capture_output=True, check=True)
                return tool
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        return None
    
    @staticmethod
    def validate_target(target: str) -> tuple[bool, Optional[str]]:
        """
        Validate if target is a valid IP address or hostname.
        
        Args:
            target: Target to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        import re
        import socket
        
        if not target or not isinstance(target, str):
            return False, "Target must be a non-empty string"
        
        # Check if it's a valid IP address
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if re.match(ip_pattern, target):
            return True, None
        
        # Check if it's a valid hostname
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        if re.match(hostname_pattern, target) and len(target) <= 253:
            return True, None
        
        # Check if it's a valid CIDR notation
        cidr_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/(?:[0-9]|[1-2][0-9]|3[0-2])$'
        if re.match(cidr_pattern, target):
            return True, None
        
        return False, f"Invalid target format: {target}"
    
    @staticmethod
    def validate_port(port: Union[str, int]) -> tuple[bool, Optional[str]]:
        """
        Validate port number or port range.
        
        Args:
            port: Port number, range, or comma-separated list
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if isinstance(port, int):
            if 1 <= port <= 65535:
                return True, None
            return False, f"Port {port} out of valid range (1-65535)"
        
        if not isinstance(port, str):
            return False, "Port must be a number or string"
        
        # Handle comma-separated ports
        for port_spec in port.split(','):
            port_spec = port_spec.strip()
            
            # Handle port ranges
            if '-' in port_spec:
                try:
                    start, end = map(int, port_spec.split('-', 1))
                    if not (1 <= start <= 65535 and 1 <= end <= 65535 and start <= end):
                        return False, f"Invalid port range: {port_spec}"
                except ValueError:
                    return False, f"Invalid port range format: {port_spec}"
            else:
                # Single port
                try:
                    port_num = int(port_spec)
                    if not (1 <= port_num <= 65535):
                        return False, f"Port {port_num} out of valid range (1-65535)"
                except ValueError:
                    return False, f"Invalid port number: {port_spec}"
        
        return True, None

def create_network_error(error_code: ErrorCode, target: str = None, **kwargs) -> Dict[str, Any]:
    """Helper for creating network-related errors"""
    return create_error_response(ErrorType.NETWORK, error_code, target=target, **kwargs)

def create_system_error(error_code: ErrorCode, **kwargs) -> Dict[str, Any]:
    """Helper for creating system-related errors"""
    return create_error_response(ErrorType.SYSTEM, error_code, **kwargs)

def create_input_error(error_code: ErrorCode, **kwargs) -> Dict[str, Any]:
    """Helper for creating input validation errors"""
    return create_error_response(ErrorType.INPUT, error_code, **kwargs)

def create_execution_error(error_code: ErrorCode, **kwargs) -> Dict[str, Any]:
    """Helper for creating execution-related errors"""
    return create_error_response(ErrorType.EXECUTION, error_code, **kwargs)