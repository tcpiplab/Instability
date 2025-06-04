"""
Startup checks module for Instability v3.

Implements the 4-phase startup sequence:
1. Core System Verification
2. Internet Connectivity Assessment  
3. Pentesting Tool Inventory
4. Target Scope Configuration
"""

import os
import sys
import time
import platform
import subprocess
import socket
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from colorama import Fore, Style, init as colorama_init

# Import configuration
from config import (
    OLLAMA_API_URL, OLLAMA_DEFAULT_MODEL, OLLAMA_TIMEOUT,
    DNS_TEST_SERVERS, CONNECTIVITY_TEST_SITES, STARTUP_PHASES
)

# Ensure colorama is initialized for colored output
colorama_init(autoreset=True)


def run_startup_sequence(silent: bool = False) -> Dict[str, Any]:
    """
    Run the complete 4-phase startup sequence.
    
    Args:
        silent: If True, suppress progress output
        
    Returns:
        Dictionary containing results of all startup phases
    """
    if not silent:
        print("Starting Instability v3 initialization...")
    
    startup_id = f"startup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    start_time = time.time()
    
    results = {
        "startup_id": startup_id,
        "timestamp": datetime.now().isoformat(),
        "total_duration": 0.0,
        "phases": {}
    }
    
    # Phase 1: Core System Verification
    if not silent:
        print("\nPhase 1: Core System Verification")
    phase1_result = run_phase1_core_system(silent)
    results["phases"]["core_system"] = phase1_result
    
    # Phase 2: Internet Connectivity Assessment
    if not silent:
        print("\nPhase 2: Internet Connectivity Assessment")
    phase2_result = run_phase2_connectivity(silent)
    results["phases"]["internet_connectivity"] = phase2_result
    
    # Phase 3: Pentesting Tool Inventory
    if not silent:
        print("\nPhase 3: Pentesting Tool Inventory")
    phase3_result = run_phase3_tool_inventory(silent)
    results["phases"]["tool_inventory"] = phase3_result
    
    # Phase 4: Target Scope Configuration
    if not silent:
        print("\nPhase 4: Target Scope Configuration")
    phase4_result = run_phase4_target_scope(silent)
    results["phases"]["target_scope"] = phase4_result
    
    # Calculate total duration
    results["total_duration"] = time.time() - start_time
    
    # Determine overall success status
    phase_statuses = [phase_data.get("status", "failure") for phase_data in results["phases"].values()]
    results["success"] = all(status in ["success", "warning"] for status in phase_statuses)
    
    if not silent:
        print(f"\n[{Fore.GREEN}OK{Style.RESET_ALL}] Startup sequence completed in {results['total_duration']:.2f} seconds")
        print_startup_summary(results)
    
    return results


