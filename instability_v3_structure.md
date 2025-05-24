# Instability v3 Repository Structure

## Root Directory Files
```
instability-chatbot/
├── instability.py              # Main entry point with enhanced startup sequence
├── requirements.txt            # Python dependencies
├── README.md                   # Installation and usage documentation
├── .gitignore                  # Standard Python gitignore
└── config.py                   # Configuration constants and defaults
```

## Core Modules
```
├── core/
│   ├── __init__.py
│   ├── chatbot.py              # Enhanced chatbot with proactive capabilities
│   ├── startup_checks.py       # Comprehensive system and tool verification
│   ├── memory_manager.py       # Long-term memory in markdown files
│   └── ollama_interface.py     # Ollama API handling with fallback modes
```

## Network Diagnostics
```
├── network/
│   ├── __init__.py
│   ├── layer2_diagnostics.py   # OS detection, interface status, local IP
│   ├── layer3_diagnostics.py   # External IP, routing, connectivity
│   ├── dns_diagnostics.py      # DNS resolution and server testing
│   └── web_connectivity.py     # Website reachability testing
```

## Pentesting Tools Integration
```
├── pentest/
│   ├── __init__.py
│   ├── tool_detector.py        # Detect installed pentesting tools
│   ├── nmap_wrapper.py         # Nmap integration and result parsing
│   ├── discovery_tools.py      # httpx, feroxbuster, gobuster integration
│   ├── exploitation_tools.py   # hydra, sqlmap integration
│   ├── nuclei_wrapper.py       # Nuclei template runner
│   └── traceroute_wrapper.py   # Cross-platform traceroute/tracert
```

## Memory and State Management
```
├── memory/
│   ├── __init__.py
│   ├── network_state.md        # Auto-updated network environment info
│   ├── target_scope.md         # Pentesting target definitions and scope
│   └── session_cache.json      # Temporary session data
```

## Utilities and Helpers
```
├── utils/
│   ├── __init__.py
│   ├── terminal_ui.py          # Enhanced terminal interface
│   ├── markdown_manager.py     # Markdown file creation and updates
│   ├── command_parser.py       # Command parsing and validation
│   └── output_formatter.py     # Consistent output formatting
```

## Testing and Documentation
```
├── tests/
│   ├── __init__.py
│   ├── test_startup_checks.py
│   ├── test_tool_detection.py
│   └── test_network_diagnostics.py
└── docs/
    ├── INSTALLATION.md
    ├── TOOL_REQUIREMENTS.md
    └── API_REFERENCE.md
```

## Key Design Changes for v3

### Enhanced Startup Sequence
The `startup_checks.py` module will implement a comprehensive initialization routine that runs automatically when the chatbot starts. This includes:

**Phase 1: Core System Verification**
- Detect operating system and version
- Check Ollama API connectivity with graceful fallback
- Verify layer 2 network interfaces and status
- Determine local IP address and network configuration

**Phase 2: Internet Connectivity Assessment**
- Test layer 3 connectivity and external IP detection
- Validate DNS resolver functionality
- Confirm access to major websites and services
- Measure basic network performance metrics

**Phase 3: Pentesting Tool Inventory**
- Scan for installed tools (nmap, nuclei, httpx, etc.)
- Verify tool versions and basic functionality
- Report missing tools with installation recommendations
- Cache tool availability for session optimization

**Phase 4: Target Scope Configuration**
- Present current network assessment summary
- Prompt user for pentesting target scope definition
- Update or create target scope markdown file
- Initialize session with full environmental context

### Long-term Memory Implementation
The memory system will maintain two primary markdown files that persist between sessions:

**network_state.md**: Automatically updated with current network environment details, including interface configurations, detected networks, external IP history, and connectivity baselines.

**target_scope.md**: User-defined pentesting targets, including IP ranges, domains, excluded addresses, and scope notes. This file supports multiple target environments and maintains historical scope definitions.

### Fallback Modes
When Ollama is unavailable, the chatbot will operate in a reduced-capability mode that still provides:
- Direct tool execution via command interface
- Network diagnostic capabilities
- Target scope management
- Basic help and guidance systems

### Tool Integration Philosophy
Each pentesting tool wrapper will provide consistent interfaces for execution, result parsing, and output formatting. The wrappers handle cross-platform differences and provide intelligent defaults based on the current target scope.

### Configuration Management
The `config.py` file will centralize all configuration constants, including tool paths, timeout values, default target ranges, and memory file locations. This allows easy customization without modifying core code.

## Migration Strategy from v2

The migration involves extracting and enhancing the existing v2 functionality while adding the new proactive capabilities:

1. **Network diagnostics**: Enhanced versions of existing tools with better integration
2. **Chatbot core**: Rebuilt with startup sequence and memory integration
3. **Tool registry**: Expanded to include pentesting tools alongside network diagnostics
4. **Memory system**: New markdown-based persistent memory implementation
5. **User interface**: Improved terminal experience with better status reporting