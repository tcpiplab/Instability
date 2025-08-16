# Instability Chatbot v3

<div style="text-align:left"><img width="33%" src="images/instability_ascii_ghost_terminal_v3.0.png" /></div>

An AI network troubleshooter and pentesting chatbot that runs locally via Ollama. Diagnoses network problems, understands your local and target network context, and keeps all analysis private on localhost. No 3rd party cloud services, no data leaks. Uses `dolphin3` LLM by default but you can specify any Ollama model you have installed. Helpful to orient yourself on an unfamiliar or problematic network, and then to call pentesting tools and analyze their output.

## Overview

Instability v3 builds upon v2 with enhanced functionality and improved architecture. It features:

- **Proactive Startup Assessment**: Comprehensive system, network, and tool inventory on launch
- **Pentesting Tool Integration**: Native support for nmap, nuclei, httpx, feroxbuster, hydra, sqlmap
- **Persistent Memory**: Markdown-based long-term memory for network state and target scope
- **Modular Architecture**: Organized core/, network/, pentest/, memory/, and utils/ modules
- **Enhanced Fallback Modes**: Graceful degradation with help text when Ollama unavailable
- **Cross-platform Tool Detection**: Intelligent tool path discovery and installation guidance
- **Target Scope Management**: Persistent pentesting target definitions with scope tracking

## Key Improvements Over Previous Versions

- **Proactive Intelligence**: Automated environment assessment and tool inventory
- **Pentesting Focus**: Native integration with security tools and workflows
- **Persistent Memory**: Long-term memory across sessions with markdown files
- **Enhanced Modularity**: Clean separation of network, pentesting, and core functions
- **Intelligent Tool Detection**: Multi-path tool discovery with installation guidance
- **Target Management**: Persistent scope definitions for pentesting engagements
- **Improved Fallback**: Functional operation even without Ollama connectivity

## Installation

### Requirements