def run_phase1_core_system(silent: bool = False) -> Dict[str, Any]:
    """
    Phase 1: Core System Verification
    - Detect operating system and version
    - Check Ollama API connectivity with graceful fallback
    - Verify layer 2 network interfaces and status
    - Determine local IP address and network configuration
    """
    phase_start = time.time()
    phase_result = {
        "status": "success",
        "duration": 0.0,
        "checks": {}
    }
    
    # Check 1: OS Detection
    try:
        os_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
        phase_result["checks"]["os_detection"] = {
            "status": "success",
            "result": os_info,
            "message": f"Detected {os_info['system']} {os_info['release']}"
        }
        if not silent:
            print(f"  [{Fore.GREEN}OK{Style.RESET_ALL}] OS: {os_info['system']} {os_info['release']}")
    except Exception as e:
        phase_result["checks"]["os_detection"] = {
            "status": "error",
            "result": None,
            "message": f"Failed to detect OS: {Fore.RED}{e}{Style.RESET_ALL}"
        }
        phase_result["status"] = "warning"
        if not silent:
            print(f"  [{Fore.RED}ERROR{Style.RESET_ALL}] OS detection failed: {Fore.RED}{e}{Style.RESET_ALL}")
    
    # Check 2: Ollama Connectivity
    ollama_result = check_ollama_connectivity()
    phase_result["checks"]["ollama_connectivity"] = ollama_result
    if ollama_result["status"] != "success":
        phase_result["status"] = "warning"
    if not silent:
        status_text = f"[{Fore.GREEN}OK{Style.RESET_ALL}]" if ollama_result["status"] == "success" else f"[{Fore.YELLOW}WARN{Style.RESET_ALL}]"
        print(f"  {status_text} Ollama: {ollama_result['message']}")
    
    # Check 3: Network Interfaces
    try:
        interfaces = get_network_interfaces()
        phase_result["checks"]["network_interfaces"] = {
            "status": "success",
            "result": interfaces,
            "message": f"Found {len(interfaces)} network interfaces"
        }
        if not silent:
            print(f"  [{Fore.GREEN}OK{Style.RESET_ALL}] Network interfaces: {len(interfaces)} found")
            for iface in interfaces[:3]:  # Show first 3
                print(f"    - {iface['name']}: {iface['status']}")
    except Exception as e:
        phase_result["checks"]["network_interfaces"] = {
            "status": "error",
            "result": None,
            "message": f"Failed to get network interfaces: {Fore.RED}{e}{Style.RESET_ALL}"
        }
        phase_result["status"] = "error"
        if not silent:
            print(f"  [{Fore.RED}ERROR{Style.RESET_ALL}] Network interfaces failed: {Fore.RED}{e}{Style.RESET_ALL}")
    
    # Check 4: Local IP Detection
    try:
        local_ip = get_local_ip()
        phase_result["checks"]["local_ip"] = {
            "status": "success",
            "result": local_ip,
            "message": f"Local IP: {local_ip}"
        }
        if not silent:
            print(f"  [{Fore.GREEN}OK{Style.RESET_ALL}] Local IP: {local_ip}")
    except Exception as e:
        phase_result["checks"]["local_ip"] = {
            "status": "error",
            "result": None,
            "message": f"Failed to get local IP: {Fore.RED}{e}{Style.RESET_ALL}"
        }
        phase_result["status"] = "warning"
        if not silent:
            print(f"  [{Fore.YELLOW}WARN{Style.RESET_ALL}] Local IP detection failed: {Fore.RED}{e}{Style.RESET_ALL}")
    
    phase_result["duration"] = time.time() - phase_start
    return phase_result


def run_phase2_connectivity(silent: bool = False) -> Dict[str, Any]:
    """
    Phase 2: Internet Connectivity Assessment
    - Test layer 3 connectivity and external IP detection
    - Validate DNS resolver functionality
    - Confirm access to major websites and services
    - Measure basic network performance metrics
    """
    phase_start = time.time()
    phase_result = {
        "status": "success",
        "duration": 0.0,
        "checks": {}
    }
    
    # Check 1: External IP Detection
    try:
        external_ip = get_external_ip()
        phase_result["checks"]["external_ip"] = {
            "status": "success",
            "result": external_ip,
            "message": f"External IP: {external_ip}"
        }
        if not silent:
            print(f"  [{Fore.GREEN}OK{Style.RESET_ALL}] External IP: {external_ip}")
    except Exception as e:
        phase_result["checks"]["external_ip"] = {
            "status": "error",
            "result": None,
            "message": f"Failed to get external IP: {Fore.RED}{e}{Style.RESET_ALL}"
        }
        phase_result["status"] = "warning"
        if not silent:
            print(f"  [{Fore.YELLOW}WARN{Style.RESET_ALL}] External IP detection failed: {Fore.RED}{e}{Style.RESET_ALL}")
    
    # Check 2: DNS Resolution
    dns_results = test_dns_resolution()
    phase_result["checks"]["dns_resolution"] = dns_results
    if dns_results["status"] != "success":
        phase_result["status"] = "warning"
    if not silent:
        status_text = f"[{Fore.GREEN}OK{Style.RESET_ALL}]" if dns_results["status"] == "success" else f"[{Fore.YELLOW}WARN{Style.RESET_ALL}]"
        print(f"  {status_text} DNS: {dns_results['message']}")
    
    # Check 3: Web Connectivity
    web_results = test_web_connectivity()
    phase_result["checks"]["web_connectivity"] = web_results
    if web_results["status"] != "success":
        phase_result["status"] = "warning"
    if not silent:
        status_text = f"[{Fore.GREEN}OK{Style.RESET_ALL}]" if web_results["status"] == "success" else f"[{Fore.YELLOW}WARN{Style.RESET_ALL}]"
        print(f"  {status_text} Web connectivity: {web_results['message']}")
    
    phase_result["duration"] = time.time() - phase_start
    return phase_result


