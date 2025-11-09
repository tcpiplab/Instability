"""
Memory manager module for Instability v3.

Handles persistent markdown-based memory files and session caching.
Provides functions for reading, writing, and updating network_state.md
and target_scope.md files.
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import colorama for terminal colors
from colorama import Fore, Style

# Import configuration
from config import (
    MEMORY_DIR, NETWORK_STATE_FILE, TARGET_SCOPE_FILE, SESSION_CACHE_FILE,
    DEFAULT_TARGET_SCOPE, get_memory_dir
)


def initialize_memory_files() -> None:
    """Create default memory files if they don't exist."""
    # Ensure memory directory exists
    get_memory_dir()
    
    # Create network_state.md if it doesn't exist
    if not os.path.exists(NETWORK_STATE_FILE):
        create_default_network_state()
    
    # Create target_scope.md if it doesn't exist
    if not os.path.exists(TARGET_SCOPE_FILE):
        create_default_target_scope()
    
    # Initialize session cache
    if not os.path.exists(SESSION_CACHE_FILE):
        create_empty_session_cache()


def create_default_network_state() -> None:
    """Create a default network_state.md file."""
    default_content = """# Network Environment State

*Last updated: {timestamp}*
*Session: {session_id}*

## System Information

**Operating System:** Not detected yet
**Hostname:** Not detected yet
**Username:** Not detected yet

## Network Interfaces

*Network interfaces will be detected during startup*

## External Connectivity

**External IP:** Not detected yet
**ISP:** Unknown
**Location:** Unknown
**Last checked:** Never

### Connectivity Tests
*Connectivity tests will be performed during startup*

## DNS Configuration

**Primary DNS:** Not detected yet
**Secondary DNS:** Not detected yet
**Search Domains:** Not detected yet

### DNS Test Results
*DNS tests will be performed during startup*

## Network Discovery

### Local Network Scan
*Network discovery will be performed as needed*

#### Active Hosts
*No hosts discovered yet*

## Historical Data

### External IP History
*No historical data yet*

### Network Changes
*No network changes recorded yet*
""".format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        session_id=datetime.now().strftime("%Y-%m-%d_%H%M%S")
    )
    
    with open(NETWORK_STATE_FILE, 'w') as f:
        f.write(default_content)


def create_default_target_scope() -> None:
    """Create a default target_scope.md file."""
    default_content = """# Pentesting Target Scope

*Last updated: {timestamp}*
*Scope type: {default_scope}*

## Current Engagement

**Engagement Name:** Default Local Assessment
**Start Date:** {date}
**Authorized by:** Self-assessment
**Scope:** {default_scope}

## In-Scope Targets

### Primary Network
**Network Range:** To be determined during network discovery
**Description:** Local network devices
**Authorization:** Limited to owned devices only

#### Specific Targets
*Targets will be identified during network discovery*

### Secondary Network
*No secondary networks defined*

## Out-of-Scope

### Explicitly Excluded
- **Any external/internet targets** - Outside of local network
- **Neighbor networks** - No authorization
- **Corporate VPN networks** - Separate authorization required

### Service Restrictions
- **No destructive testing** - Read-only assessment
- **No brute force attacks** - Light credential testing only
- **No DoS testing** - Avoid service disruption

## Testing Guidelines

### Allowed Activities
- [ALLOWED] Port scanning and service enumeration
- [ALLOWED] Vulnerability scanning with Nuclei
- [ALLOWED] Web application discovery
- [ALLOWED] Default credential testing
- [ALLOWED] Network topology mapping

### Prohibited Activities
- [PROHIBITED] Exploitation of discovered vulnerabilities
- [PROHIBITED] Data exfiltration or modification
- [PROHIBITED] Denial of service attacks
- [PROHIBITED] Social engineering
- [PROHIBITED] Physical security testing

## Tool Usage Authorization

### Passive Reconnaissance
- [ALLOWED] nmap (TCP SYN scans only)
- [ALLOWED] httpx for web discovery
- [ALLOWED] DNS enumeration
- [ALLOWED] OSINT gathering

### Active Testing
- [ALLOWED] Nuclei vulnerability scans
- [ALLOWED] Directory/file enumeration (feroxbuster, gobuster)
- ⚠ Light credential testing (hydra with small wordlists)
- [PROHIBITED] Exploitation frameworks (Metasploit, etc.)

## Findings Summary

### Discovered Services
*To be populated during testing*

### Vulnerabilities Found
*To be populated during testing*

### Recommendations
*To be populated after assessment*

## Notes and Comments

Add any additional notes about the engagement, special considerations, or observations here.

---
*This scope document should be reviewed and updated before each testing session.*
""".format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        default_scope=DEFAULT_TARGET_SCOPE,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    with open(TARGET_SCOPE_FILE, 'w') as f:
        f.write(default_content)


