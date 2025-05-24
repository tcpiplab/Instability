#!/usr/bin/env python3
"""
Test script for migrated network tools

This script tests the migrated network tools to ensure they work correctly.
"""

import os
import sys
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Import migrated tools
try:
    from network_tools import get_public_ip, check_external_ip_main
    print(f"{Fore.GREEN}Successfully imported migrated network tools{Style.RESET_ALL}")
except ImportError as e:
    print(f"{Fore.RED}Failed to import migrated network tools: {e}{Style.RESET_ALL}")
    sys.exit(1)

# Import network diagnostics module
try:
    from network_diagnostics import get_external_ip, execute_tool
    print(f"{Fore.GREEN}Successfully imported network diagnostics{Style.RESET_ALL}")
except ImportError as e:
    print(f"{Fore.RED}Failed to import network diagnostics: {e}{Style.RESET_ALL}")
    sys.exit(1)


def test_get_public_ip():
    """Test the get_public_ip function"""
    print(f"\n{Fore.CYAN}Testing get_public_ip function...{Style.RESET_ALL}")
    try:
        ip = get_public_ip()
        print(f"{Fore.GREEN}Success: External IP is {ip}{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return False


def test_check_external_ip_main():
    """Test the check_external_ip_main function"""
    print(f"\n{Fore.CYAN}Testing check_external_ip_main function...{Style.RESET_ALL}")
    try:
        result = check_external_ip_main(silent=False, polite=True)
        print(f"{Fore.GREEN}Success: Function returned successfully{Style.RESET_ALL}")
        print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return False


def test_network_diagnostics_get_external_ip():
    """Test the get_external_ip function in network_diagnostics"""
    print(f"\n{Fore.CYAN}Testing network_diagnostics.get_external_ip function...{Style.RESET_ALL}")
    try:
        ip = get_external_ip()
        print(f"{Fore.GREEN}Success: External IP is {ip}{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return False


def test_execute_tool():
    """Test the execute_tool function with get_external_ip"""
    print(f"\n{Fore.CYAN}Testing execute_tool with get_external_ip...{Style.RESET_ALL}")
    try:
        result = execute_tool("get_external_ip")
        print(f"{Fore.GREEN}Success: Tool executed successfully{Style.RESET_ALL}")
        print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return False


def main():
    """Run all tests"""
    print(f"{Fore.CYAN}Running tests for migrated network tools...{Style.RESET_ALL}")
    
    # Track overall success
    success = True
    
    # Run each test and track results
    tests = [
        test_get_public_ip,
        test_check_external_ip_main,
        test_network_diagnostics_get_external_ip,
        test_execute_tool
    ]
    
    for test in tests:
        if not test():
            success = False
    
    # Print overall result
    if success:
        print(f"\n{Fore.GREEN}All tests passed successfully!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}Some tests failed.{Style.RESET_ALL}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())