# Tool Wrapper Interface Specifications

## Core Design Principles

All tool wrappers in Instability v3 follow a consistent function-based interface pattern:
- **Functions, not classes** - Each tool is wrapped by a simple function
- **Standardized return formats** - All tools use the v3 standard result format
- **Automatic standardization** - Legacy tools upgraded via `@standardize_tool_output()` decorator
- **Centralized configuration** - Timeouts, servers, and constants from `config.py`
- **Enhanced error handling** - Contextual error messages with actionable suggestions
- **Unified registry** - Automatic tool discovery with rich metadata

## Tool Development Approaches

### Approach 1: Simple Decorator (Recommended for most tools)
```python
from utils import standardize_tool_output
from config import get_timeout

@standardize_tool_output()
def tool_name(
    target: str,
    options: str = "default",
    silent: bool = False
) -> str:
    """
    Execute a tool with automatic standardization.
    
    Args:
        target: Primary target (IP, domain, URL, etc.)
        options: Tool-specific options 
        silent: If True, suppress all output except errors
        
    Returns:
        String result (automatically wrapped in standard format)
    """
    timeout = get_timeout("tool_category")  # Use centralized config
    # Implementation here
    return "tool result"
```

### Approach 2: Full v3 Standard Interface
```python
from core.error_handling import create_network_error, ErrorCode
from utils import create_success_result
from config import get_timeout

def tool_name(
    target: str,
    options: Dict[str, Any] = None,
    silent: bool = False,
    timeout: int = None
) -> Dict[str, Any]:
    """
    Execute a tool with full v3 interface.
    
    Args:
        target: Primary target (IP, domain, URL, etc.)
        options: Tool-specific options as key-value pairs
        silent: If True, suppress all output except errors
        timeout: Override default timeout in seconds
        
    Returns:
        Standardized v3 result dictionary
    """
    start_time = datetime.now()
    if timeout is None:
        timeout = get_timeout("tool_category")
    
    try:
        result = perform_operation(target, options, timeout)
        return create_success_result(
            tool_name="tool_name",
            execution_time=(datetime.now() - start_time).total_seconds(),
            parsed_data=result,
            target=target,
            options_used=options
        )
    except TimeoutError:
        return create_network_error(ErrorCode.TIMEOUT, target=target, timeout=timeout)
    except Exception as e:
        return create_network_error(ErrorCode.CONNECTION_FAILED, target=target)
```

## Tool Categories and Signatures

### 1. Network Diagnostic Tools

#### Basic Network Info
```python
def get_local_ip(interface: str = None, silent: bool = False) -> Dict[str, Any]:
def get_external_ip(timeout: int = 10, silent: bool = False) -> Dict[str, Any]:
def check_interface_status(interface: str = None, silent: bool = False) -> Dict[str, Any]:
```

#### Connectivity Testing
```python
def ping_host(target: str, count: int = 4, timeout: int = 5, silent: bool = False) -> Dict[str, Any]:
def traceroute_host(target: str, max_hops: int = 30, timeout: int = 30, silent: bool = False) -> Dict[str, Any]:
def test_port_connectivity(target: str, port: int, timeout: int = 5, silent: bool = False) -> Dict[str, Any]:
```

#### DNS Testing
```python
def resolve_dns(target: str, record_type: str = "A", server: str = None, timeout: int = 10, silent: bool = False) -> Dict[str, Any]:
def check_dns_servers(servers: List[str] = None, timeout: int = 5, silent: bool = False) -> Dict[str, Any]:
def reverse_dns_lookup(ip: str, timeout: int = 10, silent: bool = False) -> Dict[str, Any]:
```

### 2. Pentesting Tools

#### Network Scanning
```python
def run_nmap_scan(
    target: str,
    scan_type: str = "tcp_syn",
    ports: str = "top-1000", 
    options: Dict[str, Any] = None,
    timeout: int = 300,
    silent: bool = False
) -> Dict[str, Any]:

def run_nmap_service_scan(
    target: str,
    ports: str = None,
    options: Dict[str, Any] = None,
    timeout: int = 600,
    silent: bool = False
) -> Dict[str, Any]:
```

