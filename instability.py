#!/usr/bin/env python3
"""
Instability.py v2 - Network diagnostic chatbot

A terminal-based network diagnostic tool that provides an interactive interface
for diagnosing and troubleshooting network connectivity issues, even during
complete network outages.

Usage:
    python instability.py chatbot [--model MODEL] - Run the interactive chatbot
    python instability.py manual [tool]           - Run specific tools manually
    python instability.py test                    - Test the environment setup
    python instability.py help                    - Show help information
    
Options:
    --model, -m MODEL    Specify Ollama model name (default: phi3:14b)
"""

import sys
import argparse
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init(autoreset=True)


# Will be implemented in separate modules
def start_chatbot_mode(model_name=None):
    """Start the interactive chatbot"""
    try:
        from chatbot import start_interactive_session
        start_interactive_session(model_name=model_name)
    except ImportError:
        print(
            f"{Fore.RED}Error: Chatbot module not found. Make sure chatbot.py is in the same directory.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error starting chatbot: {e}{Style.RESET_ALL}")


def run_manual_mode(tool_name=None):
    """Run specific tools manually"""
    try:
        from network_diagnostics import get_available_tools, execute_tool

        # Get all available tools
        tools = get_available_tools()

        if tool_name is None:
            # List available tools
            print(f"{Fore.CYAN}Available tools:{Style.RESET_ALL}")
            for name, func in tools.items():
                desc = func.__doc__.split('\n')[0].strip() if func.__doc__ else "No description"
                print(f"  {Fore.GREEN}{name}{Style.RESET_ALL}: {desc}")
            print(f"\nUse '{Fore.CYAN}python instability.py manual all{Style.RESET_ALL}' to run all tools")
            print(f"Use '{Fore.CYAN}python instability.py manual <tool_name>{Style.RESET_ALL}' to run a specific tool")
        elif tool_name.lower() == 'all':
            # Run all tools
            print(f"{Fore.CYAN}Running all tools:{Style.RESET_ALL}")
            for name, func in tools.items():
                print(f"\n{Fore.GREEN}Running {name}...{Style.RESET_ALL}")
                try:
                    result = execute_tool(name)
                    print(f"Result: {result}")
                except Exception as e:
                    print(f"{Fore.RED}Error executing {name}: {e}{Style.RESET_ALL}")
        elif tool_name in tools:
            # Run specific tool
            print(f"{Fore.GREEN}Running {tool_name}...{Style.RESET_ALL}")
            try:
                result = execute_tool(tool_name)
                print(f"Result: {result}")
            except Exception as e:
                print(f"{Fore.RED}Error executing {tool_name}: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Tool '{tool_name}' not found.{Style.RESET_ALL}")
            print(f"Available tools: {', '.join(tools.keys())}")
    except ImportError:
        print(f"{Fore.RED}Error: Tools module not found. Make sure tools.py is in the same directory.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error in manual mode: {e}{Style.RESET_ALL}")


def run_test_mode():
    """Test the environment setup"""
    print(f"{Fore.CYAN}Running in test mode...{Style.RESET_ALL}")

    # Test Python version
    import platform
    py_version = platform.python_version()
    print(f"Python version: {py_version}")

    # Test colorama
    print(f"{Fore.GREEN}Colorama is working{Style.RESET_ALL}")

    # Test Ollama
    try:
        import ollama
        models = ollama.list()
        print(f"{Fore.GREEN}Ollama is available{Style.RESET_ALL}")
        print(f"Available models: {', '.join([m['name'] for m in models['models']])}")

        # Check for phi3:14b model
        has_phi3 = any(m['name'] == 'phi3:14b' for m in models['models'])
        if has_phi3:
            print(f"{Fore.GREEN}phi3:14b model is available{Style.RESET_ALL}")
        else:
            print(
                f"{Fore.YELLOW}phi3:14b model not found. You can install it with: ollama pull phi3:14b{Style.RESET_ALL}")
    except ImportError:
        print(f"{Fore.RED}Ollama Python package not installed.{Style.RESET_ALL}")
        print(f"Install with: pip install ollama")
    except Exception as e:
        print(f"{Fore.RED}Error connecting to Ollama: {e}{Style.RESET_ALL}")
        print(f"Ensure Ollama is running with: ollama serve")

    # Test readline (for command history and completion)
    try:
        if sys.platform == 'darwin' or sys.platform.startswith('linux') or sys.platform.lower() == 'macos':
            import readline
            print(f"{Fore.GREEN}readline is available for command history{Style.RESET_ALL}")
        elif sys.platform == 'win32':
            try:
                import pyreadline3
                print(f"{Fore.GREEN}pyreadline3 is available for command history{Style.RESET_ALL}")
            except ImportError:
                print(
                    f"{Fore.YELLOW}pyreadline3 not installed. Command history may not work on Windows.{Style.RESET_ALL}")
                print(f"Install with: pip install pyreadline3")
    except ImportError:
        print(f"{Fore.YELLOW}readline not available. Command history will be limited.{Style.RESET_ALL}")

    # Test network diagnostics module
    try:
        from network_diagnostics import get_available_tools
        tools = get_available_tools()
        print(f"{Fore.GREEN}Network diagnostics module is available with {len(tools)} tools{Style.RESET_ALL}")
    except ImportError:
        print(f"{Fore.RED}Network diagnostics module not found. Make sure network_diagnostics.py is in the same directory.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error loading network diagnostics: {e}{Style.RESET_ALL}")


