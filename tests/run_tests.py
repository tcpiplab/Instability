#!/usr/bin/env python3
"""
Test runner for Instability v2

This script runs all the test scripts in the tests directory.
"""

import os
import sys
import importlib
import inspect
import unittest
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Add parent directory to path to allow importing from other modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


def discover_and_run_tests():
    """
    Discover and run all test scripts in the tests directory
    """
    print(f"{Fore.CYAN}Running all tests for Instability v2...{Style.RESET_ALL}\n")
    
    # Get directory of this script
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get all Python files in the tests directory
    test_files = [f[:-3] for f in os.listdir(test_dir) 
                  if f.startswith('test_') and f.endswith('.py')]
    
    if not test_files:
        print(f"{Fore.YELLOW}No test files found in {test_dir}{Style.RESET_ALL}")
        return 0
    
    print(f"{Fore.CYAN}Found {len(test_files)} test files:{Style.RESET_ALL}")
    for test_file in test_files:
        print(f"  - {test_file}")
    print()
    
    # Keep track of success
    success = True
    
    # Run each test file
    for test_file in test_files:
        try:
            print(f"{Fore.CYAN}Running {test_file}...{Style.RESET_ALL}")
            
            # Import the test module dynamically
            module_name = f"tests.{test_file}"
            module = importlib.import_module(module_name)
            
            # Check if the module has a main function
            if hasattr(module, 'main'):
                result = module.main()
                if result != 0:
                    success = False
            else:
                print(f"{Fore.YELLOW}Warning: {test_file} does not have a main function{Style.RESET_ALL}")
            
            print()
        except Exception as e:
            print(f"{Fore.RED}Error running {test_file}: {e}{Style.RESET_ALL}")
            success = False
    
    # Print overall result
    if success:
        print(f"{Fore.GREEN}All tests completed successfully!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Some tests failed.{Style.RESET_ALL}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(discover_and_run_tests())