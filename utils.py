"""
Utility functions for Instability v2

This module provides helper functions for the chatbot interface, including
colorized output, terminal utilities, and common formatting functions.
"""

import os
import sys
import platform
import time
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from colorama import Fore, Style, init

# Import centralized error handling
from core.error_handling import ErrorType, ErrorCode, get_timeout

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
ASCII_HEADER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Instability_ASCII_Header_v3.txt")

# Try to load the ASCII header from file, or use fallback if file not found
try:
    with open(ASCII_HEADER_FILE, 'r') as f:
        WELCOME_HEADER = f.read()
except FileNotFoundError:
    # Fallback ASCII art if file is not found
    WELCOME_HEADER = r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║             INSTABILITY NETWORK DIAGNOSTICS v3               ║
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


def ollama_shorten_output(text: str, max_lines: int = 15, max_chars: int = 1000) -> str:
    """Use Ollama API to intelligently shorten long output for terminal display

    Args:
        text: The text to shorten
        max_lines: Maximum number of lines to show (fallback limit)
        max_chars: Maximum number of characters to show (fallback limit)

    Returns:
        AI-shortened text or fallback truncated text if Ollama unavailable
    """
    # Check if text is short enough already
    lines = text.split('\n')
    if len(lines) <= max_lines and len(text) <= max_chars:
        return text
    
    # Try Ollama shortening first
    try:
        import ollama
        from config import OLLAMA_DEFAULT_MODEL
        
        # Use the same model as the main chatbot to avoid hallucination
        shortening_model = OLLAMA_DEFAULT_MODEL
        
        # Create a shortening prompt for postgraduate level
        shortening_conversation = [
            {
                "role": "system",
                "content": """You are a technical writing assistant. Your task is to shorten and improve text while maintaining all essential information and technical accuracy.

Requirements:
- Write at postgraduate master's level (sophisticated but clear language)
- Preserve all critical technical details, numbers, and findings
- Remove redundancy and verbose explanations
- Use precise, professional terminology
- Maintain logical flow and structure
- Keep diagnostic results, error messages, and specific data intact
- Target output should be roughly 40-50% of original length

CRITICAL: Output ONLY the shortened text. Do not include any preamble, introduction, or explanation about what you did. Start directly with the shortened content."""
            },
            {
                "role": "user", 
                "content": f"Shorten this technical output while preserving all essential information:\n\n{text}"
            }
        ]
        
        # Call Ollama with llama3.1:8b for better text processing
        response = ollama.chat(
            model=shortening_model,
            messages=shortening_conversation,
            options={
                "temperature": 0.1,  # Low temperature for consistent, factual shortening
                "top_p": 0.9
            }
        )
        
        shortened_text = response["message"]["content"].strip()
        
        # Verify the shortened text is actually shorter
        if len(shortened_text) < len(text):
            return shortened_text
        else:
            # If not shorter, fall back to truncation
            return truncate_long_output_fallback(text, max_lines, max_chars)
            
    except Exception as e:
        # Fallback to original truncation method if Ollama fails
        print(f"{WARNING_COLOR}Ollama shortening failed ({e}), using fallback truncation{Style.RESET_ALL}")
        return truncate_long_output_fallback(text, max_lines, max_chars)


