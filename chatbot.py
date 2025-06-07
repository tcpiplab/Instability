"""
Chatbot module for Instability v2

This module provides the core chatbot functionality using the Ollama API directly.
It handles the interactive terminal interface, command processing, and tool execution.
"""

import os
import sys
import json
import time
from utils import extract_thinking, colorize_numbers
from typing import Dict, List, Any, Optional, Tuple
from colorama import Fore, Style

# Import Rich for Markdown rendering
try:
    from rich.console import Console
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
    # Create a console instance
    console = Console()
except ImportError:
    RICH_AVAILABLE = False

# Import readline for command history and completion
try:
    if sys.platform == 'darwin' or sys.platform.startswith('linux'):
        import readline

        READLINE_AVAILABLE = True
    elif sys.platform == 'win32':
        try:
            import pyreadline3 as readline

            READLINE_AVAILABLE = True
        except ImportError:
            READLINE_AVAILABLE = False
    else:
        READLINE_AVAILABLE = False
except ImportError:
    READLINE_AVAILABLE = False
    
# Import utility functions
from utils import print_welcome_header

# Try to import ollama - this is a required dependency for the chatbot mode
try:
    import ollama
except ImportError:
    print(f"{Fore.RED}Error: Ollama Python package not installed.{Style.RESET_ALL}")
    print(f"Install with: pip install ollama")
    sys.exit(1)

# Local imports
try:
    from core.tools_registry import get_tool_registry
    from network_diagnostics import get_available_tools  # Legacy fallback for tool listing
except ImportError:
    print(f"{Fore.RED}Error: Tool registry or network diagnostics module not found.{Style.RESET_ALL}")
    sys.exit(1)

# Configuration
DEFAULT_MODEL = "phi3:14b"
CACHE_FILE = os.path.expanduser("~/.instability_v2_cache.json")
HISTORY_FILE = os.path.expanduser("~/.instability_v2_history")
MAX_CONVERSATION_LENGTH = 20  # Maximum number of messages to keep in history

# Terminal colors
USER_COLOR = Fore.CYAN
ASSISTANT_COLOR = Fore.BLUE
TOOL_COLOR = Fore.GREEN
ERROR_COLOR = Fore.RED
THINKING_COLOR = Style.DIM


# Command completion setup
def setup_readline():
    """Setup readline for command history and completion"""
    if not READLINE_AVAILABLE:
        return

    # Set history file
    try:
        readline.read_history_file(HISTORY_FILE)
    except FileNotFoundError:
        pass

    # Save history on exit
    import atexit
    atexit.register(readline.write_history_file, HISTORY_FILE)

    # Command completion function
    def completer(text, state):
        # Basic commands
        commands = ['/help', '/exit', '/quit', '/clear', '/tools']

        # Add tool commands
        tools = get_available_tools()
        for tool in tools:
            commands.append(f"/{tool}")

        # Filter based on current text
        matches = [cmd for cmd in commands if cmd.startswith(text)]

        # Return match or None
        if state < len(matches):
            return matches[state]
        return None

    # Set the completer
    readline.set_completer(completer)

    # Set the delimiter
    if sys.platform != 'win32':
        readline.set_completer_delims(' \t\n;')
        readline.parse_and_bind('tab: complete')
    else:
        # Windows uses different readline library
        readline.set_completer_delims(' \t\n;')
        readline.parse_and_bind('tab: complete')


