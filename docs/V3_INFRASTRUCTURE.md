# Instability v3 Infrastructure Documentation

This document describes the enhanced infrastructure components added to Instability v3 for improved maintainability, consistency, and extensibility.

## Infrastructure Components

### 1. Unified Tool Registration System (`core/tools_registry.py`)

**Purpose**: Centralized registry for all tools with automatic discovery and unified execution interface.

**Key Features**:
- **Automatic tool discovery** from modules via `get_module_tools()` functions
- **Plugin-style architecture** for easy tool addition
- **Rich metadata support** with parameters, descriptions, examples, and aliases
- **Mode-aware tool availability** (manual vs chatbot modes)
- **External tool integration** with tool detector
- **Unified execution interface** with consistent parameter validation

**Usage**:
```python
from core.tools_registry import get_tool_registry

registry = get_tool_registry()
tools = registry.get_available_tools(mode="manual")
result = registry.execute_tool("resolve_hostname", {"hostname": "google.com"})
help_text = registry.get_tool_help("resolve_hostname")
```

### 2. Centralized Error Handling (`core/error_handling.py`)

**Purpose**: Standardized error types, messages, and recovery strategies for consistent error handling.

**Key Features**:
- **5 error categories**: Network, System, Input, Execution, Configuration
- **16 specific error codes** with contextual messages
- **Actionable suggestions** for troubleshooting
- **Template-based error messages** with parameter formatting
- **Input validation helpers** for targets, ports, etc.
- **Retry strategies** with exponential backoff

**Usage**:
```python
from core.error_handling import create_error_response, ErrorType, ErrorCode, ErrorRecovery

# Create standardized error
error = create_error_response(
    ErrorType.NETWORK, 
    ErrorCode.TIMEOUT,
    tool_name="ping_host",
    target="192.168.1.1",
    timeout=10
)

# Validate input
is_valid, error_msg = ErrorRecovery.validate_target("192.168.1.1")

# Get timeout from configuration
timeout = get_timeout("nmap", "comprehensive")
```

### 3. Centralized Configuration Management (`config.py`)

**Purpose**: Single source of truth for all configuration constants and settings.

**Enhanced Configuration Categories**:
- **Network settings**: DNS servers, timeouts, test targets, port specifications
- **Tool-specific settings**: nmap timeouts/timing, DNS configuration, web request settings
- **Performance limits**: Buffer sizes, display limits, subprocess timeouts
- **External services**: IP detection services, WHOIS servers, security APIs
- **Error handling**: Retry configuration, error thresholds
- **Display settings**: Output formatting, color preferences

**Usage**:
```python
from config import (
    get_timeout, get_dns_servers, get_common_ports, 
    get_nmap_timing, is_private_ip, get_speed_category
)

timeout = get_timeout("nmap", "comprehensive")  # 600 seconds
dns_servers = get_dns_servers(include_additional=True)  # 7 servers
ports = get_common_ports("tcp")  # Top TCP ports
timing = get_nmap_timing("aggressive")  # T4
```

### 4. Standardized Tool Interfaces (`utils.py`)

**Purpose**: Consistent tool return formats and automatic standardization.

**Key Components**:
- **Standard result format**: Success/failure, timing, metadata, parsed data, error handling
- **Automatic wrapping**: `@standardize_tool_output()` decorator for legacy tools
- **Helper functions**: `create_success_result()`, `create_error_result()`, `wrap_legacy_result()`
- **Backward compatibility**: Legacy tools automatically upgraded to v3 standard

**Usage**:
```python
from utils import standardize_tool_output, create_success_result

@standardize_tool_output()
def my_tool(target: str) -> str:
    return f"Result for {target}"  # Automatically wrapped

# Manual standard format
return create_success_result(
    tool_name="my_tool",
    execution_time=1.23,
    parsed_data={"target": target, "result": data},
    stdout=raw_output
)
```

## Tool Development Patterns

### Pattern 1: Simple Decorator Approach
**Best for**: Basic tools, quick implementations, legacy tool upgrades

```python
from utils import standardize_tool_output
from config import get_timeout

@standardize_tool_output()
def ping_host(target: str, count: int = 4) -> str:
    """Ping a host and return results"""
    timeout = get_timeout("ping")
    # Implementation here
    return "ping results"
```

### Pattern 2: Full Registry Integration  
**Best for**: Complex tools, rich parameter sets, tools needing detailed metadata

