# Data Structure Specifications

## Tool Inventory Structure

The tool inventory is stored as a JSON file and loaded into memory as a Python dictionary. It tracks all detected tools and their installation status.

### Tool Inventory Schema

```python
{
    "metadata": {
        "last_updated": "2024-01-15T10:30:00Z",
        "scan_duration": 2.34,
        "platform": "darwin",
        "python_version": "3.11.5"
    },
    "tools": {
        "tool_name": {
            "found": bool,
            "path": str or None,
            "version": str or None,
            "install_command": str or None,
            "category": str,
            "description": str,
            "last_checked": str,
            "check_duration": float
        }
    }
}
```

### Example Tool Inventory

```json
{
    "metadata": {
        "last_updated": "2024-01-15T10:30:00Z",
        "scan_duration": 2.34,
        "platform": "darwin",
        "python_version": "3.11.5"
    },
    "tools": {
        "nmap": {
            "found": true,
            "path": "/opt/homebrew/bin/nmap",
            "version": "7.94",
            "install_command": null,
            "category": "network_scanning",
            "description": "Network exploration tool and security scanner",
            "last_checked": "2024-01-15T10:30:00Z",
            "check_duration": 0.12
        },
        "nuclei": {
            "found": false,
            "path": null,
            "version": null,
            "install_command": "go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
            "category": "vulnerability_scanning",
            "description": "Fast vulnerability scanner with templates",
            "last_checked": "2024-01-15T10:30:00Z",
            "check_duration": 0.08
        },
        "httpx": {
            "found": true,
            "path": "/usr/local/bin/httpx",
            "version": "1.3.7",
            "install_command": null,
            "category": "web_discovery",
            "description": "Fast HTTP toolkit for web discovery",
            "last_checked": "2024-01-15T10:30:00Z",
            "check_duration": 0.15
        }
    }
}
```

### Tool Categories

Standard categories for organizing tools:

- `"network_scanning"` - nmap, masscan
- `"vulnerability_scanning"` - nuclei, nessus
- `"web_discovery"` - httpx, gobuster, feroxbuster
- `"dns_tools"` - dig, nslookup, dnsrecon
- `"exploitation"` - hydra, sqlmap, metasploit
- `"network_diagnostics"` - ping, traceroute, netstat
- `"system_info"` - uname, ifconfig, ip

## Session Cache Structure

The session cache stores temporary data that doesn't need to persist between sessions. Stored as JSON.

### Session Cache Schema

```python
{
    "session_id": str,
    "start_time": str,
    "last_activity": str,
    "conversation_turns": int,
    "current_targets": List[str],
    "recent_tool_results": Dict[str, Any],
    "user_preferences": Dict[str, Any],
    "pending_actions": List[Dict[str, Any]]
}
```

### Example Session Cache

```json
{
    "session_id": "2024-01-15_10-30-00_lukesheppard",
    "start_time": "2024-01-15T10:30:00Z",
    "last_activity": "2024-01-15T11:45:00Z",
    "conversation_turns": 23,
    "current_targets": ["192.168.1.1", "192.168.1.10"],
    "recent_tool_results": {
        "get_external_ip": {
            "result": "203.0.113.45",
            "timestamp": "2024-01-15T10:35:00Z",
            "cache_until": "2024-01-15T11:35:00Z"
        },
        "nmap_192.168.1.1": {
            "ports_found": [22, 80, 443],
            "timestamp": "2024-01-15T10:40:00Z",
            "full_result_id": "nmap_scan_001"
        }
    },
    "user_preferences": {
        "preferred_scan_intensity": "moderate",
        "auto_resolve_dns": true,
        "show_tool_commands": true,
        "max_concurrent_scans": 3
    },
    "pending_actions": [
        {
            "action": "scheduled_scan",
            "tool": "nuclei",
            "target": "192.168.1.1",
            "scheduled_for": "2024-01-15T12:00:00Z",
            "options": {"severity": "high,critical"}
        }
    ]
}
```

## Startup Check Results Structure

Data structure for storing the results of the 4-phase startup sequence:

```python
{
    "startup_id": str,
    "timestamp": str,
    "total_duration": float,
    "phases": {
        "core_system": {
            "status": str,  # "success", "warning", "error"
            "duration": float,
            "checks": {
                "os_detection": {"status": str, "result": Any, "message": str},
                "ollama_connectivity": {"status": str, "result": Any, "message": str},
                "network_interfaces": {"status": str, "result": Any, "message": str},
                "local_ip": {"status": str, "result": Any, "message": str}
            }
        },
        "internet_connectivity": {
            "status": str,
            "duration": float,
            "checks": {
                "external_ip": {"status": str, "result": Any, "message": str},
                "dns_resolution": {"status": str, "result": Any, "message": str},
                "web_connectivity": {"status": str, "result": Any, "message": str}
            }
        },
        "tool_inventory": {
            "status": str,
            "duration": float,
            "tools_found": int,
            "tools_missing": int,
            "critical_missing": List[str]
        },
        "target_scope": {
            "status": str,
            "duration": float,
            "scope_loaded": bool,
            "scope_type": str,
            "targets_defined": int
        }
    }
}
```

## Helper Functions for Data Structures

```python
# Tool Inventory Functions
def load_tool_inventory() -> Dict[str, Any]:
    """Load tool inventory from JSON file."""

def save_tool_inventory(inventory: Dict[str, Any]) -> None:
    """Save tool inventory to JSON file."""

def update_tool_status(tool_name: str, detection_result: Dict[str, Any]) -> None:
    """Update status of a single tool in inventory."""

def get_tools_by_category(category: str) -> List[str]:
    """Get list of tool names in a specific category."""

def get_missing_tools() -> List[str]:
    """Get list of tools that are not installed."""

def get_available_tools() -> List[str]:
    """Get list of tools that are installed and available."""

# Session Cache Functions
def load_session_cache() -> Dict[str, Any]:
    """Load session cache from JSON file."""

def save_session_cache(cache: Dict[str, Any]) -> None:
    """Save session cache to JSON file."""

def cache_tool_result(tool_name: str, result: Dict[str, Any], ttl_minutes: int = 60) -> None:
    """Cache a tool result with TTL."""

def get_cached_result(tool_name: str) -> Dict[str, Any] or None:
    """Get cached tool result if still valid."""

def clear_expired_cache() -> None:
    """Remove expired cache entries."""

# Startup Results Functions
def save_startup_results(results: Dict[str, Any]) -> None:
    """Save startup check results."""

def get_last_startup_results() -> Dict[str, Any] or None:
    """Get results from last startup sequence."""

def format_startup_summary(results: Dict[str, Any]) -> str:
    """Format startup results for display to user."""
```

## File Management Strategy

### JSON File Handling
```python
import json
from typing import Dict, Any
from pathlib import Path

def safe_json_load(filepath: str, default: Dict[str, Any] = None) -> Dict[str, Any]:
    """Safely load JSON file with fallback to default."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default or {}

def safe_json_save(filepath: str, data: Dict[str, Any]) -> bool:
    """Safely save JSON file with atomic write."""
    try:
        # Write to temp file first
        temp_file = f"{filepath}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        # Atomic rename
        Path(temp_file).rename(filepath)
        return True
    except Exception:
        return False
```

### Data Validation
```python
def validate_tool_inventory(data: Dict[str, Any]) -> bool:
    """Validate tool inventory structure."""
    required_keys = ["metadata", "tools"]
    return all(key in data for key in required_keys)

def validate_session_cache(data: Dict[str, Any]) -> bool:
    """Validate session cache structure."""
    required_keys = ["session_id", "start_time", "last_activity"]
    return all(key in data for key in required_keys)

def sanitize_tool_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize tool result for safe storage."""
    # Remove or truncate large outputs
    if "stdout" in result and len(result["stdout"]) > 10000:
        result["stdout"] = result["stdout"][:10000] + "... (truncated)"
    return result
```

## Performance Considerations

1. **Lazy loading** - Load data structures only when needed
2. **Caching** - Keep frequently accessed data in memory
3. **Atomic writes** - Prevent corruption during concurrent access
4. **Size limits** - Truncate large outputs to prevent memory issues
5. **TTL management** - Automatically expire old cached data
6. **Validation** - Check data integrity on load and save