# Cache management functions
def load_cache() -> Dict[str, Any]:
    """Load the cache from file"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return {"_last_updated": time.strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        print(f"{ERROR_COLOR}Error loading cache: {e}{Style.RESET_ALL}")
        return {"_last_updated": time.strftime("%Y-%m-%d %H:%M:%S")}


def save_cache(cache: Dict[str, Any]) -> None:
    """Save the cache to file"""
    try:
        # Update timestamp
        cache["_last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")

        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"{ERROR_COLOR}Error saving cache: {e}{Style.RESET_ALL}")


# Helper functions for the chatbot
def print_welcome():
    """Print the welcome message with ASCII art header"""

    # Clear the terminal screen before printing the welcome message
    os.system('cls' if os.name == 'nt' else 'clear')

    # Print the ASCII art banner from the utility function
    print_welcome_header()
    
    # Print additional information
    print(f"{ASSISTANT_COLOR}A network diagnostic AI chatbot that works even during network outages{Style.RESET_ALL}")
    print(
        f"{Style.DIM}{ASSISTANT_COLOR}Type {USER_COLOR}/help{Style.RESET_ALL} "
        f"{Style.DIM}{ASSISTANT_COLOR}for available commands or {USER_COLOR}/exit{Style.RESET_ALL} "
        f"{Style.DIM}{ASSISTANT_COLOR}to quit.\n{Style.RESET_ALL}")


def print_thinking(message: str) -> None:
    """Print thinking/reasoning from the chatbot"""
    print(f"{ASSISTANT_COLOR}Chatbot (thinking): {THINKING_COLOR}{message}{Style.RESET_ALL}")


def print_tool_execution(tool_name: str) -> None:
    """Print tool execution message"""
    print(f"{ASSISTANT_COLOR}Chatbot (executing tool): {TOOL_COLOR}{tool_name}{Style.RESET_ALL}")


def print_assistant(message: str) -> None:
    """Print the assistant's response with Markdown support and number colorization"""
    # Apply number colorization
    colored_message = colorize_numbers(message)
    
    if RICH_AVAILABLE and any(md_marker in message for md_marker in ["```", "*", "_", "##", "`"]):
        # Print the prefix with colorama
        print(f"{ASSISTANT_COLOR}Chatbot: {Style.RESET_ALL}", end="")
        # Use Rich to render the Markdown content with colored numbers
        md = Markdown(colored_message)
        console.print(md)
    else:
        # For non-markdown text, we can still apply Rich markup if available
        if RICH_AVAILABLE:
            from rich.text import Text
            print(f"{ASSISTANT_COLOR}Chatbot: {Style.RESET_ALL}", end="")
            text = Text.from_markup(colored_message)
            console.print(text)
        else:
            # Fallback to regular print without Rich markup
            print(f"{ASSISTANT_COLOR}Chatbot: {Style.RESET_ALL}{message}")


def print_planning(message: str) -> None:
    """Print the assistant's planning and explaining thoughts with Markdown support"""
    if RICH_AVAILABLE and any(md_marker in message for md_marker in ["```", "*", "_", "##", "`"]):
        # Print the prefix with colorama
        print(f"{ASSISTANT_COLOR}Chatbot (planning): {Style.RESET_ALL}", end="")
        # Use Rich to render the Markdown content
        md = Markdown(style="dim blue", code_theme="solarized-dark", markup=message)
        console.print(md)
    else:
        # Regular text, use normal print
        print(f"{ASSISTANT_COLOR}Chatbot (planning): {Style.DIM}{message}{Style.RESET_ALL}")


def print_error(message: str) -> None:
    """Print an error message"""
    print(f"{ERROR_COLOR}Error: {message}{Style.RESET_ALL}")