def run_tests_mode():
    """Run the test suite"""
    print(f"{Fore.CYAN}Running test suite...{Style.RESET_ALL}")
    
    try:
        # Import and run the test runner
        from tests.run_tests import discover_and_run_tests
        return discover_and_run_tests()
    except ImportError:
        print(f"{Fore.RED}Error: Tests module not found. Make sure tests directory exists.{Style.RESET_ALL}")
        return 1
    except Exception as e:
        print(f"{Fore.RED}Error running tests: {e}{Style.RESET_ALL}")
        return 1


def show_help():
    """Display help information"""
    print(f"{Fore.CYAN}Instability.py v2 - Network diagnostic chatbot{Style.RESET_ALL}")
    print("\nA terminal-based network diagnostic tool that provides an interactive interface")
    print("for diagnosing and troubleshooting network connectivity issues.")
    print("\nUsage:")
    print(f"  {Fore.GREEN}python instability.py chatbot{Style.RESET_ALL}")
    print("      Start the interactive chatbot")
    print(f"  {Fore.GREEN}python instability.py manual [tool_name]{Style.RESET_ALL}")
    print("      Run a specific tool or list available tools")
    print(f"  {Fore.GREEN}python instability.py test{Style.RESET_ALL}")
    print("      Test the environment setup")
    print(f"  {Fore.GREEN}python instability.py run-tests{Style.RESET_ALL}")
    print("      Run all test scripts in the tests directory")
    print(f"  {Fore.GREEN}python instability.py help{Style.RESET_ALL}")
    print("      Show this help information")
    print("\nChatbot Commands:")
    print(f"  {Fore.GREEN}/help{Style.RESET_ALL}  - Show available commands and tools")
    print(f"  {Fore.GREEN}/exit{Style.RESET_ALL}  - Exit the chatbot")
    print("\nNote: This tool is designed to function even during network outages")
    print("      and can provide diagnostic information without internet access.")


def main():
    """Main entry point for instability.py"""
    parser = argparse.ArgumentParser(description="Network diagnostic chatbot")
    parser.add_argument('mode', nargs='?', choices=['chatbot', 'manual', 'test', 'run-tests', 'help'],
                        default='help', help='Mode of operation')
    parser.add_argument('tool_name', nargs='?', help='Specific tool to run in manual mode')
    parser.add_argument('--model', '-m', type=str, default='phi3:14b',
                        help='Ollama model name to use for chatbot (default: phi3:14b)')
    args = parser.parse_args()

    # Handle different modes
    if args.mode == 'chatbot':
        start_chatbot_mode(model_name=args.model)
    elif args.mode == 'manual':
        run_manual_mode(args.tool_name)
    elif args.mode == 'test':
        run_test_mode()
    elif args.mode == 'run-tests':
        return run_tests_mode()
    elif args.mode == 'help':
        show_help()
    else:
        # This should not happen due to choices in argparse
        print(f"{Fore.RED}Invalid mode: {args.mode}{Style.RESET_ALL}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    try:
        result = main()
        if result is not None:
            sys.exit(result)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)