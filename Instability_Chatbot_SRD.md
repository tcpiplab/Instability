# Software Requirements Document: Instability Chatbot v3

## 1. Project Overview

### 1.1 Purpose
The Instability Chatbot v3 is a proactive terminal-based network diagnostic and pentesting assistant that provides comprehensive environmental assessment, tool integration, and persistent memory for security professionals and network administrators.

### 1.2 Goals
- Implement proactive startup assessment with comprehensive environment analysis
- Integrate pentesting tools (nmap, nuclei, httpx, etc.) with intelligent wrappers
- Provide persistent memory across sessions using markdown files
- Offer graceful fallback modes when Ollama unavailable
- Enable cross-platform tool detection with installation guidance
- Support target scope management for pentesting engagements

### 1.3 Target Users
- Hackers and pentesters getting oriented to an unfamiliar local network or environment
- Network administrators
- IT support personnel
- End users troubleshooting network issues
- Developers testing network functionalities

### 1.4 Key Differentiators from Previous Versions
- **Proactive Intelligence**: Automated environment assessment and tool inventory
- **Pentesting Integration**: Native support for security tools with consistent wrappers
- **Persistent Memory**: Long-term memory using markdown files (network_state.md, target_scope.md)
- **Modular Architecture**: Clean separation into core/, network/, pentest/, memory/, utils/
- **Enhanced Fallback**: Functional operation with help text when Ollama unavailable
- **Smart Tool Detection**: Multi-path discovery with installation recommendations

## 2. Core Features

### 2.1 Chatbot Functionality
- Interactive text-based interface for network diagnostic and pentesting queries
- Multi-turn conversation capability with persistent memory
- Proactive startup assessment and tool inventory
- Thinking/reasoning display in grey text
- Distinct visual display for tool execution and results
- Target scope management and persistent tracking
- No emojis or unnecessary visual clutter

### 2.2 Network Diagnostic and Pentesting Capabilities
- Comprehensive Layer 2/3 network diagnostics
- DNS resolution and server testing
- Web connectivity and reachability testing
- Integrated pentesting tool support (nmap, nuclei, httpx, feroxbuster, hydra, sqlmap)
- Cross-platform tool detection with installation guidance
- Ability to function offline with degraded capabilities
- Clear separation between tool interface and implementation

### 2.3 Memory Management
- Use Ollama's native context parameter for conversation history
- Persistent markdown-based memory files:
  - `network_state.md`: Auto-updated network environment details
  - `target_scope.md`: User-defined pentesting targets and scope
- Simple JSON cache for session data (session_cache.json)
- Memory updates at session start/end to minimize file I/O
- Optional target scope prompting with "local network only" default

### 2.4 Tool Integration
- Modular tool organization (network/, pentest/ modules)
- Dynamic discovery and registration of available tools
- Intelligent tool path detection with common installation locations
- Standardized wrapper interfaces for external tools
- Cross-platform compatibility handling
- Startup tool inventory with moderate installation recommendations
- Ability to call tools directly via commands or natural language queries

## 3. Usage Modes

### 3.1 Chatbot Mode
- Interactive conversational interface
- Tool execution based on user queries
- Clear display of tool selection reasoning, execution, and results
- Runtime model selection via `--model` CLI argument

### 3.2 Manual Tool Execution
- Direct execution of specific tools via command line
- Structured output of results

### 3.3 Test Mode
- Verification of environment setup, dependencies, and tool availability
- Ollama connectivity testing
- Comprehensive tool inventory and path detection
- Network connectivity baseline establishment

## 4. Technical Requirements

### 4.1 Ollama Integration
- Direct use of Ollama Python API
- Utilization of Ollama's context parameter for conversation tracking
- Support for different Ollama models with runtime selection (default: phi3:14b)

### 4.2 Tool Execution Framework
- Simple function-based tool registry
- Standard interface for tool inputs and outputs
- Tool documentation accessible via help command

### 4.3 Caching
- Simple JSON-based cache for tool results
- No custom memory architecture
- Cache should persist between sessions

### 4.4 Error Handling
- Graceful handling of Ollama API errors
- Recovery from tool execution failures
- User-friendly error messages

### 4.5 Offline Operation and Fallback Modes
- Must function without internet access for local network diagnostics
- Graceful degradation when Ollama unavailable with basic help text
- Recommendations for starting Ollama API with default model
- Clear indication of online vs. offline capabilities
- Functional tool execution even without LLM connectivity

## 5. User Interface

### 5.1 Terminal Interface
- Color-coded output (via colorama):
  - User input: Cyan
  - Assistant responses: Blue
  - Tool execution: Green
  - Errors: Red
  - Thinking/reasoning: Grey
- Command completion for tools and built-in commands
- Command history navigation with arrow keys

### 5.2 Commands
- `/help`: Display available commands and tools
- `/exit` or `/quit`: Exit the application
- `/memory`: Display persistent memory files
- `/scope`: Show or update target scope
- `/inventory`: Display detected tool inventory
- `/tools`: List available diagnostic and pentesting tools
- Tool-specific commands for direct execution (e.g., `/nmap`, `/nuclei`)

### 5.3 Output Formatting
- Clear delineation between chatbot responses and tool results
- Visual indication of tool execution in progress
- Proper formatting of multi-line outputs

## 6. Out of Scope

### 6.1 Explicitly Excluded
- LangChain or similar high-level abstraction frameworks
- Complex OOP architecture
- Silent mode (`--silent` option)
- Web or GUI interfaces
- Backward compatibility with v1
- Speech output capabilities

## 7. Performance Requirements

### 7.1 Response Time
- Tool execution should provide feedback within 5 seconds or show progress
- Ollama API responses should be displayed as received

### 7.2 Resource Usage
- Minimal memory footprint
- No background processes or services
- Cache file size limited to reasonable bounds

## 8. Implementation Approach

### 8.1 Code Organization
- Modular architecture with clear separation of concerns
- Organized directory structure:
  - `instability.py`: Main entry point with enhanced startup
  - `config.py`: Centralized configuration and tool paths
  - `core/`: Enhanced chatbot, startup checks, memory manager, Ollama interface
  - `network/`: Layer 2/3 diagnostics, DNS testing, web connectivity
  - `pentest/`: Tool detection, wrappers for security tools
  - `memory/`: Persistent markdown files and session cache
  - `utils/`: Terminal UI, markdown management, output formatting

### 8.2 Dependencies
- Required Python packages:
  - `ollama`: For model API access
  - `colorama`: For terminal colors
  - `readline` (or equivalent): For command history and completion
- External tools (detected at startup):
  - `nmap`, `nuclei`, `httpx`, `feroxbuster`, `gobuster`
  - `hydra`, `sqlmap`, `traceroute`/`tracert`
- Tool path detection with multiple common installation locations

### 8.3 Error Recovery
- Graceful handling of Ollama API failures
- Clear user feedback on tool execution errors
- Operation in degraded modes when resources are unavailable

## 9. Future Considerations

### 9.1 Potential Enhancements
- Plugin architecture for additional external tools
- Tool workflow automation (e.g., "run all DNS tools", "perform initial recon")
- Enhanced target scope templates for common engagement types
- Integration with additional pentesting frameworks
- Export functionality for tool results and findings
- Web-based interface for remote operation