```python
def advanced_scan(target: str, scan_type: str = "basic") -> Dict[str, Any]:
    """Advanced scanning with full error handling"""
    from core.error_handling import create_network_error, ErrorCode
    from config import get_timeout
    
    start_time = datetime.now()
    
    try:
        timeout = get_timeout("nmap", scan_type)
        result = perform_scan(target, timeout)
        
        return create_success_result(
            tool_name="advanced_scan",
            execution_time=(datetime.now() - start_time).total_seconds(),
            parsed_data=result,
            target=target
        )
    except Exception as e:
        return create_network_error(
            ErrorCode.CONNECTION_FAILED,
            tool_name="advanced_scan",
            target=target
        )

def get_module_tools():
    from core.tools_registry import ToolMetadata, ParameterInfo, ParameterType, ToolCategory
    
    return {
        "advanced_scan": ToolMetadata(
            name="advanced_scan",
            function_name="advanced_scan",
            module_path="network.advanced_module",
            description="Advanced network scanning with multiple scan types",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "target": ParameterInfo(
                    param_type=ParameterType.STRING,
                    required=True,
                    description="Target IP or hostname to scan"
                ),
                "scan_type": ParameterInfo(
                    param_type=ParameterType.STRING,
                    required=False,
                    default="basic",
                    choices=["basic", "comprehensive", "stealth"],
                    description="Type of scan to perform"
                )
            },
            aliases=["adv_scan", "scan_advanced"],
            examples=[
                "advanced_scan 192.168.1.1",
                "advanced_scan example.com comprehensive"
            ]
        )
    }
```

## Error Handling Best Practices

### 1. Use Appropriate Error Types
```python
# Network-related errors
return create_network_error(ErrorCode.TIMEOUT, target=target, timeout=30)
return create_network_error(ErrorCode.CONNECTION_FAILED, target=target)

# Input validation errors  
return create_input_error(ErrorCode.INVALID_TARGET, target=target)
return create_input_error(ErrorCode.MISSING_PARAMETER, parameter="hostname")

# System/tool errors
return create_system_error(ErrorCode.TOOL_MISSING, tool="nmap")
return create_system_error(ErrorCode.PERMISSION_DENIED, operation="port_scan")
```

### 2. Leverage Input Validation
```python
from core.error_handling import ErrorRecovery

# Validate targets
is_valid, error_msg = ErrorRecovery.validate_target(target)
if not is_valid:
    return create_input_error(ErrorCode.INVALID_TARGET, target=target)

# Validate ports
is_valid, error_msg = ErrorRecovery.validate_port(port)
if not is_valid:
    return create_input_error(ErrorCode.INVALID_PORT, port=port)
```

### 3. Use Configuration Constants
```python
from config import get_timeout, get_dns_servers, COMMON_PORTS

# Don't hardcode timeouts
timeout = get_timeout("nmap", scan_type)  # ✓
timeout = 300  # ✗

# Don't hardcode DNS servers  
servers = get_dns_servers()  # ✓
servers = ["8.8.8.8", "1.1.1.1"]  # ✗

# Use centralized port specifications
ports = COMMON_PORTS  # ✓
ports = "80,443,22,21,25,53"  # ✗
```

## Migration Guide for Existing Tools

### Step 1: Add Standardization
```python
# Before
def old_tool(target):
    return "string result"

# After  
from utils import standardize_tool_output

@standardize_tool_output()
def old_tool(target):
    return "string result"  # Now automatically standardized
```

### Step 2: Use Centralized Configuration
```python
# Before
def tool_with_timeout(target):
    timeout = 30  # Hardcoded
    
# After
from config import get_timeout

def tool_with_timeout(target):
    timeout = get_timeout("ping")  # From config
```

### Step 3: Enhanced Error Handling
```python
# Before
def tool_with_errors(target):
    try:
        result = operation(target)
        return result
    except Exception as e:
        return f"Error: {e}"

# After
from core.error_handling import create_network_error, ErrorCode

def tool_with_errors(target):
    try:
        result = operation(target)
        return create_success_result("tool", 1.0, result, target=target)
    except TimeoutError:
        return create_network_error(ErrorCode.TIMEOUT, target=target)
    except Exception as e:
        return create_network_error(ErrorCode.CONNECTION_FAILED, target=target)
```

## Benefits of the v3 Infrastructure

### For Developers
- **Consistent interfaces** reduce learning curve
- **Automatic discovery** eliminates manual registration
- **Rich metadata** enables auto-generated documentation
- **Centralized configuration** makes changes easy
- **Standardized errors** improve debugging

### For Users  
- **Helpful error messages** with actionable suggestions
- **Consistent tool behavior** across all modes
- **Better discoverability** with aliases and examples
- **Reliable timeouts** and retry behavior

### For Maintenance
- **Single source of truth** for configuration and tools
- **Plugin architecture** makes adding tools trivial
- **Automated testing** via standardized interfaces
- **Documentation generation** from metadata
- **Easy refactoring** with centralized constants

## Future Enhancements

The infrastructure is designed to support:
- **Automatic help generation** from tool metadata
- **Configuration file support** for user customization
- **Tool versioning** and compatibility checking
- **Performance monitoring** and optimization
- **Remote tool execution** and distributed scanning
- **Web interface integration** with standardized APIs