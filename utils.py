"""
Utility functions for Instability v2

This module provides helper functions for the chatbot interface, including
colorized output, terminal utilities, and common formatting functions.
"""

import os
import sys
import platform
import time
from typing import Dict, Any, Optional, List, Tuple
from colorama import Fore, Style, init

# Import Rich for Markdown rendering if available
try:
    from rich.console import Console
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
    # Create a console instance
    console = Console()
except ImportError:
    RICH_AVAILABLE = False

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Terminal color constants for consistent UI
USER_COLOR = Fore.CYAN
ASSISTANT_COLOR = Fore.BLUE
TOOL_COLOR = Fore.GREEN
ERROR_COLOR = Fore.RED
WARNING_COLOR = Fore.YELLOW
THINKING_COLOR = Style.DIM

# ASCII Art for the welcome header
# Load from the ASCII art file
ASCII_HEADER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Instability_ASCII_Header_v2.txt")

# Try to load the ASCII header from file, or use fallback if file not found
try:
    with open(ASCII_HEADER_FILE, 'r') as f:
        WELCOME_HEADER = f.read()
except FileNotFoundError:
    # Fallback ASCII art if file is not found
    WELCOME_HEADER = r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║             INSTABILITY NETWORK DIAGNOSTICS v2               ║
║                                                              ║
║        A terminal-based network diagnostic assistant         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


# Output functions
def print_welcome_header():
    """Print the welcome header with ASCII art"""
    print(f"\n{USER_COLOR}{WELCOME_HEADER}{Style.RESET_ALL}")


def print_user_prompt():
    """Print the user prompt"""
    return f"{USER_COLOR}User: {Style.RESET_ALL}"


def print_thinking(message: str):
    """Print a thinking/reasoning message from the assistant"""
    print(f"{ASSISTANT_COLOR}Chatbot (thinking): {Style.RESET_ALL}{THINKING_COLOR}{message}{Style.RESET_ALL}")


# This function is a duplicate of a function in chatbot.py
# def print_assistant(message: str):
#     """Print a message from the assistant with Markdown support"""
#     if RICH_AVAILABLE and any(md_marker in message for md_marker in ["```", "*", "_", "##", "`"]):
#         # Print the prefix with colorama
#         print(f"{ASSISTANT_COLOR}Chatbot: {Style.RESET_ALL}", end="")
#         # Use Rich to render the Markdown content
#         md = Markdown(message)
#         console.print(md)
#     else:
#         # Regular text, use normal print
#         print(f"{ASSISTANT_COLOR}Chatbot: {Style.RESET_ALL}{message}")


def print_tool_execution(tool_name: str):
    """Print a tool execution message"""
    print(f"{ASSISTANT_COLOR}Chatbot (executing tool): {TOOL_COLOR}{tool_name}{Style.RESET_ALL}")


def print_tool_result(result: str):
    """Print a tool execution result"""
    print(f"{ASSISTANT_COLOR}Chatbot (tool completed): {TOOL_COLOR}Result: {Style.RESET_ALL}{result}")


def print_error(message: str):
    """Print an error message"""
    print(f"{ERROR_COLOR}Error: {message}{Style.RESET_ALL}")


def print_warning(message: str):
    """Print a warning message"""
    print(f"{WARNING_COLOR}Warning: {message}{Style.RESET_ALL}")


def print_success(message: str):
    """Print a success message"""
    print(f"{TOOL_COLOR}Success: {message}{Style.RESET_ALL}")


def print_command_list(commands: Dict[str, str]):
    """Print a list of commands with descriptions"""
    print(f"\n{USER_COLOR}Available commands:{Style.RESET_ALL}")
    for cmd, desc in commands.items():
        print(f"  {USER_COLOR}{cmd}{Style.RESET_ALL} - {desc}")


def print_tool_list(tools: Dict[str, Any]):
    """Print a list of available tools"""
    print(f"\n{USER_COLOR}Available tools:{Style.RESET_ALL}")
    for name, func in tools.items():
        desc = func.__doc__.split('\n')[0].strip() if func.__doc__ else "No description"
        print(f"  {TOOL_COLOR}{name}{Style.RESET_ALL} - {desc}")


# Terminal utilities
def clear_screen():
    """Clear the terminal screen in a cross-platform way"""
    os.system('cls' if platform.system().lower() == 'windows' else 'clear')


def get_terminal_size() -> Tuple[int, int]:
    """Get the current terminal size

    Returns:
        Tuple of (width, height)
    """
    try:
        columns, rows = os.get_terminal_size()
        return columns, rows
    except (AttributeError, OSError):
        # Fallback if terminal size can't be determined
        return 80, 24