def truncate_long_output_fallback(text: str, max_lines: int = 15, max_chars: int = 1000) -> str:
    """Fallback truncation method (original implementation)

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


# Legacy alias for backward compatibility
def truncate_long_output(text: str, max_lines: int = 15, max_chars: int = 1000) -> str:
    """Legacy alias - now uses Ollama-based shortening"""
    return ollama_shorten_output(text, max_lines, max_chars)


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

    # Format with consistent style and Markdown code blocks for monospace output
    formatted = f"Tool: {tool_name}\n"
    formatted += "=" * (len(tool_name) + 6) + "\n"
    
    # If the result looks like structured data or code, wrap it in a Markdown code block
    if any(pattern in truncated_result for pattern in ['{', '}', '[', ']', ':', '|', '=', '/']):
        formatted += f"```\n{truncated_result}\n```"
    else:
        formatted += truncated_result

    return formatted


def colorize_numbers(text: str) -> str:
    """Add Rich markup to colorize numbers and adjacent characters in text.
    
    Args:
        text: The text to process
        
    Returns:
        Text with Rich markup tags around numbers and adjacent characters
    """
    # Skip processing if text contains code blocks to avoid coloring code
    if '```' in text:
        return text
    
    # Skip if text has many backticks (likely inline code)
    if text.count('`') >= 4:
        return text
    
    # Single comprehensive pattern that captures:
    # - Any sequence containing at least one digit
    # - Including adjacent letters, dots, hyphens, underscores
    # - Word boundaries to avoid partial matches
    pattern = r'\b[a-zA-Z0-9._-]*\d[a-zA-Z0-9._-]*\b'
    
    def colorize_match(match):
        matched_text = match.group(0)
        return f'[red]{matched_text}[/red]'
    
    # Apply the pattern
    colored_text = re.sub(pattern, colorize_match, text)
    
    return colored_text


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


# Standardized Tool Result Format Functions
def create_tool_result(
    success: bool,
    tool_name: str,
    execution_time: float,
    command_executed: str = "",
    target: Optional[str] = None,
    stdout: str = "",
    stderr: str = "",
    parsed_data: Optional[Dict[str, Any]] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    exit_code: int = 0,
    options_used: Optional[Dict[str, Any]] = None,
    start_time: Optional[datetime] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized tool result dictionary following the v3 interface standard.
    
    Args:
        success: Whether the tool executed successfully
        tool_name: Name of the tool that was executed
        execution_time: Total execution time in seconds
        command_executed: Human-readable command or operation
        target: Target of the operation (IP, hostname, etc.)
        stdout: Raw stdout/primary output
        stderr: Raw stderr/error output
        parsed_data: Structured, tool-specific data
        error_type: Error category ("network", "timeout", "execution", "invalid_target")
        error_message: Human-readable error description
        exit_code: Exit code (0 = success, >0 = error)
        options_used: Parameters/options passed to the tool
        start_time: Start timestamp (uses current time if not provided)
        **kwargs: Additional tool-specific fields
    
    Returns:
        Standardized tool result dictionary
    """
    if start_time is None:
        start_time = datetime.now()
    
    result = {
        # Core execution metadata (REQUIRED)
        "success": success,
        "execution_time": execution_time,
        "timestamp": start_time.isoformat(),
        "tool_name": tool_name,
        
        # Command/execution details (REQUIRED)
        "command_executed": command_executed,
        "exit_code": exit_code,
        "target": target,
        "options_used": options_used or {},
        
        # Output data (REQUIRED)
        "stdout": stdout,
        "stderr": stderr,
        "parsed_data": parsed_data or {},
        
        # Error handling (REQUIRED)
        "error_type": error_type,
        "error_message": error_message,
    }
    
    # Add any additional tool-specific fields
    result.update(kwargs)
    
    return result