#### Web Discovery
```python
def run_httpx_scan(
    targets: List[str],
    options: Dict[str, Any] = None,
    timeout: int = 300,
    silent: bool = False
) -> Dict[str, Any]:

def run_feroxbuster_scan(
    target: str,
    wordlist: str = None,
    extensions: List[str] = None,
    options: Dict[str, Any] = None,
    timeout: int = 600,
    silent: bool = False
) -> Dict[str, Any]:
```

#### Vulnerability Scanning
```python
def run_nuclei_scan(
    targets: List[str],
    templates: List[str] = None,
    severity: str = "medium,high,critical",
    options: Dict[str, Any] = None,
    timeout: int = 1800,
    silent: bool = False
) -> Dict[str, Any]:
```

#### Exploitation Tools
```python
def run_hydra_attack(
    target: str,
    service: str,
    userlist: str = None,
    passlist: str = None,
    options: Dict[str, Any] = None,
    timeout: int = 1800,
    silent: bool = False
) -> Dict[str, Any]:

def run_sqlmap_scan(
    target: str,
    options: Dict[str, Any] = None,
    timeout: int = 1800,
    silent: bool = False
) -> Dict[str, Any]:
```

## Tool Detection Functions

```python
def detect_tool_installation(tool_name: str) -> Dict[str, Any]:
    """
    Detect if a tool is installed and get its details.
    
    Args:
        tool_name: Name of the tool to detect
        
    Returns:
        {
            "found": bool,
            "path": str or None,
            "version": str or None,
            "install_command": str or None
        }
    """

def get_tool_inventory(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Get complete inventory of all detectable tools.
    
    Args:
        force_refresh: If True, re-scan for tools instead of using cache
        
    Returns:
        Dictionary with tool names as keys and detection results as values
    """
```

## Standard Tool Result Format

All tool functions return a dictionary with this structure:

```python
{
    # Execution metadata
    "success": bool,              # True if tool executed without errors
    "exit_code": int,             # Tool's exit code (0 = success)
    "execution_time": float,      # Time taken in seconds
    "timestamp": str,             # ISO format timestamp
    "tool_name": str,             # Name of the tool executed
    "command_executed": str,      # Actual command that was run
    
    # Output data
    "stdout": str,                # Raw stdout from tool
    "stderr": str,                # Raw stderr from tool
    "parsed_data": Dict[str, Any], # Structured data extracted from output
    
    # Error handling
    "error_type": str or None,    # Type of error if any ("timeout", "not_found", "execution", etc.)
    "error_message": str or None, # Human-readable error description
    
    # Tool-specific metadata
    "target": str or None,        # Target that was scanned/tested
    "options_used": Dict[str, Any], # Actual options passed to tool
}
```

## Example Tool Result

```python
# Successful nmap scan result
{
    "success": True,
    "exit_code": 0,
    "execution_time": 12.34,
    "timestamp": "2024-01-15T10:30:00Z",
    "tool_name": "nmap",
    "command_executed": "nmap -sS -p 1-1000 192.168.1.1",
    
    "stdout": "Starting Nmap 7.94 ...\nNmap scan report for 192.168.1.1\n...",
    "stderr": "",
    "parsed_data": {
        "hosts": [
            {
                "ip": "192.168.1.1",
                "hostname": "router.local",
                "status": "up",
                "ports": [
                    {"port": 22, "state": "open", "service": "ssh"},
                    {"port": 80, "state": "open", "service": "http"}
                ]
            }
        ],
        "scan_stats": {
            "total_hosts": 1,
            "hosts_up": 1,
            "total_ports": 1000
        }
    },
    
    "error_type": None,
    "error_message": None,
    "target": "192.168.1.1",
    "options_used": {"scan_type": "tcp_syn", "ports": "1-1000"}
}

# Failed tool execution result
{
    "success": False,
    "exit_code": 127,
    "execution_time": 0.1,
    "timestamp": "2024-01-15T10:30:00Z",
    "tool_name": "nmap",
    "command_executed": "nmap -sS 192.168.1.1",
    
    "stdout": "",
    "stderr": "nmap: command not found",
    "parsed_data": {},
    
    "error_type": "not_found",
    "error_message": "nmap is not installed or not in PATH",
    "target": "192.168.1.1",
    "options_used": {"scan_type": "tcp_syn"}
}
```