def create_empty_session_cache() -> None:
    """Create an empty session cache file."""
    empty_cache = {
        "session_id": None,
        "start_time": None,
        "last_activity": None,
        "conversation_turns": 0,
        "current_targets": [],
        "recent_tool_results": {},
        "user_preferences": {},
        "pending_actions": []
    }
    
    with open(SESSION_CACHE_FILE, 'w') as f:
        json.dump(empty_cache, f, indent=2)


def read_network_state() -> Dict[str, Any]:
    """
    Read and parse network_state.md file.
    
    Returns:
        Dictionary containing parsed network state data
    """
    if not os.path.exists(NETWORK_STATE_FILE):
        create_default_network_state()
    
    try:
        with open(NETWORK_STATE_FILE, 'r') as f:
            content = f.read()
        
        # Parse the markdown content
        parsed_data = parse_network_state_markdown(content)
        return parsed_data
    
    except Exception as e:
        print(f"Warning: Failed to read network state file: {Fore.RED}{e}{Style.RESET_ALL}")
        return {}


def update_network_state(updates: Dict[str, Any]) -> None:
    """
    Update specific sections of network_state.md file.
    
    Args:
        updates: Dictionary containing sections to update
    """
    try:
        # Read current content
        if os.path.exists(NETWORK_STATE_FILE):
            with open(NETWORK_STATE_FILE, 'r') as f:
                content = f.read()
        else:
            create_default_network_state()
            with open(NETWORK_STATE_FILE, 'r') as f:
                content = f.read()
        
        # Update the content
        updated_content = update_markdown_sections(content, updates)
        
        # Update timestamp
        timestamp_line = f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        updated_content = re.sub(
            r'\*Last updated:.*?\*',
            timestamp_line,
            updated_content
        )
        
        # Write updated content atomically
        temp_file = f"{NETWORK_STATE_FILE}.tmp"
        with open(temp_file, 'w') as f:
            f.write(updated_content)
        
        os.rename(temp_file, NETWORK_STATE_FILE)
    
    except Exception as e:
        print(f"Warning: Failed to update network state file: {Fore.RED}{e}{Style.RESET_ALL}")


def read_target_scope() -> Dict[str, Any]:
    """
    Read and parse target_scope.md file.
    
    Returns:
        Dictionary containing parsed target scope data
    """
    if not os.path.exists(TARGET_SCOPE_FILE):
        create_default_target_scope()
    
    try:
        with open(TARGET_SCOPE_FILE, 'r') as f:
            content = f.read()
        
        # Parse the markdown content
        parsed_data = parse_target_scope_markdown(content)
        return parsed_data
    
    except Exception as e:
        print(f"Warning: Failed to read target scope file: {Fore.RED}{e}{Style.RESET_ALL}")
        return {"scope_type": DEFAULT_TARGET_SCOPE, "targets": []}


