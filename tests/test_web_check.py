#!/usr/bin/env python3
"""
Test script for migrated web_check module

This script tests the migrated web_check module to ensure it works correctly.
"""

import os
import sys
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Import migrated tools
try:
    from network_tools import web_check_main, check_website, check_websites_reachability
    print(f"{Fore.GREEN}Successfully imported migrated web_check tools{Style.RESET_ALL}")
except ImportError as e:
    print(f"{Fore.RED}Failed to import migrated web_check tools: {e}{Style.RESET_ALL}")
    sys.exit(1)

# Import network diagnostics module
try:
    from network_diagnostics import check_websites
    print(f"{Fore.GREEN}Successfully imported network_diagnostics.check_websites{Style.RESET_ALL}")
except ImportError as e:
    print(f"{Fore.RED}Failed to import network_diagnostics.check_websites: {e}{Style.RESET_ALL}")
    sys.exit(1)


def test_check_website():
    """Test the check_website function"""
    print(f"\n{Fore.CYAN}Testing check_website function...{Style.RESET_ALL}")
    try:
        # Test with a reliable website
        status, result = check_website("https://www.google.com")
        print(f"Status: {status}, Result: {result}")
        if status == "reachable" and isinstance(result, float):
            print(f"{Fore.GREEN}Success: Website check returned expected result type{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}Error: Unexpected result format{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return False


def test_check_websites_reachability():
    """Test the check_websites_reachability function"""
    print(f"\n{Fore.CYAN}Testing check_websites_reachability function...{Style.RESET_ALL}")
    try:
        # Test with a subset of websites for quicker testing
        test_websites = [
            "https://www.google.com",
            "https://www.github.com",
            "https://www.example.com"
        ]
        
        reachable, unreachable = check_websites_reachability(
            websites=test_websites,
            max_retries=0,
            silent=True
        )
        
        print(f"Reachable websites: {len(reachable)}")
        print(f"Unreachable websites: {len(unreachable)}")
        
        if isinstance(reachable, list) and isinstance(unreachable, list):
            print(f"{Fore.GREEN}Success: check_websites_reachability returned expected result types{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}Error: Unexpected result format{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return False


def test_web_check_main():
    """Test the web_check_main function"""
    print(f"\n{Fore.CYAN}Testing web_check_main function...{Style.RESET_ALL}")
    try:
        result = web_check_main(silent=True, polite=False)
        print(f"{Fore.GREEN}Success: web_check_main executed successfully{Style.RESET_ALL}")
        print(f"Result excerpt: {result[:100]}...")
        return True
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return False


def test_network_diagnostics_check_websites():
    """Test the check_websites function in network_diagnostics"""
    print(f"\n{Fore.CYAN}Testing network_diagnostics.check_websites function...{Style.RESET_ALL}")
    try:
        result = check_websites()
        print(f"{Fore.GREEN}Success: check_websites executed successfully{Style.RESET_ALL}")
        print(f"Result excerpt: {result[:100]}...")
        return True
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return False


def main():
    """Run all tests"""
    print(f"{Fore.CYAN}Running tests for migrated web_check module...{Style.RESET_ALL}")
    
    # Track overall success
    success = True
    
    # Run each test and track results
    tests = [
        test_check_website,
        test_check_websites_reachability,
        test_web_check_main,
        test_network_diagnostics_check_websites
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