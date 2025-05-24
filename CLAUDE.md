# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run the chatbot: `python instability.py chatbot`
- Run the chatbot with specific model: `python instability.py chatbot --model MODEL_NAME`
- Run all checks: `python instability.py manual all`
- Run specific check: `python instability.py manual [check_name]`
- Run tests: `python instability.py test`

## Code Style Guidelines
- **Imports**: Standard library imports first, then third-party, then local modules
- **Typing**: Use Python type hints (from typing import List, Dict, Optional, etc.)
- **Naming**: 
  - snake_case for functions/variables
  - CamelCase for classes
  - UPPERCASE for constants
- **Error Handling**: Use try/except blocks with specific exceptions
- **Logging**: Print statements should use colorama (Fore.COLOR)
- **Comments**: Minimal comments, focusing on why not what
- **Functions**: Include verbose, thorough docstrings for functions, especially for tools that can be called by the chatbot

## v3 Project Architecture
- **Modular Design**: Organized into core/, network/, pentest/, memory/, and utils/ modules
- **Enhanced Startup**: Comprehensive system checks and tool inventory on startup
- **Persistent Memory**: Markdown-based long-term memory (network_state.md, target_scope.md)
- **Pentesting Integration**: Native support for nmap, nuclei, httpx, feroxbuster, etc.
- **Fallback Modes**: Graceful degradation when Ollama unavailable

### Core Components (v3)
- **core/**: chatbot.py, startup_checks.py, memory_manager.py, ollama_interface.py
- **network/**: layer2_diagnostics.py, layer3_diagnostics.py, dns_diagnostics.py, web_connectivity.py
- **pentest/**: tool_detector.py, nmap_wrapper.py, discovery_tools.py, exploitation_tools.py, nuclei_wrapper.py
- **memory/**: network_state.md, target_scope.md, session_cache.json
- **utils/**: terminal_ui.py, markdown_manager.py, command_parser.py, output_formatter.py
- **config.py**: Centralized configuration constants

## Tool Development (v3)
When creating tools for v3:
- Place network diagnostics in network/ module
- Place pentesting tools in pentest/ module
- Register tools in respective module's __init__.py
- Implement consistent wrapper interfaces for external tools
- Support both interactive and programmatic execution
- Include cross-platform compatibility
- Add to startup_checks.py tool inventory if applicable

## Dependencies
- Ollama Python API
- colorama for terminal colors
- pyreadline3 (Windows only) for command history
- External tools (nmap, nuclei, httpx, etc.) - detected at startup

## Working Methods
- Rather than having Claude directly test my chatbot after source code modifications, I always prefer to test my chatbot manually in a separate terminal and then I'll tell you the outcome of the testing.
- When implementing v3 features, follow the modular structure defined in instability_v3_structure.md