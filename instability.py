#!/usr/bin/env python3
"""
Instability.py v3 - Network diagnostic and pentesting chatbot

A terminal-based network diagnostic tool that provides an interactive interface
for diagnosing and troubleshooting network connectivity issues, pentesting,
and comprehensive network assessment.

Usage:
    python instability.py chatbot [--model MODEL] - Run the interactive chatbot
    python instability.py manual [tool]           - Run specific tools manually
    python instability.py test                    - Test the environment setup
    python instability.py help                    - Show help information
    
Options:
    --model, -m MODEL    Specify Ollama model name (default: dolphin3)
"""

import sys
import os
import json
import argparse
from typing import Dict, Any
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def start_chatbot_mode(model_name=None):
    """Start the interactive chatbot with v3 startup sequence"""
    try:
        # Run v3 startup sequence
        from core.startup_checks import run_startup_sequence
        startup_results = run_startup_sequence(silent=False)
        
        if not startup_results["success"]:
            print(f"{Fore.YELLOW}[WARN] Startup checks completed with warnings. Proceeding in degraded mode.{Style.RESET_ALL}")
        
        # Start chatbot with v3 startup context integration
        from chatbot import start_interactive_session
        start_interactive_session(model_name=model_name, startup_context=startup_results)
    except ImportError as e:
        print(f"{Fore.RED}Error: Required module not found: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Ensure all v3 modules are properly installed.{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error starting chatbot: {e}{Style.RESET_ALL}")


def run_manual_mode(tool_name=None):
    """Run specific tools manually with v3 architecture"""
    try:
        # Import the tools registry
        from core.tools_registry import get_tool_registry
        registry = get_tool_registry()
        
        # Quick startup check for tools
        from core.startup_checks import check_tool_inventory
        tool_inventory = check_tool_inventory(silent=True)

        if tool_name is None:
            # List available tools using the registry
            print(f"{Fore.CYAN}Instability v3 - Available Tools:{Style.RESET_ALL}")
            print(registry.list_tools(mode="manual"))
            
            print(f"\nUsage:")
            print(f"  {Fore.CYAN}python instability.py manual all{Style.RESET_ALL} - Run comprehensive diagnostics")
            print(f"  {Fore.CYAN}python instability.py manual <tool_name>{Style.RESET_ALL} - Run specific tool")
            
        elif tool_name.lower() == 'all':
            # Run comprehensive diagnostics
            _run_comprehensive_diagnostics()
            
        else:
            # Check if tool exists in registry
            tool_metadata = registry.get_tool(tool_name)
            if tool_metadata:
                # Execute tool using registry
                print(f"{Fore.GREEN}Running {tool_name}...{Style.RESET_ALL}")
                result = registry.execute_tool(tool_name, {}, mode="manual")
                
                # Display the result
                if result:
                    if isinstance(result, dict):
                        if result.get('success'):
                            print(f"{Fore.GREEN}Success!{Style.RESET_ALL}")
                            if 'stdout' in result:
                                print(result['stdout'])
                            elif 'parsed_data' in result:
                                print(json.dumps(result['parsed_data'], indent=2))
                        else:
                            print(f"{Fore.RED}Error: {result.get('error_message', 'Unknown error')}{Style.RESET_ALL}")
                    else:
                        print(result)
            else:
                print(f"{Fore.RED}Tool '{tool_name}' not found.{Style.RESET_ALL}")
                available_tools = registry.get_available_tools(mode="manual")
                print(f"Available tools: {', '.join(available_tools.keys())}")
            
    except ImportError as e:
        print(f"{Fore.RED}Error: Required v3 module not found: {e}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error in manual mode: {e}{Style.RESET_ALL}")