def update_target_scope(scope_data: Dict[str, Any]) -> None:
    """
    Update target_scope.md with new scope information.
    
    Args:
        scope_data: Dictionary containing new scope information
    """
    try:
        # Read current content
        if os.path.exists(TARGET_SCOPE_FILE):
            with open(TARGET_SCOPE_FILE, 'r') as f:
                content = f.read()
        else:
            create_default_target_scope()
            with open(TARGET_SCOPE_FILE, 'r') as f:
                content = f.read()
        
        # Update specific sections based on scope_data
        updates = {}
        
        if "scope_type" in scope_data:
            updates["scope_type_header"] = f"*Scope type: {scope_data['scope_type']}*"
        
        if "engagement_name" in scope_data:
            updates["engagement_name"] = f"**Engagement Name:** {scope_data['engagement_name']}"
        
        if "targets" in scope_data:
            targets_section = format_targets_section(scope_data["targets"])
            updates["targets"] = targets_section
        
        # Update the content
        updated_content = update_markdown_sections(content, updates)
        
        # Update timestamp
        timestamp_line = f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        updated_content = re.sub(
            r'\*Last updated:.*?\*',
            timestamp_line,
            updated_content,
            count=1
        )
        
        # Write updated content atomically
        temp_file = f"{TARGET_SCOPE_FILE}.tmp"
        with open(temp_file, 'w') as f:
            f.write(updated_content)
        
        os.rename(temp_file, TARGET_SCOPE_FILE)
    
    except Exception as e:
        print(f"Warning: Failed to update target scope file: {Fore.RED}{e}{Style.RESET_ALL}")