def format_output_to_width(text: str, width: Optional[int] = None) -> str:
    """Format text to fit within the terminal width

    Args:
        text: The text to format
        width: Optional custom width (uses terminal width if not specified)

    Returns:
        Formatted text
    """
    if width is None:
        width, _ = get_terminal_size()
        # Leave some margin
        width = max(40, width - 4)

    # Split into lines, respecting existing line breaks
    lines = text.split('\n')
    result = []

    for line in lines:
        # If line is shorter than width, keep it as is
        if len(line) <= width:
            result.append(line)
            continue

        # Otherwise, wrap the line
        current_line = ''
        for word in line.split(' '):
            if len(current_line) + len(word) + 1 <= width:
                if current_line:
                    current_line += ' ' + word
                else:
                    current_line = word
            else:
                result.append(current_line)
                current_line = word

        if current_line:
            result.append(current_line)

    return '\n'.join(result)


def truncate_long_output(text: str, max_lines: int = 15, max_chars: int = 1000) -> str:
    """Truncate long output to avoid flooding the terminal

    Args:
        text: The text to truncate
        max_lines: Maximum number of lines to show
        max_chars: Maximum number of characters to show

    Returns:
        Truncated text with indicator if truncated
    """
    lines = text.split('\n')

    # Truncate by lines
    if len(lines) > max_lines:
        truncated = lines[:max_lines]
        truncated.append(f"... (truncated, {len(lines) - max_lines} more lines)")
        return '\n'.join(truncated)

    # Truncate by characters
    if len(text) > max_chars:
        return text[:max_chars] + f"... (truncated, {len(text) - max_chars} more characters)"

    return text


# String formatting utilities
def format_tool_result(tool_name: str, result: str) -> str:
    """Format a tool result in a consistent way, with Markdown support

    Args:
        tool_name: The name of the tool
        result: The result string

    Returns:
        Formatted result
    """
    # Truncate very long results
    truncated_result = truncate_long_output(result)

    # Format with consistent style and markdown code blocks for monospace output
    formatted = f"Tool: {tool_name}\n"
    formatted += "=" * (len(tool_name) + 6) + "\n"
    
    # If the result looks like structured data or code, wrap it in a markdown code block
    if any(pattern in truncated_result for pattern in ['{', '}', '[', ']', ':', '|', '=', '/']):
        formatted += f"```\n{truncated_result}\n```"
    else:
        formatted += truncated_result

    return formatted


def extract_thinking(content: str) -> Tuple[Optional[str], str]:
    """Extract thinking section from assistant's response

    Args:
        content: The content to process

    Returns:
        Tuple of (extracted_thinking, remaining_content)
    """
    thinking = None

    # Check for thinking pattern 1: <think>...</think>
    if "<think>" in content and "</think>" in content:
        thinking_start = content.find("<think>") + len("<think>")
        thinking_end = content.find("</think>")

        if thinking_end > thinking_start:
            thinking = content[thinking_start:thinking_end].strip()
            # Remove thinking tags from content
            content = content[:thinking_start - len("<think>")] + content[thinking_end + len("</think>"):].strip()

    # Check for thinking pattern 2: [thinking]...[/thinking]
    elif "[thinking]" in content and "[/thinking]" in content:
        thinking_start = content.find("[thinking]") + len("[thinking]")
        thinking_end = content.find("[/thinking]")

        if thinking_end > thinking_start:
            thinking = content[thinking_start:thinking_end].strip()
            # Remove thinking tags from content
            content = content[:thinking_start - len("[thinking]")] + content[thinking_end + len("[/thinking]"):].strip()

    return thinking, content


# Progress indicators
def show_spinner(message: str, duration: float = 1.0):
    """Show a simple spinner with a message

    Args:
        message: The message to display
        duration: How long to show the spinner (seconds)
    """
    spinner_chars = ['|', '/', '-', '\\']
    end_time = time.time() + duration

    i = 0
    try:
        while time.time() < end_time:
            sys.stdout.write(f"\r{message} {spinner_chars[i % len(spinner_chars)]}")
            sys.stdout.flush()
            i += 1
            time.sleep(0.1)

        # Clear the spinner
        sys.stdout.write(f"\r{' ' * (len(message) + 2)}\r")
        sys.stdout.flush()
    except KeyboardInterrupt:
        # Clear the spinner on interrupt
        sys.stdout.write(f"\r{' ' * (len(message) + 2)}\r")
        sys.stdout.flush()
        raise


def is_tool_call(content: str) -> bool:
    """Determine if a message contains a tool call

    Args:
        content: The message content to check

    Returns:
        True if the message appears to contain a tool call
    """
    # Check for standard tool call format
    return "TOOL:" in content or "TOOL: " in content


def sanitize_command(command: str) -> str:
    """Sanitize user command input

    Args:
        command: The command to sanitize

    Returns:
        Sanitized command string
    """
    # Remove leading/trailing whitespace
    command = command.strip()

    # Remove any potentially problematic characters
    # (more sanitization could be added if needed)
    command = command.replace(';', '')

    return command