- Python 3.11 or higher
- [Ollama](https://ollama.ai/) installed and running locally
- An Ollama model installed (default: `dolphin3`, but any compatible model can be used)

### Setting Up

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Ensure Ollama is running:

```bash
ollama serve
```

4. Make sure the dolphin3 model is available (or any other model you want to use):

```bash
ollama pull dolphin3
```

To use a different model, pull it first and then specify it with the `--model` option:

```bash
ollama pull qwen3:8b
python instability.py chatbot --model qwen3:8b
```

## Usage

### Running the Chatbot

```bash
python instability.py chatbot
```

The chatbot automatically runs the v3 4-phase startup sequence before launching, providing comprehensive environment assessment and tool inventory.

You can specify a different Ollama model using the `--model` or `-m` option:

```bash
python instability.py chatbot --model qwen3:8b
python instability.py chatbot -m llama3.2:1b
python instability.py chatbot --model mistral:7b
```

The default model is `dolphin3` if no model is specified.

### Running Specific Tools Manually

```bash
python instability.py manual [tool_name]
```

Available tools are organized into categories:
- **Network Diagnostics**: ping, dns_check, web_check, network_scan
- **Email Diagnostics**: smtp_connectivity, imap_connectivity, email_services
- **Pentesting**: nmap_scan, port_scan, host_discovery  
- **System Info**: system_info, interface_status, tool_inventory

To see a list of available tools:

```bash
python instability.py manual
```

To run comprehensive diagnostics:

```bash
python instability.py manual all
```

### Testing the Environment (v3 Startup Sequence)

```bash
python instability.py test
```

This runs the comprehensive v3 4-phase startup sequence:
1. **Core System Verification** - OS detection, Ollama connectivity, network interfaces, local IP
2. **Internet Connectivity Assessment** - External IP detection, DNS resolution, web services
3. **Pentesting Tool Inventory** - Scan for nmap, nuclei, httpx, feroxbuster, etc.
4. **Target Scope Configuration** - Memory and scope management (partially implemented)

### Running Tests

```bash
python instability.py run-tests
```

### Getting Help

```bash
python instability.py help
```

## In-Chat Commands

While using the chatbot, you can use these commands:

- `/help` - Show available commands and tools
- `/exit` or `/quit` - Exit the chatbot
- `/clear` - Clear conversation history
- `/tools` - List available diagnostic and pentesting tools
- `/memory` - Display persistent memory files
- `/scope` - Show or update target scope
- `/inventory` - Display detected tool inventory
- `/<tool_name>` - Run a specific tool directly (e.g., `/nmap`, `/get_local_ip`)

## Project Structure

### Root Files
- `instability.py` - Main entry point with enhanced startup sequence
- `config.py` - Centralized configuration and tool paths
- `requirements.txt` - Project dependencies
- `Instability_Chatbot_SRD.md` - Software Requirements Document
- `Instability_ASCII_Header_v3.txt` - ASCII art header for the terminal interface

### Core Modules
- `core/` - Enhanced chatbot, startup checks, memory manager, Ollama interface
- `network/` - Layer 2/3 diagnostics, DNS testing, web connectivity, email diagnostics
- `pentest/` - Tool detection, nmap/nuclei/httpx wrappers, exploitation tools
- `memory/` - Persistent markdown files (network_state.md, target_scope.md)
- `utils/` - Terminal UI, markdown management, command parsing, output formatting

## Design Principles

This implementation follows these key principles:

1. **Proactivity**: Automated assessment and intelligent recommendations
2. **Modularity**: Clean separation of network, pentesting, and core functions
3. **Persistence**: Long-term memory across sessions with markdown files
4. **Reliability**: Graceful degradation with helpful fallback modes
5. **Intelligence**: Smart tool detection with installation guidance
6. **Usability**: Intuitive interface with comprehensive startup assessment

## MCP (Model Context Protocol) Server

Instability v3 includes a built-in MCP server that exposes all network diagnostics and pentesting tools through the Model Context Protocol, making them accessible to any MCP-compatible client.

### Compatibility
- ✅ **Claude Desktop**: Fully compatible and tested
- ✅ **VS Code GitHub Copilot**: Fully compatible and tested
- ✅ **Other MCP clients**: Should work with any MCP-compatible application

### Setup
1. Generate API key and configure authentication:
```bash
python setup_mcp_auth.py
```

2. Add the server configuration to your MCP client (e.g., Claude Desktop)

3. Start the MCP server:
```bash
python mcp_server.py
```

See `MCP_AUTHENTICATION.md` for detailed setup instructions.

## Dependencies

### Required Python Packages
- `ollama`: For interfacing with local LLM
- `colorama`: For colorized terminal output
- `readline` (Unix/macOS) or `pyreadline3` (Windows): For command history and completion
- `mcp`: For MCP server functionality

### External Tools (Detected at Startup)
- `nmap`: Network mapping and port scanning
- `nuclei`: Vulnerability scanner with templates
- `httpx`: Fast HTTP toolkit for web discovery
- `feroxbuster`: Fast directory/file enumeration
- `gobuster`: Directory/DNS enumeration tool
- `hydra`: Network login cracker
- `sqlmap`: SQL injection testing tool
- `traceroute`/`tracert`: Network path tracing

## Extending the Tools

To add a new tool in v3, you have two approaches:

### Option 1: Simple Decorator Approach (Recommended for basic tools)
```python
from utils import standardize_tool_output

@standardize_tool_output()
def my_new_tool(target: str, option: str = "default") -> str:
    """Tool description"""
    # Your tool implementation
    return "tool result"
```

### Option 2: Full Registry Integration (Recommended for complex tools)
1. **Add your function** to the appropriate module in `network/`, `pentest/`, etc.
2. **Create get_module_tools()** function in your module:
```python
def get_module_tools():
    from core.tools_registry import ToolMetadata, ParameterInfo, ParameterType, ToolCategory
    return {
        "my_tool": ToolMetadata(
            name="my_tool",
            function_name="my_new_tool", 
            module_path="network.my_module",
            description="Tool description",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "target": ParameterInfo(ParameterType.STRING, required=True),
                "option": ParameterInfo(ParameterType.STRING, default="default")
            }
        )
    }
```
3. **External Tools**: Update `pentest/tool_detector.py` if it's an external dependency
4. **Configuration**: Add any constants to `config.py`

The tool will automatically be discovered and available in both chatbot and manual modes.

## Current Implementation Status

### ☑︎ Fully Functional
- **4-phase startup sequence** - Complete system assessment
- **Manual tool execution** - All listed tools working  
- **Chatbot integration** - v3 startup sequence integrated
- **Tool inventory** - Detection of external pentesting tools
- **Network diagnostics** - Layer 2/3, DNS, web connectivity, email infrastructure testing
- **Basic pentesting tools** - nmap integration and wrappers
- **Cross-platform support** - Windows, Linux, macOS compatibility
- **Graceful degradation** - Functions without internet/Ollama
- **Unified tool interfaces** - Standardized return formats across all tools
- **Centralized configuration** - All constants and settings in config.py
- **Enhanced error handling** - Contextual error messages with actionable suggestions
- **Automatic tool registration** - Plugin-style architecture with metadata

### ⚠ Partially Implemented  
- **Memory system** - Framework in place, markdown files defined but not fully functional
- **Target scope management** - Basic structure exists, needs full implementation
- **Advanced pentesting features** - Some tools need expanded functionality

### [PLANNED] Features
- Additional pentesting tool wrappers (nuclei, httpx, feroxbuster full integration)
- Enhanced memory persistence and session tracking
- Advanced target scope and engagement management
- Web-based interface option

## Recent Additions

- **Email Diagnostics** - SMTP/IMAP connectivity testing for 9 major email providers (Gmail, Outlook, Yahoo, iCloud, AOL, Zoho, Mail.com, GMX, Fastmail)
- **MAC Address Manufacturer Lookup** - Offline MAC address manufacturer identification using Wireshark database

## TODO

- Add IP address geolocation lookup tool
- Add tool for displaying ARP table

## Troubleshooting

### Ollama Connection Issues

If you encounter issues connecting to Ollama:

1. Ensure Ollama is running with `ollama serve`
2. Verify your desired model is installed with `ollama list` (default is dolphin3)
3. Check for any firewalls blocking localhost connections
4. If using a custom model, ensure it's correctly spelled and available in Ollama

### Command History Not Working

On Windows, ensure pyreadline3 is installed:

```bash
pip install pyreadline3
```

On Unix/Linux/macOS, the built-in readline should work automatically.