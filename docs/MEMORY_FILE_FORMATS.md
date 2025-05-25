# Memory File Format Specifications

## Overview

Instability v3 uses markdown files for persistent memory across sessions. This approach provides:
- **Human readability** - Files can be viewed and edited in any text editor
- **Version control friendly** - Git can track changes meaningfully
- **Structured but flexible** - Markdown headers organize data while allowing freeform content
- **No abstraction overhead** - Simple file I/O with standard library functions

## File Locations

All memory files are stored in the `memory/` directory:
- `memory/network_state.md` - Auto-updated network environment information
- `memory/target_scope.md` - User-defined pentesting targets and scope
- `memory/session_cache.json` - Temporary session data (not persistent across sessions)

## network_state.md Format

This file is automatically updated by the chatbot and contains current network environment details.

```markdown
# Network Environment State

*Last updated: 2024-01-15 10:30:00*
*Session: 2024-01-15_morning*

## System Information

**Operating System:** macOS 14.2.1 (Darwin)
**Hostname:** MacBook-Pro.local
**Username:** lukesheppard

## Network Interfaces

### en0 (Ethernet)
- **Status:** Up
- **IP Address:** 192.168.1.100
- **Subnet Mask:** 255.255.255.0
- **Gateway:** 192.168.1.1
- **MAC Address:** aa:bb:cc:dd:ee:ff

### en1 (Wi-Fi)
- **Status:** Up
- **IP Address:** 10.0.0.50
- **SSID:** HomeNetwork
- **Signal Strength:** -45 dBm

## External Connectivity

**External IP:** 203.0.113.45
**ISP:** Example ISP Inc.
**Location:** San Francisco, CA
**Last checked:** 2024-01-15 10:25:00

### Connectivity Tests
- **Google DNS (8.8.8.8):** ✓ Reachable (15ms)
- **Cloudflare DNS (1.1.1.1):** ✓ Reachable (12ms)
- **www.google.com:** ✓ Reachable (HTTP 200)
- **www.github.com:** ✓ Reachable (HTTP 200)

## DNS Configuration

**Primary DNS:** 192.168.1.1
**Secondary DNS:** 8.8.8.8
**Search Domains:** local

### DNS Test Results
- **Forward DNS (google.com):** ✓ Working
- **Reverse DNS (8.8.8.8):** ✓ dns.google

## Network Discovery

### Local Network Scan (192.168.1.0/24)
*Last scan: 2024-01-15 10:20:00*

#### Active Hosts
1. **192.168.1.1** - router.local
   - Ports: 22/tcp (ssh), 80/tcp (http), 443/tcp (https)
   - MAC: 00:11:22:33:44:55
   - Vendor: Netgear

2. **192.168.1.10** - printer.local
   - Ports: 9100/tcp (jetdirect)
   - MAC: 66:77:88:99:aa:bb
   - Vendor: HP

## Historical Data

### External IP History
- 2024-01-15 10:25:00: 203.0.113.45
- 2024-01-14 09:15:00: 203.0.113.44
- 2024-01-13 14:30:00: 203.0.113.45

### Network Changes
- 2024-01-15 08:00:00: Connected to HomeNetwork Wi-Fi
- 2024-01-14 18:30:00: Disconnected from ethernet
- 2024-01-13 09:00:00: Network interface en0 came up
```

## target_scope.md Format

This file contains user-defined pentesting targets and is manually editable.

```markdown
# Pentesting Target Scope

*Last updated: 2024-01-15 10:30:00*
*Scope type: local network only*

## Current Engagement

**Engagement Name:** Home Network Assessment
**Start Date:** 2024-01-15
**Authorized by:** Self-assessment
**Scope:** Local network reconnaissance only

## In-Scope Targets

### Primary Network
**Network Range:** 192.168.1.0/24
**Description:** Home network devices
**Authorization:** Full access to owned devices

#### Specific Targets
1. **192.168.1.1** - Home router
   - Services: SSH, HTTP, HTTPS
   - Notes: Default credentials already changed
   
2. **192.168.1.10** - Network printer
   - Services: HTTP, IPP
   - Notes: Check for default credentials

3. **192.168.1.100** - This machine
   - Services: SSH
   - Notes: Self-assessment, all services

### Secondary Network
**Network Range:** 10.0.0.0/24
**Description:** Wi-Fi guest network
**Authorization:** Limited scanning only

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
- ✓ Port scanning and service enumeration
- ✓ Vulnerability scanning with Nuclei
- ✓ Web application discovery
- ✓ Default credential testing
- ✓ Network topology mapping

### Prohibited Activities
- ✗ Exploitation of discovered vulnerabilities
- ✗ Data exfiltration or modification
- ✗ Denial of service attacks
- ✗ Social engineering
- ✗ Physical security testing

## Tool Usage Authorization

### Passive Reconnaissance
- ✓ nmap (TCP SYN scans only)
- ✓ httpx for web discovery
- ✓ DNS enumeration
- ✓ OSINT gathering

### Active Testing
- ✓ Nuclei vulnerability scans
- ✓ Directory/file enumeration (feroxbuster, gobuster)
- ⚠️ Light credential testing (hydra with small wordlists)
- ✗ Exploitation frameworks (Metasploit, etc.)

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
```

## Memory Management Functions

Simple functions for reading and writing memory files:

```python
def read_network_state() -> Dict[str, Any]:
    """Read and parse network_state.md file."""
    
def update_network_state(updates: Dict[str, Any]) -> None:
    """Update specific sections of network_state.md file."""
    
def read_target_scope() -> Dict[str, Any]:
    """Read and parse target_scope.md file."""
    
def update_target_scope(scope_data: Dict[str, Any]) -> None:
    """Update target_scope.md with new scope information."""
    
def initialize_memory_files() -> None:
    """Create default memory files if they don't exist."""
```

## File Update Strategy

### network_state.md Updates
- **Session start:** Update system info, interface status, external IP
- **After connectivity tests:** Update DNS and connectivity results
- **After network scans:** Update discovered hosts and services
- **Session end:** Add any new historical data

### target_scope.md Updates
- **User-initiated only:** Never auto-update without user consent
- **Interactive prompting:** Ask user for scope changes during startup
- **Manual editing:** Users can edit file directly between sessions

### Parsing Strategy
- **Section-based parsing:** Use markdown headers to identify sections
- **Regex patterns:** Extract structured data from markdown tables
- **Fallback handling:** Graceful degradation if file format is modified
- **Validation:** Check for required sections and warn if missing

## Implementation Notes

1. **Use standard library only** - No markdown parsing dependencies
2. **Simple regex parsing** - Extract data with basic pattern matching
3. **Preserve user modifications** - Don't overwrite manually edited sections
4. **Atomic updates** - Write to temp file then rename to avoid corruption
5. **Backup on major changes** - Keep backup copies of important updates
6. **Cross-platform paths** - Use os.path.join for file paths