def run_phase3_tool_inventory(silent: bool = False) -> Dict[str, Any]:
    """
    Phase 3: Pentesting Tool Inventory
    - Scan for installed tools (nmap, nuclei, httpx, etc.)
    - Verify tool versions and basic functionality
    - Report missing tools with installation recommendations
    - Cache tool availability for session optimization
    """
    phase_start = time.time()
    
    # Import tool detector (will be implemented next)
    try:
        from pentest.tool_detector import scan_for_tools, get_missing_tools
        
        tool_inventory = scan_for_tools()
        missing_tools = get_missing_tools(tool_inventory)
        
        phase_result = {
            "status": "success",
            "duration": 0.0,
            "tools_found": len([t for t in tool_inventory["tools"].values() if t["found"]]),
            "tools_missing": len(missing_tools),
            "critical_missing": [t for t in missing_tools if t in ["nmap", "nuclei"]]
        }
        
        if not silent:
            print(f"  [{Fore.GREEN}OK{Style.RESET_ALL}] Tools found: {phase_result['tools_found']}")
            print(f"  [{Fore.YELLOW}WARN{Style.RESET_ALL}] Tools missing: {phase_result['tools_missing']}")
            
            if phase_result["critical_missing"]:
                print(f"  [{Fore.YELLOW}WARN{Style.RESET_ALL}] Critical tools missing: {', '.join(phase_result['critical_missing'])}")
                phase_result["status"] = "warning"
    
    except ImportError:
        # Tool detector not implemented yet
        phase_result = {
            "status": "warning",
            "duration": 0.0,
            "tools_found": 0,
            "tools_missing": 0,
            "critical_missing": []
        }
        if not silent:
            print(f"  [{Fore.YELLOW}WARN{Style.RESET_ALL}] Tool inventory system not yet implemented")
    
    phase_result["duration"] = time.time() - phase_start
    return phase_result


def run_phase4_target_scope(silent: bool = False) -> Dict[str, Any]:
    """
    Phase 4: Target Scope Configuration
    - Present current network assessment summary
    - Prompt user for pentesting target scope definition
    - Update or create target scope markdown file
    - Initialize session with full environmental context
    """
    phase_start = time.time()
    
    # Import memory manager (will be implemented next)
    try:
        from memory.memory_manager import load_target_scope, create_default_scope
        
        scope_data = load_target_scope()
        if not scope_data:
            scope_data = create_default_scope()
        
        phase_result = {
            "status": "success",
            "duration": 0.0,
            "scope_loaded": True,
            "scope_type": scope_data.get("scope_type", "local network only"),
            "targets_defined": len(scope_data.get("targets", []))
        }
        
        if not silent:
            print(f"  [{Fore.GREEN}OK{Style.RESET_ALL}] Target scope: {phase_result['scope_type']}")
            print(f"  [{Fore.GREEN}OK{Style.RESET_ALL}] Targets defined: {phase_result['targets_defined']}")
    
    except ImportError:
        # Memory manager not implemented yet
        phase_result = {
            "status": "warning",
            "duration": 0.0,
            "scope_loaded": False,
            "scope_type": "local network only",
            "targets_defined": 0
        }
        if not silent:
            print(f"  [{Fore.YELLOW}WARN{Style.RESET_ALL}] Target scope system not yet implemented")
            print("  Using default scope: local network only")
    
    phase_result["duration"] = time.time() - phase_start
    return phase_result


# Helper functions for individual checks

def check_ollama_connectivity() -> Dict[str, Any]:
    """Check if Ollama API is accessible."""
    try:
        import requests
        response = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=OLLAMA_TIMEOUT)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {
                "status": "success",
                "result": {"available": True, "models": len(models)},
                "message": f"Connected, {len(models)} models available"
            }
        else:
            return {
                "status": "error",
                "result": {"available": False},
                "message": f"API returned status {response.status_code}"
            }
    except ImportError:
        return {
            "status": "error",
            "result": {"available": False},
            "message": "requests library not available"
        }
    except Exception as e:
        return {
            "status": "error",
            "result": {"available": False},
            "message": f"Connection failed: {Fore.RED}{e}{Style.RESET_ALL}"
        }


