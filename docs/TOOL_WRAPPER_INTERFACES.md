# Tool Wrapper Interface Specifications

## Core Design Principles

All tool wrappers follow a consistent function-based interface pattern:
- **Functions, not classes** - Each tool is wrapped by a simple function
- **Standardized signatures** - Consistent parameter and return patterns
- **Plain data structures** - Dictionaries and lists, no custom objects
- **Graceful error handling** - Tools should never crash the chatbot

## Standard Tool Function Signature

```python
def tool_name(
    target: str = None,
    options: Dict[str, Any] = None,
    silent: bool = False,
    timeout: int = None
) -> Dict[str, Any]:
    """
    Execute a tool with standardized interface.
    
    Args:
        target: Primary target (IP, domain, URL, etc.)
        options: Tool-specific options as key-value pairs
        silent: If True, suppress all output except errors
        timeout: Override default timeout in seconds
        
    Returns:
        Standardized result dictionary (see TOOL_RESULT_FORMAT below)
    """
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

## Error Types

Standard error types for consistent error handling:

- `"not_found"` - Tool not installed or not in PATH
- `"timeout"` - Tool execution exceeded timeout
- `"execution"` - Tool ran but returned non-zero exit code
- `"parsing"` - Tool ran successfully but output couldn't be parsed
- `"permission"` - Insufficient permissions to run tool
- `"network"` - Network connectivity issues
- `"invalid_target"` - Target format is invalid
- `"invalid_options"` - Tool options are invalid

## Implementation Guidelines

1. **Use subprocess for external tools** - All external commands via subprocess with proper timeout handling
2. **Capture both stdout and stderr** - Always capture both for debugging
3. **Parse output when possible** - Extract structured data from tool output
4. **Handle timeouts gracefully** - Kill processes that exceed timeout
5. **Validate inputs** - Check targets and options before execution
6. **Log command execution** - Always log the exact command being run
7. **Cross-platform compatibility** - Handle Windows vs Unix differences