def run_test_mode():
    """Test the v3 environment setup using startup sequence"""
    print(f"{Fore.CYAN}Instability v3 - Environment Test{Style.RESET_ALL}")
    print(f"{'=' * 50}")
    
    try:
        # Run comprehensive v3 startup sequence
        from core.startup_checks import run_startup_sequence
        startup_results = run_startup_sequence(silent=False)
        
        print(f"\n{Fore.CYAN}Test Summary:{Style.RESET_ALL}")
        print(f"{'=' * 50}")
        
        # Overall status
        if startup_results["success"]:
            print(f"{Fore.GREEN}[OK] All systems operational - Ready for full functionality{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}[WARN] Some issues detected - Limited functionality available{Style.RESET_ALL}")
        
        # Phase summaries
        for phase_name, phase_data in startup_results.get("phases", {}).items():
            status_text = f"[{Fore.YELLOW}WARN{Style.RESET_ALL}]" if phase_data.get("success", False) else f"[{Fore.YELLOW}WARN{Style.RESET_ALL}]"
            status_color = Fore.GREEN if phase_data.get("success", False) else Fore.YELLOW
            print(f"{status_color}{status_text} {phase_name.replace('_', ' ').title()}: {phase_data.get('status', 'Unknown')}{Style.RESET_ALL}")
        
        # Tool inventory summary
        tool_inventory = startup_results.get("phases", {}).get("tool_inventory", {})
        if tool_inventory:
            found_tools = len([t for t in tool_inventory.get("tools", {}).values() if t.get("found")])
            total_tools = len(tool_inventory.get("tools", {}))
            print(f"{Fore.CYAN}Tools Available: {found_tools}/{total_tools}{Style.RESET_ALL}")
        
        return 0 if startup_results["success"] else 1
        
    except ImportError as e:
        print(f"{Fore.RED}Error: v3 startup module not found: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Falling back to basic environment check...{Style.RESET_ALL}")
        return _run_basic_test_mode()
    except Exception as e:
        print(f"{Fore.RED}Error running v3 test mode: {e}{Style.RESET_ALL}")
        return 1


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
    print(f"{Fore.CYAN}Instability.py v3 - Network Diagnostic & Pentesting Toolkit{Style.RESET_ALL}")
    print("\nA comprehensive terminal-based network diagnostic and pentesting tool")
    print("with AI-powered assistance, persistent memory, and extensive tool integration.")
    
    print(f"\n{Fore.YELLOW}v3 Features:{Style.RESET_ALL}")
    print("  • 4-Phase startup sequence with comprehensive environment assessment")
    print("  • Proactive system verification and pentesting tool inventory")
    print("  • Enhanced network diagnostics (Layer 2/3, DNS, Web connectivity)")
    print("  • Native pentesting tool integration (nmap, nuclei, httpx, etc.)")
    print("  • Persistent memory system with markdown-based storage")
    print("  • Intelligent fallback modes when services unavailable")
    
    print(f"\n{Fore.YELLOW}Usage:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}python instability.py chatbot{Style.RESET_ALL}")
    print("      Start the interactive AI-powered chatbot with v3 startup sequence")
    print(f"  {Fore.GREEN}python instability.py manual [tool_name]{Style.RESET_ALL}")
    print("      Run diagnostic tools manually (use 'manual' to list all tools)")
    print(f"  {Fore.GREEN}python instability.py manual all{Style.RESET_ALL}")
    print("      Run comprehensive diagnostic suite")
    print(f"  {Fore.GREEN}python instability.py test{Style.RESET_ALL}")
    print("      Run v3 environment test with 4-phase startup sequence")
    print(f"  {Fore.GREEN}python instability.py run-tests{Style.RESET_ALL}")
    print("      Execute test suite")
    print(f"  {Fore.GREEN}python instability.py help{Style.RESET_ALL}")
    print("      Show this help information")
    
    print(f"\n{Fore.YELLOW}Options:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}--model, -m MODEL{Style.RESET_ALL}")
    print("      Specify Ollama model (default: dolphin3)")
    
    print(f"\n{Fore.YELLOW}Available Manual Tools:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}Network Diagnostics:{Style.RESET_ALL} ping, dns_check, web_check, network_scan")
    print(f"  {Fore.GREEN}Pentesting:{Style.RESET_ALL} nmap_scan, port_scan, host_discovery")
    print(f"  {Fore.GREEN}System Info:{Style.RESET_ALL} system_info, interface_status, tool_inventory")
    
    print(f"\n{Fore.YELLOW}Chatbot Commands:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}/help{Style.RESET_ALL}    - Show available commands and tools")
    print(f"  {Fore.GREEN}/tools{Style.RESET_ALL}   - Display tool inventory")
    print(f"  {Fore.GREEN}/memory{Style.RESET_ALL}  - Show persistent memory status")
    print(f"  {Fore.GREEN}/scan{Style.RESET_ALL}    - Quick network scan")
    print(f"  {Fore.GREEN}/exit{Style.RESET_ALL}    - Exit the chatbot")
    
    print(f"\n{Fore.YELLOW}v3 Startup Phases:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}Phase 1:{Style.RESET_ALL} Core System Verification (OS, Ollama, interfaces, local IP)")
    print(f"  {Fore.GREEN}Phase 2:{Style.RESET_ALL} Internet Connectivity Assessment (external IP, DNS, web)")
    print(f"  {Fore.GREEN}Phase 3:{Style.RESET_ALL} Pentesting Tool Inventory (nmap, nuclei, httpx, etc.)")
    print(f"  {Fore.GREEN}Phase 4:{Style.RESET_ALL} Target Scope Configuration (memory and scope management)")
    
    print(f"\n{Fore.YELLOW}Design Philosophy:{Style.RESET_ALL}")
    print("  • Functions even during complete network outages")
    print("  • Provides diagnostic information without internet access")
    print("  • Modular architecture for easy extension")
    print("  • Cross-platform compatibility")


