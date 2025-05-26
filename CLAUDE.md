# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run the chatbot: `python instability.py chatbot`
- Run the chatbot with specific model: `python instability.py chatbot --model MODEL_NAME`
- Run comprehensive diagnostics: `python instability.py manual all`
- Run specific tool: `python instability.py manual [tool_name]`
- List available tools: `python instability.py manual`
- Run v3 environment test: `python instability.py test`
- Run test suite: `python instability.py run-tests`

## Code Style Guidelines & Design Philosophy
- **Simplicity First**: Avoid framework complexity and OOP abstraction - keep code easy to understand, maintain, and customize
- **Function-Based**: Use simple functions rather than complex class hierarchies
- **No Heavy Frameworks**: Avoid LangChain, complex ORMs, or other heavyweight abstractions
- **Direct Implementation**: Prefer direct library usage over abstraction layers
- **Imports**: Standard library imports first, then third-party, then local modules
- **Typing**: Use Python type hints (from typing import List, Dict, Optional, etc.)
- **Naming**: 
  - snake_case for functions/variables
  - CamelCase for classes (use sparingly)
  - UPPERCASE for constants
- **Error Handling**: Use try/except blocks with specific exceptions
- **Logging**: Print statements should use colorama (Fore.COLOR)
- **Comments**: Minimal comments, focusing on why not what
- **Functions**: Include verbose, thorough docstrings for functions, especially for tools that can be called by the chatbot

## v3 Project Architecture
- **Modular Design**: Organized into core/, network/, pentest/, memory/, and utils/ modules
- **4-Phase Startup**: Comprehensive system assessment with graceful degradation
  1. Core System Verification (OS, Ollama, interfaces, local IP)
  2. Internet Connectivity Assessment (external IP, DNS, web services)
  3. Pentesting Tool Inventory (nmap, nuclei, httpx, feroxbuster, etc.)
  4. Target Scope Configuration (memory and scope management)
- **Persistent Memory**: Markdown-based long-term memory (network_state.md, target_scope.md)
- **Pentesting Integration**: Native support for security tools with consistent wrappers
- **Fallback Modes**: Graceful degradation when Ollama or internet unavailable
- **Function-Based Tools**: Simple tool registry using direct function calls

### Core Components (v3)
- **core/**: chatbot.py, startup_checks.py, memory_manager.py, ollama_interface.py
- **network/**: layer2_diagnostics.py, layer3_diagnostics.py, dns_diagnostics.py, web_connectivity.py
- **pentest/**: tool_detector.py, nmap_wrapper.py, discovery_tools.py, exploitation_tools.py, nuclei_wrapper.py
- **memory/**: network_state.md, target_scope.md, session_cache.json
- **utils/**: terminal_ui.py, markdown_manager.py, command_parser.py, output_formatter.py
- **config.py**: Centralized configuration constants

## Tool Development (v3)
When creating tools for v3, follow these simple principles:

### Tool Placement
- **Network diagnostics**: Place in `network/` module
- **Pentesting tools**: Place in `pentest/` module 
- **System utilities**: Place in appropriate module or `utils/`

### Implementation Guidelines
- **Keep it simple**: Write direct functions, avoid complex classes
- **Consistent interfaces**: Return standardized result dictionaries
- **Cross-platform**: Handle Windows/Linux/macOS differences gracefully
- **Error handling**: Use try/except with informative error messages
- **Documentation**: Include clear docstrings explaining purpose and usage

### Tool Registration
1. **Manual mode**: Add to `_get_v3_tools_registry()` in `instability.py`
2. **Chatbot mode**: Add to tool registry in `network_diagnostics.py` or equivalent
3. **Tool detection**: Add to `pentest/tool_detector.py` if it's an external tool
4. **Startup inventory**: External tools are automatically detected

### Tool Function Structure
```python
def my_tool(target: str, silent: bool = False) -> Dict[str, Any]:
    """Tool description and purpose"""
    start_time = datetime.now()
    
    try:
        # Tool implementation
        result = do_the_work(target)
        
        return {
            "success": True,
            "result": result,
            "execution_time": (datetime.now() - start_time).total_seconds(),
            "timestamp": start_time.isoformat(),
            "tool_name": "my_tool",
            "target": target
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time": (datetime.now() - start_time).total_seconds(),
            "tool_name": "my_tool"
        }
```

## Dependencies
- Ollama Python API
- colorama for terminal colors
- pyreadline3 (Windows only) for command history
- External tools (nmap, nuclei, httpx, etc.) - detected at startup

## Working Methods & Testing
- **Manual Testing Preferred**: Rather than having Claude directly test the chatbot after source code modifications, always prefer manual testing in a separate terminal and report results back
- **v3 Structure**: When implementing v3 features, follow the modular structure defined in instability_v3_structure.md
- **Incremental Development**: Test tools individually before integration
- **Graceful Degradation**: Ensure functionality works even when external dependencies unavailable

### Testing Commands
```bash
# Test v3 startup sequence
python instability.py test

# Test manual tools
python instability.py manual
python instability.py manual system_info
python instability.py manual all

# Test chatbot (manual testing preferred)
python instability.py chatbot
```

### v3 Integration Status
The v3 integration includes:
- ✅ 4-phase startup sequence working
- ✅ Manual mode tools functional
- ✅ Tool interface standardization complete
- ✅ Chatbot integration with v3 modules
- ✅ Error handling and graceful degradation
- ⚠️ Memory manager and tool detector stubs (functional but not fully implemented)
- ⚠️ Some pentesting tools need full wrapper implementation

## Key Design Principles (IMPORTANT)
1. **Simplicity Over Sophistication**: Simple, readable functions beat complex frameworks
2. **Direct Over Abstract**: Use libraries directly rather than creating abstraction layers
3. **Functions Over Classes**: Prefer function-based tools over class hierarchies
4. **Clarity Over Cleverness**: Code should be immediately understandable
5. **Manual Over Automatic**: Prefer explicit tool registration over magic discovery
6. **Graceful Over Rigid**: Always provide fallbacks and degrade gracefully
7. **Modular Over Monolithic**: Separate concerns but keep interfaces simple

These principles make the codebase easy to understand, maintain, and extend with new tools.