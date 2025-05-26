# Migration Guide: v2 to v3

This guide helps understand how to port tools and functionality from Instability v2 to the new v3 architecture.

## Architecture Overview

### v2 Architecture (Legacy)
- **Monolithic tools**: Most tools in `tools.py` and `network_diagnostics.py`
- **Direct imports**: Tools imported directly from original scripts
- **Simple registry**: Function-based tool dictionary
- **Minimal structure**: Flat organization with basic categorization

### v3 Architecture (Current)
- **Modular structure**: Tools organized by purpose (`network/`, `pentest/`, `core/`)
- **Standardized interfaces**: Consistent return formats and parameters
- **4-phase startup**: Comprehensive environment assessment
- **Graceful degradation**: Fallback modes when dependencies unavailable
- **Tool detection**: Automatic discovery of external tools

## Tool Implementation Patterns

### v2 Tool Pattern
```python
# In tools.py or network_diagnostics.py
def ping_target(host: str = "8.8.8.8", target: str = None, arg_name: str = None, count: int = 4) -> str:
    """Simple function returning string result"""
    try:
        # Tool implementation
        result = subprocess.run(...)
        return f"Ping successful: {result}"
    except Exception as e:
        return f"Ping failed: {e}"
```

### v3 Tool Pattern
```python
# In network/layer3_diagnostics.py
def ping_host(target: str, count: int = 4, silent: bool = False) -> Dict[str, Any]:
    """Standardized function returning structured result"""
    start_time = datetime.now()
    
    try:
        # Tool implementation
        result = subprocess.run(...)
        
        if not silent:
            print(f"Ping to {target}: Success")
        
        return {
            "success": True,
            "result": {"avg_time": 15.2, "packets_sent": count},
            "execution_time": (datetime.now() - start_time).total_seconds(),
            "timestamp": start_time.isoformat(),
            "tool_name": "ping_host",
            "target": target,
            "command_executed": f"ping -c {count} {target}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time": (datetime.now() - start_time).total_seconds(),
            "tool_name": "ping_host",
            "target": target
        }
```

## Tool Registration

### v2 Registration
```python
# In network_diagnostics.py
def get_available_tools() -> Dict[str, Callable]:
    return {
        "ping_target": ping_target,
        "check_dns_resolvers": check_dns_resolvers,
        "get_external_ip": get_external_ip,
        # ... more tools
    }
```

### v3 Registration
```python
# In instability.py
def _get_v3_tools_registry() -> Dict[str, Any]:
    return {
        "ping": {
            "module": "network.layer3_diagnostics", 
            "function": "ping_host", 
            "description": "Test ICMP connectivity"
        },
        "dns_check": {
            "module": "network.dns_diagnostics", 
            "function": "resolve_hostname", 
            "description": "DNS resolution testing"
        },
        # ... more tools
    }
```

## Module Placement Rules

### Network Diagnostics → `network/`
- **Layer 2**: `network/layer2_diagnostics.py` (interfaces, local IP, MAC addresses)
- **Layer 3**: `network/layer3_diagnostics.py` (ping, traceroute, routing)
- **DNS**: `network/dns_diagnostics.py` (resolution, server testing)
- **Web**: `network/web_connectivity.py` (HTTP/HTTPS testing)

### Pentesting Tools → `pentest/`
- **Tool Detection**: `pentest/tool_detector.py` (nmap, nuclei detection)
- **Port Scanning**: `pentest/nmap_wrapper.py` (nmap integration)
- **Web Discovery**: `pentest/discovery_tools.py` (httpx, feroxbuster)
- **Exploitation**: `pentest/exploitation_tools.py` (hydra, sqlmap)

### System Tools → `core/` or `utils/`
- **Startup Checks**: `core/startup_checks.py`
- **Memory Management**: `memory/memory_manager.py`
- **Utilities**: `utils/` (formatting, parsing, etc.)

## Interface Standardization

### Parameter Compatibility
Many v2 tools have multiple parameter names for the same concept:
```python
# v2 compatibility pattern
def ping_target(host: str = "8.8.8.8", target: str = None, arg_name: str = None, count: int = 4):
    # Handle multiple parameter names
    actual_target = target or host or arg_name or "8.8.8.8"
```