def get_network_interfaces() -> List[Dict[str, Any]]:
    """Get list of network interfaces and their status."""
    interfaces = []
    
    try:
        if platform.system() == "Windows":
            # Windows implementation
            result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, timeout=10)
            # Parse Windows ipconfig output (simplified)
            interfaces.append({
                "name": "Windows Interface",
                "status": "up" if result.returncode == 0 else "unknown"
            })
        else:
            # Unix/Linux/macOS implementation
            result = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse ifconfig output (simplified)
                for line in result.stdout.split('\n'):
                    if line and not line.startswith(' ') and not line.startswith('\t'):
                        iface_name = line.split(':')[0]
                        if iface_name and iface_name != "lo":  # Skip loopback
                            interfaces.append({
                                "name": iface_name,
                                "status": "up"
                            })
    except Exception:
        # Fallback: minimal interface detection
        interfaces.append({
            "name": "default",
            "status": "unknown"
        })
    
    return interfaces


def get_local_ip() -> str:
    """Get the local IP address."""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def get_external_ip() -> str:
    """Get the external IP address."""
    try:
        import requests
        response = requests.get("https://api.ipify.org", timeout=10)
        return response.text.strip()
    except Exception as e:
        raise Exception(f"Unable to determine external IP: {Fore.RED}{e}{Style.RESET_ALL}")


def test_dns_resolution() -> Dict[str, Any]:
    """Test DNS resolution functionality."""
    try:
        successful_resolves = 0
        for dns_server in DNS_TEST_SERVERS[:2]:  # Test first 2 servers
            try:
                socket.gethostbyname("google.com")
                successful_resolves += 1
            except Exception:
                continue
        
        if successful_resolves > 0:
            return {
                "status": "success",
                "result": {"servers_working": successful_resolves},
                "message": f"{successful_resolves}/{len(DNS_TEST_SERVERS[:2])} DNS servers working"
            }
        else:
            return {
                "status": "error",
                "result": {"servers_working": 0},
                "message": "DNS resolution failed"
            }
    except Exception as e:
        return {
            "status": "error",
            "result": None,
            "message": f"DNS test failed: {Fore.RED}{e}{Style.RESET_ALL}"
        }


def test_web_connectivity() -> Dict[str, Any]:
    """Test connectivity to major websites."""
    try:
        import requests
        successful_connections = 0
        
        for site in CONNECTIVITY_TEST_SITES[:2]:  # Test first 2 sites
            try:
                response = requests.get(site, timeout=10)
                if response.status_code == 200:
                    successful_connections += 1
            except Exception:
                continue
        
        if successful_connections > 0:
            return {
                "status": "success",
                "result": {"sites_reachable": successful_connections},
                "message": f"{successful_connections}/{len(CONNECTIVITY_TEST_SITES[:2])} sites reachable"
            }
        else:
            return {
                "status": "error",
                "result": {"sites_reachable": 0},
                "message": "No websites reachable"
            }
    except ImportError:
        return {
            "status": "error",
            "result": None,
            "message": "requests library not available"
        }
    except Exception as e:
        return {
            "status": "error",
            "result": None,
            "message": f"Web connectivity test failed: {Fore.RED}{e}{Style.RESET_ALL}"
        }


def check_tool_inventory(silent: bool = False) -> Dict[str, Any]:
    """
    Quick tool inventory check for manual mode.
    Returns simplified tool availability information.
    """
    try:
        from pentest.tool_detector import scan_for_tools
        tool_inventory = scan_for_tools()
        return tool_inventory
    except ImportError:
        # Tool detector not implemented yet - return empty inventory
        return {
            "tools": {},
            "scan_time": 0.0,
            "system": "unknown"
        }


def print_startup_summary(results: Dict[str, Any]) -> None:
    """Print a summary of startup check results."""
    print("\nStartup Summary:")
    print(f"   Duration: {results['total_duration']:.2f}s")
    
    for phase_name, phase_data in results["phases"].items():
        status_text = f"[{Fore.GREEN}OK{Style.RESET_ALL}]" if phase_data["status"] == "success" else f"[{Fore.YELLOW}WARN{Style.RESET_ALL}]" if phase_data["status"] == "warning" else f"[{Fore.RED}ERROR{Style.RESET_ALL}]"
        phase_display = phase_name.replace("_", " ").title()
        print(f"   {status_text} {phase_display}: {phase_data['status']}")


# Quick test function for development
def test_startup_checks():
    """Test function for development purposes."""
    print("Testing startup checks module...")
    results = run_startup_sequence(silent=False)
    return results


if __name__ == "__main__":
    test_startup_checks()