def _get_v3_tools_registry() -> Dict[str, Any]:
    """Get registry of available v3 tools"""
    return {
        # Network Diagnostics
        "ping": {"module": "network.layer3_diagnostics", "function": "ping_host", "description": "Test ICMP connectivity"},
        "dns_check": {"module": "network.dns_diagnostics", "function": "resolve_hostname", "description": "DNS resolution testing"},
        "web_check": {"module": "network.web_connectivity", "function": "test_http_connectivity", "description": "HTTP/HTTPS connectivity test"},
        "network_scan": {"module": "network.layer2_diagnostics", "function": "get_all_interfaces", "description": "Network interface analysis"},
        
        # Pentesting Tools
        "nmap_scan": {"module": "pentest.nmap_wrapper", "function": "run_nmap_scan", "description": "Network scanning with nmap"},
        "port_scan": {"module": "pentest.nmap_wrapper", "function": "quick_port_scan", "description": "Quick port scan"},
        "host_discovery": {"module": "pentest.nmap_wrapper", "function": "network_discovery", "description": "Network host discovery"},
        
        # System Information
        "system_info": {"module": "network.layer2_diagnostics", "function": "get_system_info", "description": "System information"},
        "interface_status": {"module": "network.layer2_diagnostics", "function": "get_all_interfaces", "description": "Network interface status"},
        "tool_inventory": {"module": "pentest.tool_detector", "function": "scan_for_tools", "description": "Scan for available tools"}
    }

def _is_tool_available(tool_name: str, tool_inventory: Dict[str, Any]) -> bool:
    """Check if a tool is available based on inventory"""
    if not tool_inventory or "tools" not in tool_inventory:
        return True  # Assume available if no inventory
    
    # Map tool names to actual tools in inventory
    tool_mapping = {
        "nmap_scan": "nmap",
        "port_scan": "nmap", 
        "host_discovery": "nmap"
    }
    
    actual_tool = tool_mapping.get(tool_name, tool_name)
    return tool_inventory["tools"].get(actual_tool, {}).get("found", True)

def _execute_v3_tool(tool_name: str, tool_config: Dict[str, Any]):
    """Execute a v3 tool"""
    try:
        module_name = tool_config["module"]
        function_name = tool_config["function"]
        
        # Dynamic import
        module = __import__(module_name, fromlist=[function_name])
        func = getattr(module, function_name)
        
        print(f"{Fore.GREEN}Running {tool_name}...{Style.RESET_ALL}")
        
        # Execute with basic parameters
        if tool_name in ["ping", "dns_check", "web_check"]:
            # Tools that need a target
            target = input(f"Enter target (hostname/IP): ").strip() or "google.com"
            result = func(target, silent=False)
        elif tool_name == "tool_inventory":
            result = func(force_refresh=True)
        elif tool_name in ["interface_status", "network_scan"]:
            # Tools that don't accept silent parameter
            result = func()
        else:
            result = func(silent=False)
        
        # Handle different result types
        if isinstance(result, dict):
            print(f"{Fore.CYAN}Result: {result.get('success', 'Unknown')}{Style.RESET_ALL}")
        elif isinstance(result, list):
            print(f"{Fore.CYAN}Found {len(result)} items{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}Result: {result}{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}Error executing {tool_name}: {e}{Style.RESET_ALL}")

