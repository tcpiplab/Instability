"""
Layer 2 network diagnostics for Instability v3.

Provides OS detection, interface status, local IP detection,
and basic network configuration information.
"""

import os
import sys
import platform
import socket
import subprocess
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import colorama for terminal colors
from colorama import Fore, Style

# Import configuration
from config import PING_TIMEOUT


def get_local_ip(interface: str = None, silent: bool = False) -> Dict[str, Any]:
    """
    Get the local IP address.
    
    Args:
        interface: Specific interface to check (optional)
        silent: If True, suppress output except errors
        
    Returns:
        Standardized result dictionary
    """
    start_time = datetime.now()
    
    try:
        if interface:
            # Get IP for specific interface
            ip_address = get_interface_ip(interface)
        else:
            # Get primary local IP by connecting to remote address
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                ip_address = s.getsockname()[0]
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if not silent:
            print(f"Local IP: {ip_address}")
        
        return {
            "success": True,
            "exit_code": 0,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "get_local_ip",
            "command_executed": f"get_local_ip(interface={interface})",
            "stdout": ip_address,
            "stderr": "",
            "parsed_data": {
                "ip_address": ip_address,
                "interface": interface or "primary"
            },
            "error_type": None,
            "error_message": None,
            "target": interface,
            "options_used": {"interface": interface}
        }
    
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Failed to get local IP: {Fore.RED}{e}{Style.RESET_ALL}"
        
        if not silent:
            print(f"Error: {error_msg}")
        
        return {
            "success": False,
            "exit_code": 1,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "get_local_ip",
            "command_executed": f"get_local_ip(interface={interface})",
            "stdout": "",
            "stderr": str(e),
            "parsed_data": {},
            "error_type": "network",
            "error_message": error_msg,
            "target": interface,
            "options_used": {"interface": interface}
        }


def check_interface_status(interface: str = None, silent: bool = False) -> Dict[str, Any]:
    """
    Check network interface status and configuration.
    
    Args:
        interface: Specific interface to check (if None, checks all)
        silent: If True, suppress output except errors
        
    Returns:
        Standardized result dictionary
    """
    start_time = datetime.now()
    
    try:
        interfaces = get_all_interfaces()
        
        if interface:
            # Filter to specific interface
            filtered_interfaces = [iface for iface in interfaces if iface["name"] == interface]
            if not filtered_interfaces:
                raise Exception(f"Interface {interface} not found")
            interfaces = filtered_interfaces
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if not silent:
            print(f"Network interfaces ({len(interfaces)} found):")
            for iface in interfaces:
                status_icon = "[UP]" if iface["status"] == "up" else "[DOWN]"
                print(f"  {status_icon} {iface['name']}: {iface['ip']} ({iface['status']})")
        
        return {
            "success": True,
            "exit_code": 0,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "check_interface_status",
            "command_executed": f"check_interface_status(interface={interface})",
            "stdout": f"Found {len(interfaces)} interfaces",
            "stderr": "",
            "parsed_data": {
                "interfaces": interfaces,
                "interface_count": len(interfaces)
            },
            "error_type": None,
            "error_message": None,
            "target": interface,
            "options_used": {"interface": interface}
        }
    
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Failed to check interface status: {Fore.RED}{e}{Style.RESET_ALL}"
        
        if not silent:
            print(f"Error: {error_msg}")
        
        return {
            "success": False,
            "exit_code": 1,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "check_interface_status",
            "command_executed": f"check_interface_status(interface={interface})",
            "stdout": "",
            "stderr": str(e),
            "parsed_data": {},
            "error_type": "execution",
            "error_message": error_msg,
            "target": interface,
            "options_used": {"interface": interface}
        }


def get_system_info(silent: bool = False) -> Dict[str, Any]:
    """
    Get comprehensive system information.
    
    Args:
        silent: If True, suppress output except errors
        
    Returns:
        Standardized result dictionary
    """
    start_time = datetime.now()
    
    try:
        system_info = {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "username": os.getenv("USER") or os.getenv("USERNAME") or "unknown"
        }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if not silent:
            print(f"System Information:")
            print(f"  Hostname: {system_info['hostname']}")
            print(f"  OS: {system_info['platform']} {system_info['platform_release']}")
            print(f"  Architecture: {system_info['architecture']}")
            print(f"  User: {system_info['username']}")
        
        return {
            "success": True,
            "exit_code": 0,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "get_system_info",
            "command_executed": "get_system_info()",
            "stdout": f"System: {system_info['platform']} {system_info['platform_release']}",
            "stderr": "",
            "parsed_data": system_info,
            "error_type": None,
            "error_message": None,
            "target": None,
            "options_used": {}
        }
    
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Failed to get system info: {Fore.RED}{e}{Style.RESET_ALL}"
        
        if not silent:
            print(f"Error: {error_msg}")
        
        return {
            "success": False,
            "exit_code": 1,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "get_system_info",
            "command_executed": "get_system_info()",
            "stdout": "",
            "stderr": str(e),
            "parsed_data": {},
            "error_type": "execution",
            "error_message": error_msg,
            "target": None,
            "options_used": {}
        }