### v3 Standardized Parameters
```python
# v3 standard pattern
def ping_host(target: str, count: int = 4, timeout: int = 5, silent: bool = False):
    # Single, clear parameter names
```

## Current Porting Status

### ✅ Successfully Ported
- **ping functionality**: `network.layer3_diagnostics.ping_host()`
- **DNS checking**: `network.dns_diagnostics.resolve_hostname()`
- **System info**: `network.layer2_diagnostics.get_system_info()`
- **Interface detection**: `network.layer2_diagnostics.get_all_interfaces()`
- **Web connectivity**: `network.web_connectivity.test_http_connectivity()`
- **External IP**: `network.layer3_diagnostics.get_external_ip()`
- **Tool detection**: `pentest.tool_detector.scan_for_tools()`

### ⚠️ Partially Implemented
- **Memory system**: Stubs in place, markdown files defined but not fully functional
- **nmap integration**: Basic wrapper exists, needs full feature implementation
- **Chatbot tools**: v2 tools still used with compatibility layer

### ❌ Missing (Referenced but not available)
- `check_if_external_ip_changed` - IP change monitoring
- `resolver_check` - DNS resolver monitoring
- `check_layer_two_network` - Advanced layer 2 analysis
- `whois_check` - WHOIS lookup functionality
- `os_utils` - OS-specific utilities

## Porting Guidelines

### 1. Analyze v2 Tool
- Understand the tool's purpose and functionality
- Identify input parameters and output format
- Note any external dependencies

### 2. Choose v3 Module Location
- **Network diagnostics** → `network/`
- **Security/pentesting** → `pentest/`
- **System utilities** → `core/` or `utils/`

### 3. Implement v3 Interface
- Use standardized parameter names
- Return structured dictionary with success/error info
- Include timing and metadata
- Add optional `silent` parameter for non-interactive use

### 4. Add Tool Registration
- Add to `_get_v3_tools_registry()` in `instability.py`
- Add to chatbot tool registry if needed
- Update startup tool detection if external tool

### 5. Test Integration
- Test in manual mode: `python instability.py manual tool_name`
- Test in comprehensive suite: `python instability.py manual all`
- Test chatbot integration if applicable

## Example: Porting a v2 Tool

### Before (v2 Style)
```python
# In tools.py
def check_dns_resolvers() -> str:
    """Check DNS resolver functionality"""
    try:
        result = socket.gethostbyname("google.com")
        return f"DNS working: {result}"
    except Exception as e:
        return f"DNS failed: {e}"
```

### After (v3 Style)
```python
# In network/dns_diagnostics.py
def test_dns_resolvers(target: str = "google.com", silent: bool = False) -> Dict[str, Any]:
    """Test DNS resolver functionality against target domain"""
    start_time = datetime.now()
    
    try:
        resolved_ip = socket.gethostbyname(target)
        
        if not silent:
            print(f"DNS resolution successful: {target} → {resolved_ip}")
        
        return {
            "success": True,
            "result": {
                "target": target,
                "resolved_ip": resolved_ip,
                "resolver_working": True
            },
            "execution_time": (datetime.now() - start_time).total_seconds(),
            "timestamp": start_time.isoformat(),
            "tool_name": "test_dns_resolvers",
            "target": target
        }
    except Exception as e:
        if not silent:
            print(f"DNS resolution failed: {e}")
        
        return {
            "success": False,
            "error": str(e),
            "result": {
                "target": target,
                "resolver_working": False
            },
            "execution_time": (datetime.now() - start_time).total_seconds(),
            "tool_name": "test_dns_resolvers",
            "target": target
        }
```

## Future Migration Tasks

When additional v2 scripts are available:

1. **Inventory new tools** - Catalog functionality of copied v2 scripts
2. **Assess duplication** - Check if v3 equivalents already exist
3. **Prioritize porting** - Focus on missing functionality first
4. **Maintain compatibility** - Keep parameter compatibility where needed
5. **Update documentation** - Keep this guide current with new ports

## Key Benefits of v3 Architecture

- **Modularity**: Easy to find and modify specific functionality
- **Consistency**: Standardized interfaces and return formats
- **Testability**: Individual tools can be tested in isolation
- **Extensibility**: Clear patterns for adding new tools
- **Maintainability**: Simple function-based design without complex frameworks
- **Reliability**: Graceful degradation when dependencies unavailable