def _run_comprehensive_diagnostics():
    """Run comprehensive diagnostic suite"""
    print(f"{Fore.CYAN}Running Comprehensive Diagnostics Suite{Style.RESET_ALL}")
    print(f"{'=' * 50}")
    
    try:
        # Import required modules
        from network.layer2_diagnostics import get_system_info, get_all_interfaces
        from network.layer3_diagnostics import get_external_ip, ping_host
        from network.web_connectivity import test_common_web_services
        from pentest.tool_detector import scan_for_tools
        
        # System Information
        print(f"\n{Fore.YELLOW}1. System Information{Style.RESET_ALL}")
        system_info = get_system_info(silent=False)
        
        # Network Interfaces
        print(f"\n{Fore.YELLOW}2. Network Interfaces{Style.RESET_ALL}")
        interfaces = get_all_interfaces()
        
        # External Connectivity
        print(f"\n{Fore.YELLOW}3. External Connectivity{Style.RESET_ALL}")
        external_ip = get_external_ip(silent=False)
        ping_result = ping_host("8.8.8.8", count=3, silent=False)
        
        # Web Services
        print(f"\n{Fore.YELLOW}4. Web Service Connectivity{Style.RESET_ALL}")
        web_services = test_common_web_services(silent=False)
        
        # Tool Inventory
        print(f"\n{Fore.YELLOW}5. Tool Inventory{Style.RESET_ALL}")
        tool_inventory = scan_for_tools(force_refresh=False)
        
        print(f"\n{Fore.GREEN}Comprehensive diagnostics completed.{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}Error in comprehensive diagnostics: {e}{Style.RESET_ALL}")

def _run_basic_test_mode():
    """Fallback basic test mode"""
    print(f"{Fore.YELLOW}Running basic environment test...{Style.RESET_ALL}")
    
    import platform
    py_version = platform.python_version()
    print(f"Python version: {py_version}")
    print(f"{Fore.GREEN}Colorama is working{Style.RESET_ALL}")
    
    # Test Ollama
    try:
        import ollama
        models = ollama.list()
        print(f"{Fore.GREEN}Ollama is available{Style.RESET_ALL}")
        print(f"Available models: {', '.join([m['name'] for m in models['models']])}")
    except Exception as e:
        print(f"{Fore.RED}Ollama not available: {e}{Style.RESET_ALL}")
    
    return 0

def main():
    """Main entry point for instability.py"""
    parser = argparse.ArgumentParser(description="Network diagnostic chatbot")
    parser.add_argument('mode', nargs='?', choices=['chatbot', 'manual', 'test', 'run-tests', 'mcp', 'help'],
                        default='help', help='Mode of operation')
    parser.add_argument('tool_name', nargs='?', help='Specific tool to run in manual mode')
    parser.add_argument('--model', '-m', type=str, default='dolphin3',
                        help='Ollama model name to use for chatbot (default: dolphin3)')
    args = parser.parse_args()

    # Handle different modes
    if args.mode == 'chatbot':
        start_chatbot_mode(model_name=args.model)
        return None
    elif args.mode == 'manual':
        run_manual_mode(args.tool_name)
        return None
    elif args.mode == 'test':
        run_test_mode()
        return None
    elif args.mode == 'run-tests':
        return run_tests_mode()
    elif args.mode == 'mcp':
        # Run as MCP server
        import subprocess
        subprocess.run([sys.executable, "mcp_server.py"])
        return None
    elif args.mode == 'help':
        show_help()
        return None
    else:
        # This should not happen due to choices in argparse
        print(f"{Fore.RED}Invalid mode: {args.mode}{Style.RESET_ALL}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    try:
        result_of_calling_main = main()
        if result_of_calling_main is not None:
            sys.exit(result_of_calling_main)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as unexpected_error:
        print(f"{Fore.RED}Unexpected error: {unexpected_error}{Style.RESET_ALL}")
        sys.exit(1)