def get_gateway_info(silent: bool = False) -> Dict[str, Any]:
    """
    Get default gateway information.
    
    Args:
        silent: If True, suppress output except errors
        
    Returns:
        Standardized result dictionary
    """
    start_time = datetime.now()
    
    try:
        gateway_ip = get_default_gateway()
        
        # Try to get gateway MAC address
        gateway_mac = None
        try:
            gateway_mac = get_mac_address(gateway_ip)
        except Exception:
            pass
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if not silent:
            print(f"Default Gateway:")
            print(f"  IP: {gateway_ip}")
            if gateway_mac:
                print(f"  MAC: {gateway_mac}")
        
        return {
            "success": True,
            "exit_code": 0,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "get_gateway_info",
            "command_executed": "get_gateway_info()",
            "stdout": f"Gateway: {gateway_ip}",
            "stderr": "",
            "parsed_data": {
                "gateway_ip": gateway_ip,
                "gateway_mac": gateway_mac
            },
            "error_type": None,
            "error_message": None,
            "target": gateway_ip,
            "options_used": {}
        }
    
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Failed to get gateway info: {Fore.RED}{e}{Style.RESET_ALL}"
        
        if not silent:
            print(f"Error: {error_msg}")
        
        return {
            "success": False,
            "exit_code": 1,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "get_gateway_info",
            "command_executed": "get_gateway_info()",
            "stdout": "",
            "stderr": str(e),
            "parsed_data": {},
            "error_type": "network",
            "error_message": error_msg,
            "target": None,
            "options_used": {}
        }


# Helper functions