def parse_tool_call(content: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Parse a potential tool call from the model's response

    Returns:
        Tuple of (tool_name, args) or (None, None) if no tool call found
    """
    # Check for tool call format:
    # TOOL: tool_name
    # ARGS: {...}
    if "TOOL:" not in content:
        return None, None

    try:
        # Split content by TOOL:
        parts = content.split("TOOL:")
        if len(parts) < 2:
            return None, None

        # Get the part after TOOL:
        tool_part = parts[1].strip()

        # Extract tool name (everything before ARGS: or the next line)
        if "ARGS:" in tool_part:
            tool_name = tool_part.split("ARGS:")[0].strip()
        else:
            # No args specified
            tool_name = tool_part.split("\n")[0].strip()
        
        # Clean up tool name - remove parentheses if present (AI sometimes adds them)
        if "(" in tool_name:
            tool_name = tool_name.split("(")[0]

        # Extract args if present
        args = {}
        if "ARGS:" in tool_part:
            args_text = tool_part.split("ARGS:")[1].strip()
            
            # Take only the first line after ARGS: to avoid parsing fake tool results
            args_line = args_text.split('\n')[0].strip()

            # Find the JSON part (everything between { and })
            json_start = args_line.find("{")
            if json_start >= 0:
                json_end = args_line.rfind("}") + 1
                if json_end > json_start:
                    json_str = args_line[json_start:json_end]
                    try:
                        args = json.loads(json_str)
                    except json.JSONDecodeError as e:
                        # Invalid JSON, use empty args
                        print_error(f"Invalid JSON in args: {json_str} (Error: {e})")
                        args = {}

        return tool_name, args
    except Exception as e:
        print_error(f"Error parsing tool call: {Fore.RED}{e}{Style.RESET_ALL}")
        return None, None


# Command handling functions
def handle_command(command: str, cache: Dict[str, Any]) -> Tuple[bool, bool]:
    """Handle special commands

    Returns:
        Tuple of (handled, should_exit)
    """
    cmd = command.lower()

    if cmd in ['/exit', '/quit']:
        return True, True

    elif cmd == '/help':
        print(f"\n{USER_COLOR}Available commands:{Style.RESET_ALL}")
        print(f"  {USER_COLOR}/help{Style.RESET_ALL}  - Show this help message")
        print(f"  {USER_COLOR}/exit{Style.RESET_ALL}  - Exit the chatbot")
        print(f"  {USER_COLOR}/quit{Style.RESET_ALL}  - Same as /exit")
        print(f"  {USER_COLOR}/clear{Style.RESET_ALL} - Clear conversation history")
        print(f"  {USER_COLOR}/tools{Style.RESET_ALL} - List available diagnostic tools")
        print(f"  {USER_COLOR}/cache{Style.RESET_ALL} - Display cached data")
        print(f"  {USER_COLOR}/<tool>{Style.RESET_ALL} - Run a specific tool directly")
        return True, False

    elif cmd == '/clear':
        print(f"{TOOL_COLOR}Conversation history cleared{Style.RESET_ALL}")
        return True, False

    elif cmd == '/tools':
        tools = get_available_tools()
        print(f"\n{USER_COLOR}Available tools:{Style.RESET_ALL}")
        for name, func in tools.items():
            desc = func.__doc__.split('\n')[0].strip() if func.__doc__ else "No description"
            print(f"  {TOOL_COLOR}{name}{Style.RESET_ALL} - {desc}")
        return True, False

    elif cmd == '/cache':
        print(f"\n{USER_COLOR}Cached data:{Style.RESET_ALL}")
        for key, value in cache.items():
            if not key.startswith('_'):  # Skip internal keys
                print(f"  {TOOL_COLOR}{key}{Style.RESET_ALL}: {value}")
        return True, False

    elif cmd.startswith('/'):
        # Check if it's a direct tool call
        tool_name = cmd[1:]  # Remove the leading /
        tools = get_available_tools()

        if tool_name in tools:
            print_tool_execution(tool_name)
            try:
                # Use v3 tool registry for proper execution
                registry = get_tool_registry()
                result = registry.execute_tool(tool_name, {}, mode="manual")
                # Tool result suppressed for clean output

                # Update cache with the result
                cache[tool_name] = result
                save_cache(cache)
            except Exception as e:
                print_error(f"Error executing tool {tool_name}: {Fore.RED}{e}{Style.RESET_ALL}")
            return True, False
        else:
            print_error(f"Unknown command or tool: {cmd}")
            return True, False

    # Not a command
    return False, False


def start_interactive_session(model_name: str = DEFAULT_MODEL) -> None:
    """Start the interactive chatbot session"""
    # Setup readline for command history and completion
    setup_readline()

    # Load cache
    cache = load_cache()

    # Print welcome message
    print_welcome()

    # Initialize conversation history
    conversation = [
        {
            "role": "system",
            "content": """You are a network diagnostics and cybersecurity specialist working with an experienced security admin/pentester. 
            You can also call tools for network diagnosis, security scanning, and for pentest reconnaissance.
            You have access to various networking tools that can be called to diagnose problems or to do pentest reconnaissance and security scanning.
            You are capable of reasoning about network and security issues, but you must use the tools to get real data.

IMPORTANT: For any network-related questions about connectivity, DNS, ping, latency, IP addresses, routing, or network performance, you MUST use the appropriate tools to get real data. Do not guess or provide generic answers without using tools. 

CRITICAL: NEVER include fake tool results, sample data, or "Tool result:" text in your responses. Only call tools using the specified format and wait for the actual results.

CRITICAL: NEVER attempt to infer NAT status from speed test results, responsiveness metrics, or other unrelated network data. NAT detection requires checking IP addresses directly via check_nat_status.

When you need specific information, you can call a tool using this format:

TOOL: tool_name
ARGS: {"arg_name": "value"} (or {} if no arguments needed)

STOP after the tool call. Do NOT include any text like "Tool result:", example output, or sample data. The system will execute the tool and provide the real result.

CONTEXT AWARENESS: When users ask about "we", "our machine", "this system", or "localhost", they mean the LOCAL machine you're running on. When they specify IP addresses or hostnames, they mean REMOTE targets.

IMPORTANT: Do NOT use pentesting tools (nmap_scan, os_detection_scan, etc.) for questions about the local machine. Use local system tools instead.

Examples of when you MUST use tools:
- Questions about ping times or connectivity → use ping_target
- DNS resolution issues → use check_dns_resolvers
- DNS root server issues → use check_dns_root_servers
- IP address questions → use get_external_ip or get_local_ip
- Website accessibility → use check_websites
- General connectivity → use check_internet_connection or check_local_network
- NAT questions (Are we behind NAT? Are we using NAT? NAT status?) → ALWAYS use check_nat_status
- Speed or bandwidth questions → use run_speed_test
- Questions about the local operating system (this machine, localhost) → use get_os_info
- Port scanning or service detection on remote hosts → use nmap_scan, quick_port_scan, service_version_scan
- Network discovery or host discovery on remote networks → use network_discovery
- OS fingerprinting of remote hosts/targets → use os_detection_scan
- Comprehensive security scanning → use comprehensive_scan

Be direct, concise, and opinionated. Use technical shorthand. You are an expert conversing with another expert. 
Skip basic explanations of common technologies. 
Assume the user understands networking concepts, protocols, and security tools.

CRITICAL: Keep all responses extremely brief. One to two sentences maximum. 
When using tools, provide only essential context before the tool call - no lengthy explanations.
After tool execution, interpret results concisely without repeating obvious information.
"""
        }
    ]

    # Tool system message with available tools
    tools = get_available_tools()
    tool_descriptions = []
    for name, func in tools.items():
        desc = func.__doc__.split('\n')[0].strip() if func.__doc__ else f"Tool: {name}"
        
        # Get function signature to show parameters
        import inspect
        try:
            sig = inspect.signature(func)
            params = []
            for param_name, param in sig.parameters.items():
                if param.default == inspect.Parameter.empty:
                    params.append(f"{param_name}")
                else:
                    params.append(f"{param_name}={param.default}")
            
            if params:
                signature = f"({', '.join(params)})"
            else:
                signature = "()"
            
            tool_descriptions.append(f"- {name}{signature}: {desc}")
        except Exception:
            # Fallback if signature inspection fails
            tool_descriptions.append(f"- {name}: {desc}")

    # Add tool descriptions to system message
    tool_system_message = {
        "role": "system",
        "content": "Available tools:\n" + "\n".join(tool_descriptions)
    }
    conversation.append(tool_system_message)

    # Main interaction loop
    try:
        while True:
            # Get user input
            user_input = input(f"{USER_COLOR}User: {Style.RESET_ALL}")

            # Check if it's a command
            handled, should_exit = handle_command(user_input, cache)
            if should_exit:
                break
            if handled:
                continue

            # If it's not a command, process as normal input
            conversation.append({"role": "user", "content": user_input})

            try:
                # Generate response using Ollama API
                response = ollama.chat(
                    model=model_name,
                    messages=conversation,
                    options={"temperature": 0.1}  # Lower temperature for more deterministic responses
                )

                # Get the response content
                content = response["message"]["content"]

                # Check for thinking patterns in the response
                thinking, content = extract_thinking(content)

                # Show thinking if available
                if thinking:

                    print_thinking(thinking)

                # Check for tool calls
                tool_name, args = parse_tool_call(content)

                if tool_name:

                    # Extract planning section concisely
                    planning_content = _extract_planning_section(content)
                    if planning_content:
                        print_planning(planning_content)

                    # Check if the tool exists
                    if tool_name in tools:
                        print_tool_execution(tool_name)

                        try:
                            # Execute the tool using v3 registry (filters invalid parameters)
                            registry = get_tool_registry()
                            tool_result = registry.execute_tool(tool_name, args, mode="chatbot")
                            # Tool result suppressed for clean output

                            # Update cache with result
                            cache[tool_name] = tool_result
                            save_cache(cache)

                            # Add tool execution and result to conversation
                            conversation.append({"role": "assistant", "content": content})
                            conversation.append({"role": "system", "content": f"Tool result: {tool_result}"})

                            # Get follow-up response with streaming
                            follow_up_stream = ollama.chat(
                                model=model_name,
                                messages=conversation,
                                options={"temperature": 0.7},
                                stream=True
                            )

                            # Collect streamed response and display in real-time with number colorization
                            print(f"{ASSISTANT_COLOR}Chatbot: {Style.RESET_ALL}", end="", flush=True)
                            full_response = ""
                            for chunk in follow_up_stream:
                                content_chunk = chunk["message"]["content"]
                                full_response += content_chunk
                                
                                # Apply number colorization to chunk if Rich is available
                                if RICH_AVAILABLE:
                                    from rich.text import Text
                                    colored_chunk = colorize_numbers(content_chunk)
                                    chunk_text = Text.from_markup(colored_chunk)
                                    console.print(chunk_text, end="")
                                else:
                                    print(content_chunk, end="", flush=True)
                            print()  # New line when streaming is complete

                            # Add complete response to conversation
                            conversation.append({"role": "assistant", "content": full_response})

                            # Note: We don't extract thinking/planning from streamed responses
                            # since they're typically just the final answer after tool execution

                        except Exception as e:

                            error_msg = f"Error executing tool {tool_name}: {Fore.RED}{e}{Style.RESET_ALL}"
                            print_error(error_msg)
                            conversation.append({"role": "system", "content": error_msg})

                    else:

                        error_msg = f"Tool not found: {tool_name}"
                        print_error(error_msg)
                        conversation.append({"role": "system", "content": error_msg})

                else:

                    # No tool call - check if this is a network-related question and add warning
                    network_keywords = ['ping', 'network', 'connectivity', 'internet', 'dns', 'ip', 'connection', 'latency', 'speed', 'bandwidth', 'traceroute', 'route', 'packet', 'loss', 'nat', 'firewall', 'port', 'external', 'local']
                    user_message = conversation[-1].get('content', '').lower() if conversation else ''
                    
                    is_network_question = any(keyword in user_message for keyword in network_keywords)
                    
                    if is_network_question:
                        warning_msg = "WARNING: Network diagnostic questions should use tools for accurate data. Response may contain inaccurate information."
                        conversation.append({"role": "system", "content": warning_msg})
                        print(f"{Fore.YELLOW}[WARN] {warning_msg}{Style.RESET_ALL}")

                    # No tool call, just display the response
                    conversation.append({"role": "assistant", "content": content})

                    print(f"{Fore.MAGENTA}DEBUG: From chatbot.py. Assistant response (no tool call): {content}{Style.RESET_ALL}")

                    print_assistant(content)

                # Trim conversation history if too long
                if len(conversation) > MAX_CONVERSATION_LENGTH + 2:  # +2 for the system messages

                    # Keep the first two system messages and the most recent history
                    conversation = conversation[:2] + conversation[-(MAX_CONVERSATION_LENGTH):]

            except Exception as e:
                print_error(f"Error generating response: {Fore.RED}{e}{Style.RESET_ALL}")

    except KeyboardInterrupt:

        print("\nExiting...")

    except Exception as e:

        print_error(f"Unexpected error: {Fore.RED}{e}{Style.RESET_ALL}")

    finally:
        # Save cache before exiting
        save_cache(cache)


def _extract_planning_section(content: str) -> Optional[str]:
    """Extract planning/reasoning section before tool call, keeping it concise"""
    # Find the TOOL: line
    tool_index = content.find("TOOL:")
    if tool_index == -1:
        return None
    
    # Get text before the tool call
    planning_text = content[:tool_index].strip()
    
    # If planning text is too long, take first sentence or first 100 chars
    if len(planning_text) > 100:
        # Try to find first sentence
        sentences = planning_text.split('. ')
        if len(sentences) > 0 and len(sentences[0]) < 100:
            return sentences[0] + '.'
        else:
            # Truncate to 100 chars
            return planning_text[:97] + "..."
    
    return planning_text if planning_text else None