def load_session_cache() -> Dict[str, Any]:
    """
    Load session cache from JSON file.
    
    Returns:
        Dictionary containing session cache data
    """
    if not os.path.exists(SESSION_CACHE_FILE):
        create_empty_session_cache()
    
    try:
        with open(SESSION_CACHE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load session cache: {Fore.RED}{e}{Style.RESET_ALL}")
        create_empty_session_cache()
        return load_session_cache()


def save_session_cache(cache: Dict[str, Any]) -> None:
    """
    Save session cache to JSON file.
    
    Args:
        cache: Dictionary containing session cache data
    """
    try:
        # Update last activity timestamp
        cache["last_activity"] = datetime.now().isoformat()
        
        # Write to temp file first for atomic operation
        temp_file = f"{SESSION_CACHE_FILE}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(cache, f, indent=2, default=str)
        
        os.rename(temp_file, SESSION_CACHE_FILE)
    
    except Exception as e:
        print(f"Warning: Failed to save session cache: {Fore.RED}{e}{Style.RESET_ALL}")


def cache_tool_result(tool_name: str, result: Dict[str, Any], ttl_minutes: int = 60) -> None:
    """
    Cache a tool result with TTL.
    
    Args:
        tool_name: Name of the tool
        result: Tool result dictionary
        ttl_minutes: Time-to-live in minutes
    """
    try:
        cache = load_session_cache()
        
        # Calculate expiration time
        from datetime import timedelta
        expire_time = datetime.now() + timedelta(minutes=ttl_minutes)
        
        # Store summarized result (not full output)
        cache_entry = {
            "summary": result.get("parsed_data", {}),
            "timestamp": datetime.now().isoformat(),
            "cache_until": expire_time.isoformat(),
            "success": result.get("success", False)
        }
        
        cache["recent_tool_results"][tool_name] = cache_entry
        save_session_cache(cache)
    
    except Exception as e:
        print(f"Warning: Failed to cache tool result: {Fore.RED}{e}{Style.RESET_ALL}")


def get_cached_result(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Get cached tool result if still valid.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Cached result if valid, None otherwise
    """
    try:
        cache = load_session_cache()
        
        if tool_name in cache["recent_tool_results"]:
            entry = cache["recent_tool_results"][tool_name]
            cache_until = datetime.fromisoformat(entry["cache_until"])
            
            if datetime.now() < cache_until:
                return entry
            else:
                # Remove expired entry
                del cache["recent_tool_results"][tool_name]
                save_session_cache(cache)
        
        return None
    
    except Exception as e:
        print(f"Warning: Failed to get cached result: {Fore.RED}{e}{Style.RESET_ALL}")
        return None


# Helper functions for parsing markdown

def parse_network_state_markdown(content: str) -> Dict[str, Any]:
    """Parse network_state.md markdown content."""
    data = {
        "system_info": {},
        "interfaces": [],
        "external_ip": None,
        "dns_config": {},
        "connectivity_tests": {},
        "discovered_hosts": []
    }
    
    # Extract system information
    system_match = re.search(r'\*\*Operating System:\*\* (.+)', content)
    if system_match:
        data["system_info"]["os"] = system_match.group(1)
    
    hostname_match = re.search(r'\*\*Hostname:\*\* (.+)', content)
    if hostname_match:
        data["system_info"]["hostname"] = hostname_match.group(1)
    
    # Extract external IP
    ip_match = re.search(r'\*\*External IP:\*\* (.+)', content)
    if ip_match and ip_match.group(1) != "Not detected yet":
        data["external_ip"] = ip_match.group(1)
    
    return data


def parse_target_scope_markdown(content: str) -> Dict[str, Any]:
    """Parse target_scope.md markdown content."""
    data = {
        "scope_type": DEFAULT_TARGET_SCOPE,
        "engagement_name": "Default Local Assessment",
        "targets": [],
        "authorized_activities": [],
        "prohibited_activities": []
    }
    
    # Extract scope type
    scope_match = re.search(r'\*Scope type: (.+)\*', content)
    if scope_match:
        data["scope_type"] = scope_match.group(1)
    
    # Extract engagement name
    engagement_match = re.search(r'\*\*Engagement Name:\*\* (.+)', content)
    if engagement_match:
        data["engagement_name"] = engagement_match.group(1)
    
    return data


def update_markdown_sections(content: str, updates: Dict[str, Any]) -> str:
    """Update specific sections in markdown content."""
    updated_content = content
    
    for section_key, new_value in updates.items():
        if section_key == "system_info" and isinstance(new_value, dict):
            # Update system information section
            for key, value in new_value.items():
                if key == "os":
                    pattern = r'(\*\*Operating System:\*\*) .+'
                    replacement = f'\\1 {value}'
                    updated_content = re.sub(pattern, replacement, updated_content)
                elif key == "hostname":
                    pattern = r'(\*\*Hostname:\*\*) .+'
                    replacement = f'\\1 {value}'
                    updated_content = re.sub(pattern, replacement, updated_content)
        
        elif section_key == "external_ip":
            pattern = r'(\*\*External IP:\*\*) .+'
            replacement = f'\\1 {new_value}'
            updated_content = re.sub(pattern, replacement, updated_content)
    
    return updated_content


def format_targets_section(targets: List[Dict[str, Any]]) -> str:
    """Format targets list into markdown section."""
    if not targets:
        return "*No targets defined yet*"
    
    formatted = ""
    for i, target in enumerate(targets, 1):
        formatted += f"{i}. **{target.get('ip', 'Unknown')}** - {target.get('hostname', 'Unknown')}\n"
        if target.get('ports'):
            formatted += f"   - Ports: {', '.join(map(str, target['ports']))}\n"
        if target.get('notes'):
            formatted += f"   - Notes: {target['notes']}\n"
        formatted += "\n"
    
    return formatted.strip()


# Quick test function for development
def test_memory_manager():
    """Test function for development purposes."""
    print("Testing memory manager module...")

    # Test initialization
    initialize_memory_files()
    print(f"[{Fore.GREEN}OK{Style.RESET_ALL}] Memory files initialized")

    # Test reading network state
    network_state = read_network_state()
    print(f"[{Fore.GREEN}OK{Style.RESET_ALL}] Network state loaded: {len(network_state)} sections")

    # Test reading target scope
    target_scope = read_target_scope()
    print(f"[{Fore.GREEN}OK{Style.RESET_ALL}] Target scope loaded: {target_scope.get('scope_type', 'unknown')}")

    # Test session cache
    cache = load_session_cache()
    print(f"[{Fore.GREEN}OK{Style.RESET_ALL}] Session cache loaded")

    return True


def get_module_tools():
    """
    Return tool metadata for this module.

    All functions in this module are internal memory management functions
    that should not be exposed directly via MCP. They are accessed through
    higher-level interfaces like the chat tool's historical query features.

    Returns:
        Empty dict - no tools to expose from this module
    """
    return {}


if __name__ == "__main__":
    test_memory_manager()