def get_interface_ip(interface: str) -> str:
    """Get IP address for a specific interface."""
    system = platform.system()
    
    if system == "Windows":
        # Windows implementation
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Parse Windows output (simplified)
        return parse_windows_interface_ip(result.stdout, interface)
    else:
        # Unix/Linux/macOS implementation
        result = subprocess.run(
            ["ifconfig", interface],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return parse_unix_interface_ip(result.stdout)
        else:
            raise Exception(f"Interface {interface} not found")


def get_all_interfaces() -> List[Dict[str, Any]]:
    """Get information about all network interfaces."""
    interfaces = []
    system = platform.system()
    
    try:
        if system == "Windows":
            # Windows implementation using ipconfig
            result = subprocess.run(
                ["ipconfig", "/all"],
                capture_output=True,
                text=True,
                timeout=15
            )
            interfaces = parse_windows_interfaces(result.stdout)
        else:
            # Unix/Linux/macOS implementation using ifconfig
            result = subprocess.run(
                ["ifconfig"],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                interfaces = parse_unix_interfaces(result.stdout)
    except Exception:
        # Fallback: minimal interface detection
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            interfaces = [{
                "name": "default",
                "ip": local_ip,
                "status": "up",
                "mac": None
            }]
        except Exception:
            interfaces = [{
                "name": "unknown",
                "ip": "127.0.0.1",
                "status": "unknown",
                "mac": None
            }]
    
    return interfaces


def parse_unix_interfaces(ifconfig_output: str) -> List[Dict[str, Any]]:
    """Parse Unix/Linux/macOS ifconfig output."""
    interfaces = []
    current_interface = None
    
    for line in ifconfig_output.split('\n'):
        # New interface line
        if line and not line.startswith(' ') and not line.startswith('\t'):
            if current_interface:
                interfaces.append(current_interface)
            
            interface_name = line.split(':')[0]
            if interface_name and interface_name != "lo":  # Skip loopback
                current_interface = {
                    "name": interface_name,
                    "ip": None,
                    "status": "up" if "UP" in line else "down",
                    "mac": None
                }
        
        # IP address line
        elif current_interface and "inet " in line:
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                current_interface["ip"] = ip_match.group(1)
        
        # MAC address line
        elif current_interface and ("ether " in line or "HWaddr " in line):
            mac_match = re.search(r'([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})', line, re.IGNORECASE)
            if mac_match:
                current_interface["mac"] = mac_match.group(1)
    
    # Add the last interface
    if current_interface:
        interfaces.append(current_interface)
    
    return [iface for iface in interfaces if iface["ip"]]  # Only return interfaces with IPs


def parse_windows_interfaces(ipconfig_output: str) -> List[Dict[str, Any]]:
    """Parse Windows ipconfig output (simplified)."""
    interfaces = []
    
    # Simple parsing for Windows - this is a basic implementation
    lines = ipconfig_output.split('\n')
    current_interface = None
    
    for line in lines:
        line = line.strip()
        
        # Interface name line
        if "adapter" in line.lower() and ":" in line:
            if current_interface and current_interface["ip"]:
                interfaces.append(current_interface)
            
            interface_name = line.split(":")[-1].strip()
            current_interface = {
                "name": interface_name,
                "ip": None,
                "status": "unknown",
                "mac": None
            }
        
        # IP address line
        elif current_interface and "IPv4 Address" in line:
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                current_interface["ip"] = ip_match.group(1)
                current_interface["status"] = "up"
    
    # Add the last interface
    if current_interface and current_interface["ip"]:
        interfaces.append(current_interface)
    
    return interfaces


def parse_unix_interface_ip(ifconfig_output: str) -> str:
    """Parse IP address from Unix ifconfig output for single interface."""
    ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ifconfig_output)
    if ip_match:
        return ip_match.group(1)
    raise Exception("No IP address found")


def parse_windows_interface_ip(ipconfig_output: str, interface: str) -> str:
    """Parse IP address from Windows ipconfig output for specific interface."""
    # Simplified Windows parsing
    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', ipconfig_output)
    if ip_match:
        return ip_match.group(1)
    raise Exception("No IP address found")


def get_default_gateway() -> str:
    """Get the default gateway IP address."""
    system = platform.system()
    
    try:
        if system == "Windows":
            result = subprocess.run(
                ["route", "print", "0.0.0.0"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Parse Windows route output
            for line in result.stdout.split('\n'):
                if "0.0.0.0" in line and "0.0.0.0" in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        return parts[2]  # Gateway IP
        else:
            # Unix/Linux/macOS
            result = subprocess.run(
                ["route", "-n", "get", "default"],
                capture_output=True,
                text=True,
                timeout=10
            )
            for line in result.stdout.split('\n'):
                if "gateway:" in line.lower():
                    return line.split()[-1]
            
            # Alternative method for Linux
            result = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                match = re.search(r'via (\d+\.\d+\.\d+\.\d+)', result.stdout)
                if match:
                    return match.group(1)
    
    except Exception:
        pass
    
    # Fallback: try to determine gateway by connecting
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            # Assume gateway is .1 of the same subnet
            gateway_ip = '.'.join(local_ip.split('.')[:-1]) + '.1'
            return gateway_ip
    except Exception:
        raise Exception("Unable to determine default gateway")


def get_mac_address(ip_address: str) -> Optional[str]:
    """Get MAC address for an IP address using ARP."""
    try:
        system = platform.system()
        
        if system == "Windows":
            result = subprocess.run(
                ["arp", "-a", ip_address],
                capture_output=True,
                text=True,
                timeout=5
            )
        else:
            result = subprocess.run(
                ["arp", "-n", ip_address],
                capture_output=True,
                text=True,
                timeout=5
            )
        
        if result.returncode == 0:
            # Parse MAC address from ARP output
            mac_match = re.search(r'([0-9a-f]{2}[:-][0-9a-f]{2}[:-][0-9a-f]{2}[:-][0-9a-f]{2}[:-][0-9a-f]{2}[:-][0-9a-f]{2})', result.stdout, re.IGNORECASE)
            if mac_match:
                return mac_match.group(1)
    
    except Exception:
        pass
    
    return None


# Quick test function for development
def test_layer2_diagnostics():
    """Test function for development purposes."""
    print("Testing Layer 2 diagnostics...")
    
    # Test functions
    test_functions = [
        ("get_system_info", lambda: get_system_info(silent=False)),
        ("get_local_ip", lambda: get_local_ip(silent=False)),
        ("check_interface_status", lambda: check_interface_status(silent=False)),
        ("get_gateway_info", lambda: get_gateway_info(silent=False))
    ]
    
    for func_name, func in test_functions:
        print(f"\n--- Testing {func_name} ---")
        try:
            result = func()
            print(f"Success: {result['success']}")
            if result['parsed_data']:
                print(f"Data: {list(result['parsed_data'].keys())}")
        except Exception as e:
            print(f"Error: {Fore.RED}{e}{Style.RESET_ALL}")


if __name__ == "__main__":
    test_layer2_diagnostics()