def create_success_result(
    tool_name: str,
    execution_time: float,
    parsed_data: Dict[str, Any],
    command_executed: str = "",
    target: Optional[str] = None,
    stdout: str = "",
    options_used: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized successful tool result.
    
    Args:
        tool_name: Name of the tool
        execution_time: Execution time in seconds
        parsed_data: Structured tool output
        command_executed: Command that was executed
        target: Target of the operation
        stdout: Raw output
        options_used: Options passed to the tool
        **kwargs: Additional tool-specific fields
        
    Returns:
        Standardized success result
    """
    return create_tool_result(
        success=True,
        tool_name=tool_name,
        execution_time=execution_time,
        command_executed=command_executed,
        target=target,
        stdout=stdout,
        stderr="",
        parsed_data=parsed_data,
        error_type=None,
        error_message=None,
        exit_code=0,
        options_used=options_used,
        **kwargs
    )


def create_error_result(
    tool_name: str,
    execution_time: float,
    error_message: str,
    error_type: str = "execution",
    command_executed: str = "",
    target: Optional[str] = None,
    stderr: str = "",
    exit_code: int = 1,
    options_used: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized error tool result.
    
    Args:
        tool_name: Name of the tool
        execution_time: Execution time in seconds
        error_message: Description of the error
        error_type: Category of error ("network", "timeout", "execution", "invalid_target")
        command_executed: Command that was attempted
        target: Target of the operation
        stderr: Raw error output
        exit_code: Exit code (>0 for errors)
        options_used: Options passed to the tool
        **kwargs: Additional tool-specific fields
        
    Returns:
        Standardized error result
    """
    # Try to map legacy error types to new ErrorType enum
    error_type_mapping = {
        "network": ErrorType.NETWORK,
        "timeout": ErrorType.NETWORK,
        "execution": ErrorType.EXECUTION,
        "invalid_target": ErrorType.INPUT,
        "system": ErrorType.SYSTEM,
        "configuration": ErrorType.CONFIGURATION
    }
    
    # Map to appropriate error code
    error_code_mapping = {
        "network": ErrorCode.CONNECTION_FAILED,
        "timeout": ErrorCode.TIMEOUT,
        "execution": ErrorCode.COMMAND_FAILED,
        "invalid_target": ErrorCode.INVALID_TARGET,
        "system": ErrorCode.UNEXPECTED_ERROR,
        "configuration": ErrorCode.INVALID_CONFIG
    }
    
    mapped_type = error_type_mapping.get(error_type, ErrorType.EXECUTION)
    mapped_code = error_code_mapping.get(error_type, ErrorCode.UNEXPECTED_ERROR)
    
    # Import here to avoid circular import
    from core.error_handling import create_error_response
    
    return create_error_response(
        error_type=mapped_type,
        error_code=mapped_code,
        message=error_message,
        tool_name=tool_name,
        execution_time=execution_time,
        target=target,
        details={
            "command": command_executed,
            "stderr": stderr,
            "exit_code": exit_code,
            "options": options_used or {}
        },
        **kwargs
    )


def wrap_legacy_result(
    tool_name: str,
    legacy_result: Any,
    execution_time: float,
    command_executed: str = "",
    target: Optional[str] = None,
    options_used: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Wrap a legacy tool result (string, tuple, list) in the standardized format.
    
    Args:
        tool_name: Name of the tool
        legacy_result: The original result from the legacy tool
        execution_time: Execution time in seconds
        command_executed: Command that was executed
        target: Target of the operation
        options_used: Options passed to the tool
        
    Returns:
        Standardized tool result
    """
    if isinstance(legacy_result, str):
        return create_success_result(
            tool_name=tool_name,
            execution_time=execution_time,
            parsed_data={"result": legacy_result},
            command_executed=command_executed,
            target=target,
            stdout=legacy_result,
            options_used=options_used
        )
    elif isinstance(legacy_result, (list, tuple)):
        return create_success_result(
            tool_name=tool_name,
            execution_time=execution_time,
            parsed_data={"result": list(legacy_result)},
            command_executed=command_executed,
            target=target,
            stdout=str(legacy_result),
            options_used=options_used
        )
    elif isinstance(legacy_result, dict):
        return create_success_result(
            tool_name=tool_name,
            execution_time=execution_time,
            parsed_data=legacy_result,
            command_executed=command_executed,
            target=target,
            stdout=str(legacy_result),
            options_used=options_used
        )
    else:
        return create_success_result(
            tool_name=tool_name,
            execution_time=execution_time,
            parsed_data={"result": str(legacy_result)},
            command_executed=command_executed,
            target=target,
            stdout=str(legacy_result),
            options_used=options_used
        )


def standardize_tool_output(tool_name: str = None):
    """
    Decorator to automatically wrap legacy tool functions with standardized output format.
    
    Args:
        tool_name: Optional custom tool name (uses function name if not provided)
        
    Usage:
        @standardize_tool_output()
        def my_tool(target):
            return "some result"
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            actual_tool_name = tool_name or func.__name__
            start_time = datetime.now()

            target = None

            try:
                # Extract target from args/kwargs if present
                target = None
                if args:
                    target = str(args[0]) if args[0] is not None else None
                elif 'target' in kwargs:
                    target = str(kwargs['target'])
                elif 'host' in kwargs:
                    target = str(kwargs['host'])
                elif 'hostname' in kwargs:
                    target = str(kwargs['hostname'])
                
                # Call the original function
                legacy_result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Wrap result in standardized format
                return wrap_legacy_result(
                    tool_name=actual_tool_name,
                    legacy_result=legacy_result,
                    execution_time=execution_time,
                    command_executed=f"{func.__name__}({', '.join(str(arg) for arg in args)})",
                    target=target,
                    options_used=kwargs
                )
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Determine error type based on exception
                error_type = "execution"
                if "timeout" in str(e).lower():
                    error_type = "timeout"
                elif "connection" in str(e).lower() or "network" in str(e).lower():
                    error_type = "network"
                elif "permission" in str(e).lower() or "denied" in str(e).lower():
                    error_type = "system"
                elif "invalid" in str(e).lower() or "format" in str(e).lower():
                    error_type = "invalid_target"
                
                return create_error_result(
                    tool_name=actual_tool_name,
                    execution_time=execution_time,
                    error_message=str(e),
                    error_type=error_type,
                    command_executed=f"{func.__name__}({', '.join(str(arg) for arg in args)})",
                    stderr=str(e),
                    target=target
                )
        
        # Preserve original function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        
        return wrapper
    return decorator