## Enhanced Error Handling

### Error Categories and Codes
Instability v3 uses a structured error taxonomy with contextual messages and actionable suggestions:

**Network Errors** (`ErrorType.NETWORK`):
- `CONNECTION_FAILED` - Failed to establish connection to target
- `TIMEOUT` - Operation timed out after specified duration  
- `DNS_RESOLUTION` - Failed to resolve hostname
- `UNREACHABLE` - Target appears to be unreachable

**System Errors** (`ErrorType.SYSTEM`):
- `TOOL_MISSING` - Required tool not found on system
- `PERMISSION_DENIED` - Insufficient permissions for operation
- `INVALID_PLATFORM` - Operation not supported on this platform

**Input Errors** (`ErrorType.INPUT`):
- `INVALID_TARGET` - Target format is invalid
- `INVALID_PORT` - Port specification is invalid
- `MISSING_PARAMETER` - Required parameter not provided

**Execution Errors** (`ErrorType.EXECUTION`):
- `COMMAND_FAILED` - Command execution failed
- `PARSING_ERROR` - Could not parse tool output
- `UNEXPECTED_ERROR` - Unexpected runtime error

### Error Response Format
```python
{
    "success": False,
    "error": {
        "type": "network",
        "code": "timeout", 
        "message": "Operation timed out after 30s",
        "suggestions": [
            "Check your internet connection",
            "Try increasing timeout value",
            "Verify target is reachable manually"
        ],
        "timestamp": "2024-01-15T10:30:00Z"
    },
    "tool_name": "ping_host",
    "execution_time": 30.0,
    "target": "192.168.1.1"
}
```

## Tool Registry Integration

### Automatic Discovery with get_module_tools()
For full registry integration, add this function to your module:

```python
def get_module_tools():
    from core.tools_registry import ToolMetadata, ParameterInfo, ParameterType, ToolCategory
    
    return {
        "tool_name": ToolMetadata(
            name="tool_name",
            function_name="tool_function",
            module_path="network.my_module",
            description="Tool description for help text",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "target": ParameterInfo(
                    param_type=ParameterType.STRING,
                    required=True,
                    description="Target IP or hostname"
                ),
                "scan_type": ParameterInfo(
                    param_type=ParameterType.STRING,
                    required=False,
                    default="basic",
                    choices=["basic", "comprehensive"],
                    description="Type of scan to perform"
                )
            },
            modes=["manual", "chatbot"],
            aliases=["alt_name", "short_name"],
            examples=[
                "tool_name 192.168.1.1",
                "tool_name example.com comprehensive"
            ]
        )
    }
```

### Registry Usage
```python
from core.tools_registry import get_tool_registry

registry = get_tool_registry()

# Get all available tools
tools = registry.get_available_tools(mode="manual")

# Execute a tool
result = registry.execute_tool("resolve_hostname", {"hostname": "google.com"})

# Get help for a tool
help_text = registry.get_tool_help("resolve_hostname")

# List tools by category
dns_tools = registry.get_available_tools(category=ToolCategory.DNS)
```

## Implementation Guidelines

1. **Use centralized configuration** - Get timeouts, servers, ports from `config.py`
2. **Leverage error handling** - Use appropriate error types and codes from `core.error_handling`
3. **Use subprocess for external tools** - All external commands via subprocess with proper timeout handling
4. **Capture both stdout and stderr** - Always capture both for debugging
5. **Parse output when possible** - Extract structured data from tool output
6. **Handle timeouts gracefully** - Kill processes that exceed timeout
7. **Validate inputs** - Use `ErrorRecovery.validate_target()` and similar helpers
8. **Cross-platform compatibility** - Handle Windows vs Unix differences
9. **Add rich metadata** - Include examples, aliases, and parameter descriptions
10. **Test both approaches** - Ensure tools work with decorator and full interface