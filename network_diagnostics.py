"""
Network Diagnostics module for Instability v2

This module provides a registry of network diagnostic tools and handles
their execution. It can use tools from the original codebase when available,
use migrated tools from the network_tools package, and provides fallback 
implementations for essential tools to ensure the chatbot can function 
even in offline situations.
"""

import os
import sys
import socket
import subprocess
import platform
import json
import time
import re
from datetime import datetime
from typing import Dict, Any, Callable, Optional, List
from colorama import Fore, Style

# Import migrated tools from network_tools package
from network_tools import check_external_ip_main, get_public_ip, web_check_main, resolver_check_main, monitor_dns_resolvers, dns_check_main

# Import standardized tool result functions
from utils import create_success_result, create_error_result, wrap_legacy_result, standardize_tool_output

# Import centralized configuration
from config import get_dns_servers, DNS_TEST_SERVERS, COMMON_PORTS

# Import v3 pentest tools
try:
    from pentest.nmap_wrapper import run_nmap_scan, quick_port_scan, network_discovery, service_version_scan, os_detection_scan, comprehensive_scan
    PENTEST_TOOLS_AVAILABLE = True
except ImportError as import_nmap_error:
    print(f"{Fore.YELLOW}Warning: Pentest tools not available: {import_nmap_error}{Style.RESET_ALL}")
    PENTEST_TOOLS_AVAILABLE = False

# Import v3 layer2 diagnostic tools
try:
    from network.layer2_diagnostics import check_interface_status as _check_interface_status, get_system_info as _get_system_info, get_gateway_info as _get_gateway_info
    LAYER2_TOOLS_AVAILABLE = True
    
    # Create module-level functions for direct import
    def check_interface_status(interface: str = None, silent: bool = False):
        """Check network interface status and configuration for all interfaces or a specific one."""
        return _check_interface_status(interface=interface, silent=silent)
    
    def get_system_info_v3(silent: bool = False):
        """Get comprehensive system information including OS details."""
        return _get_system_info(silent=silent)
    
    def get_gateway_info(silent: bool = False):
        """Get default gateway information including IP and MAC address."""
        return _get_gateway_info(silent=silent)
        
except ImportError as import_layer2_tools_error:
    print(f"{Fore.YELLOW}Warning: Layer2 diagnostic tools not available: {import_layer2_tools_error}{Style.RESET_ALL}")
    LAYER2_TOOLS_AVAILABLE = False

# Add parent directory to path to allow importing from original modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Attempt to import original tools
ORIGINAL_TOOLS_AVAILABLE = False
try:
    # Import core modules from original codebase
    # Note: check_external_ip, web_check, resolver_check and dns_check have been migrated to network_tools package
    from check_if_external_ip_changed import did_external_ip_change
    # resolver_check has been migrated to network_tools package
    # dns_check has been migrated to network_tools package
    from check_layer_two_network import report_link_status_and_type
    from whois_check import main as whois_check_main
    from os_utils import get_os_type

    ORIGINAL_TOOLS_AVAILABLE = True
except ImportError as import_error:
    print(f"{Fore.YELLOW}Warning: Some original tools not available: {import_error}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Fallback implementations will be used where possible.{Style.RESET_ALL}")


# Basic tool implementations (fallbacks if original tools are not available)

def get_os_info() -> Dict[str, Any]:
    """Get information about the operating system and environment"""
    start_time = datetime.now()
    
    try:
        if ORIGINAL_TOOLS_AVAILABLE:
            try:
                legacy_result = get_os_type()
                execution_time = (datetime.now() - start_time).total_seconds()
                return wrap_legacy_result(
                    tool_name="get_os_info",
                    legacy_result=legacy_result,
                    execution_time=execution_time,
                    command_executed="get_os_type() (original tool)"
                )
            except Exception as error_get_os_type:
                print(f"{Fore.YELLOW}Error using original get_os_type: {error_get_os_type}{Style.RESET_ALL}")

        # Fallback implementation
        system = platform.system()
        release = platform.release()
        version = platform.version()
        machine = platform.machine()
        processor = platform.processor()
        
        result_str = f"{system} {release} ({version}) {machine} {processor}"
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return create_success_result(
            tool_name="get_os_info",
            execution_time=execution_time,
            command_executed="platform.system() + details",
            parsed_data={
                "system": system,
                "release": release,
                "version": version,
                "machine": machine,
                "processor": processor,
                "summary": result_str
            },
            stdout=result_str
        )
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        return create_error_result(
            tool_name="get_os_info",
            execution_time=execution_time,
            error_message=f"Failed to get OS info: {str(e)}",
            error_type="execution",
            command_executed="platform module calls"
        )


@standardize_tool_output()
def get_local_ip() -> str:
    """Get the local IP address of this machine"""
    try:
        # Create a socket to get the local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Connect to a public IP (doesn't actually send packets)
            s.connect((DNS_TEST_SERVERS[0], 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception as e:
        return f"Error getting local IP: {Fore.RED}{e}{Style.RESET_ALL}"


@standardize_tool_output()
def get_default_gateway() -> str:
    """Get the default gateway IP address and interface information"""
    try:
        system = platform.system().lower()
        
        if system == 'linux':
            # Use ip route command on Linux
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse output like: "default via 192.168.1.1 dev eth0 proto dhcp metric 100"
                lines = result.stdout.strip().split('\n')
                gateway_info = []
                
                for line in lines:
                    if 'via' in line:
                        parts = line.split()
                        gateway_ip = parts[parts.index('via') + 1]
                        
                        # Extract interface name
                        interface = 'unknown'
                        if 'dev' in parts:
                            interface = parts[parts.index('dev') + 1]
                        
                        # Extract metric if present
                        metric = 'unknown'
                        if 'metric' in parts:
                            metric = parts[parts.index('metric') + 1]
                        
                        # Extract protocol if present
                        proto = 'unknown'
                        if 'proto' in parts:
                            proto = parts[parts.index('proto') + 1]
                        
                        gateway_info.append(f"Gateway: {gateway_ip}, Interface: {interface}, Protocol: {proto}, Metric: {metric}")
                
                return '\n'.join(gateway_info) if gateway_info else "No default gateway found"
            
            # Fallback to route command for Linux
            result = subprocess.run(['route', '-n'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.startswith('0.0.0.0') or 'default' in line.lower():
                        parts = line.split()
                        if len(parts) >= 2:
                            return f"Gateway: {parts[1]} (via route command)"
                            
        elif system == 'darwin':  # macOS
            # Use netstat on macOS (ip command not available by default)
            result = subprocess.run(['netstat', '-rn'], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.startswith('default') or line.startswith('0.0.0.0'):
                        parts = line.split()
                        if len(parts) >= 2:
                            gateway_ip = parts[1]
                            interface = parts[-1] if len(parts) > 5 else 'unknown'
                            return f"Gateway: {gateway_ip}, Interface: {interface} (macOS netstat)"
        
        elif system == 'windows':
            # Use route print command on Windows
            result = subprocess.run(['route', 'print', '0.0.0.0'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if '0.0.0.0' in line and 'Gateway' not in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            return f"Gateway: {parts[2]} (Windows route)"
        
        return "Could not determine default gateway"
        
    except subprocess.TimeoutExpired:
        return "Timeout while getting gateway information"
    except FileNotFoundError:
        return "Network commands not available on this system"
    except Exception as e:
        return f"Error getting default gateway: {str(e)}"


@standardize_tool_output()
def get_external_ip() -> str:
    """Get the external/public IP address"""
    # Use the migrated check_external_ip module
    try:
        return get_public_ip()
    except Exception as e:
        print(f"{Fore.YELLOW}Error using migrated external IP check: {e}{Style.RESET_ALL}")
        return "Could not determine external IP (offline or no connectivity)"


@standardize_tool_output()
def get_interface_config() -> str:
    """Get network interface configuration including DHCP vs static detection"""
    try:
        system = platform.system().lower()
        interface_info = []
        
        if system == 'linux':
            # Get interface information using ip command (Linux)
            result = subprocess.run(['ip', 'addr', 'show'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Parse ip addr output
                interfaces = {}
                current_interface = None
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith(' '):
                        # New interface line
                        parts = line.split(':')
                        if len(parts) >= 2:
                            current_interface = parts[1].strip()
                            interfaces[current_interface] = {
                                'name': current_interface,
                                'addresses': [],
                                'status': 'DOWN'
                            }
                            if 'UP' in line:
                                interfaces[current_interface]['status'] = 'UP'
                    elif line.startswith('inet ') and current_interface:
                        # IPv4 address line
                        parts = line.split()
                        if len(parts) >= 2:
                            addr = parts[1]
                            interfaces[current_interface]['addresses'].append(addr)
                
                # Check for DHCP vs static configuration
                for iface_name, iface_data in interfaces.items():
                    if iface_data['status'] == 'UP' and iface_data['addresses']:
                        # Check DHCP lease files
                        dhcp_status = check_dhcp_status(iface_name)
                        
                        iface_info = f"Interface: {iface_name}\n"
                        iface_info += f"  Status: {iface_data['status']}\n"
                        iface_info += f"  Addresses: {', '.join(iface_data['addresses'])}\n"
                        iface_info += f"  Configuration: {dhcp_status}\n"
                        
                        interface_info.append(iface_info)
        
        elif system == 'darwin':  # macOS
            # Use ifconfig on macOS
            result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Parse ifconfig output
                current_interface = None
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('\t') and ':' in line:
                        # New interface line like "en0: flags=..."
                        interface_name = line.split(':')[0]
                        current_interface = interface_name
                        status = 'UP' if 'UP' in line else 'DOWN'
                        
                        iface_info = f"Interface: {interface_name}\n"
                        iface_info += f"  Status: {status}\n"
                        
                        interface_info.append(iface_info)
                    elif line.startswith('inet ') and current_interface:
                        # IPv4 address line
                        parts = line.split()
                        if len(parts) >= 2:
                            addr = parts[1]
                            # Update the last interface info with the address
                            if interface_info:
                                interface_info[-1] += f"  Address: {addr}\n"
                
                # Try to determine DHCP vs static for macOS interfaces
                for i, info in enumerate(interface_info):
                    if 'en0' in info or 'en1' in info:  # Common WiFi/Ethernet interfaces
                        dhcp_status = check_dhcp_status_macos()
                        interface_info[i] += f"  Configuration: {dhcp_status}\n"
        
        elif system == 'windows':
            # Use ipconfig /all on Windows
            result = subprocess.run(['ipconfig', '/all'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Parse ipconfig output
                lines = result.stdout.split('\n')
                current_adapter = None
                
                for line in lines:
                    line = line.strip()
                    if 'adapter' in line.lower() and ':' in line:
                        current_adapter = line
                        interface_info.append(f"\n{current_adapter}")
                    elif 'DHCP Enabled' in line:
                        dhcp_enabled = 'Yes' if 'Yes' in line else 'No'
                        interface_info.append(f"  DHCP: {dhcp_enabled}")
                    elif 'IPv4 Address' in line:
                        addr = line.split(':')[-1].strip()
                        interface_info.append(f"  IPv4: {addr}")
        
        return '\n'.join(interface_info) if interface_info else "No network interface information available"
        
    except subprocess.TimeoutExpired:
        return "Timeout while getting interface configuration"
    except FileNotFoundError:
        return "Network configuration commands not available"
    except Exception as e:
        return f"Error getting interface configuration: {str(e)}"


def check_dhcp_status_macos() -> str:
    """Check DHCP status on macOS using system configuration"""
    try:
        # Try to use networksetup to check if DHCP is enabled
        result = subprocess.run(['networksetup', '-getinfo', 'Wi-Fi'], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            if 'DHCP' in result.stdout:
                return "DHCP (macOS Wi-Fi)"
            elif 'Manually' in result.stdout:
                return "Static (macOS Wi-Fi)"
        
        # Try Ethernet if Wi-Fi fails
        result = subprocess.run(['networksetup', '-getinfo', 'Ethernet'], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            if 'DHCP' in result.stdout:
                return "DHCP (macOS Ethernet)"
            elif 'Manually' in result.stdout:
                return "Static (macOS Ethernet)"
        
        return "Unknown (macOS configuration method)"
    except Exception as e:
        return f"Unknown (macOS error: {str(e)})"


def check_dhcp_status(interface_name: str) -> str:
    """Check if an interface is using DHCP or static configuration"""
    try:
        system = platform.system().lower()
        
        if system == 'linux':
            # Check common DHCP lease file locations
            dhcp_lease_files = [
                f'/var/lib/dhcp/dhclient.{interface_name}.leases',
                f'/var/lib/dhclient/dhclient.{interface_name}.leases',
                '/var/lib/dhcp/dhclient.leases',
                '/var/lib/dhclient/dhclient.leases'
            ]
            
            for lease_file in dhcp_lease_files:
                if os.path.exists(lease_file):
                    with open(lease_file, 'r') as f:
                        content = f.read()
                        if interface_name in content or 'lease' in content:
                            return "DHCP (lease file found)"
            
            # Check NetworkManager if available
            try:
                result = subprocess.run(['nmcli', 'connection', 'show'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and 'dhcp' in result.stdout.lower():
                    return "DHCP (NetworkManager)"
            except FileNotFoundError:
                pass
            
            # Check systemd-networkd
            networkd_files = [
                f'/etc/systemd/network/{interface_name}.network',
                f'/run/systemd/network/{interface_name}.network'
            ]
            
            for net_file in networkd_files:
                if os.path.exists(net_file):
                    with open(net_file, 'r') as f:
                        content = f.read()
                        if 'DHCP=yes' in content or 'DHCP=true' in content:
                            return "DHCP (systemd-networkd)"
                        elif 'Address=' in content:
                            return "Static (systemd-networkd)"
        
        elif system == 'darwin':  # macOS
            # Check macOS network configuration
            try:
                result = subprocess.run(['networksetup', '-getinfo', f'"{interface_name}"'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    if 'DHCP' in result.stdout:
                        return "DHCP (macOS networksetup)"
                    elif 'Manually' in result.stdout:
                        return "Static (macOS networksetup)"
            except FileNotFoundError:
                pass
        
        return "Unknown (unable to determine)"
    
    except Exception as e:
        return f"Unknown (error: {str(e)})"


@standardize_tool_output()
def get_interface_mac_address(interface: str = None) -> str:
    """Get MAC address of a specific interface or all interfaces
    
    Args:
        interface: Interface name (e.g., 'eth0', 'en0', 'WiFi'). If None, lists all interfaces with MAC addresses.
    
    Returns:
        MAC address or interface list with MAC addresses
    """
    try:
        system = platform.system().lower()
        
        if interface:
            # Get MAC for specific interface
            mac_address = _get_single_interface_mac(interface, system)
            if mac_address:
                return f"Interface {interface}: {mac_address}"
            else:
                return f"Interface {interface}: MAC address not found"
        else:
            # List all interfaces with MAC addresses
            interfaces_with_mac = _get_all_interfaces_mac(system)
            if interfaces_with_mac:
                result = "Network interfaces with MAC addresses:\n"
                for iface_name, mac_addr in interfaces_with_mac.items():
                    result += f"  {iface_name}: {mac_addr}\n"
                return result.strip()
            else:
                return "No network interfaces with MAC addresses found"
                
    except Exception as e:
        return f"Error getting MAC address: {str(e)}"


def _get_single_interface_mac(interface: str, system: str) -> str:
    """Get MAC address for a single interface"""
    try:
        if system == 'linux':
            # Try ip link show first
            result = subprocess.run(['ip', 'link', 'show', interface], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                mac_match = re.search(r'link/ether ([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})', 
                                    result.stdout, re.IGNORECASE)
                if mac_match:
                    return mac_match.group(1)
            
            # Fallback to cat /sys/class/net/{interface}/address
            result = subprocess.run(['cat', f'/sys/class/net/{interface}/address'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
                
        elif system == 'darwin':  # macOS
            # Use ifconfig
            result = subprocess.run(['ifconfig', interface], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                mac_match = re.search(r'ether ([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})', 
                                    result.stdout, re.IGNORECASE)
                if mac_match:
                    return mac_match.group(1)
        
        elif system == 'windows':
            # Use getmac command
            result = subprocess.run(['getmac', '/fo', 'csv', '/v'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines[1:]:  # Skip header
                    if interface.lower() in line.lower():
                        parts = line.split(',')
                        if len(parts) >= 3:
                            mac = parts[2].strip('"')
                            if mac and mac != 'N/A':
                                return mac
                                
    except Exception:
        pass
    
    return None


def _get_all_interfaces_mac(system: str) -> Dict[str, str]:
    """Get MAC addresses for all interfaces"""
    interfaces = {}
    
    try:
        if system == 'linux':
            # Use ip link show
            result = subprocess.run(['ip', 'link', 'show'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                current_interface = None
                for line in result.stdout.split('\n'):
                    # Interface line: "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500..."
                    if re.match(r'^\d+:', line):
                        parts = line.split(':')
                        if len(parts) >= 2:
                            current_interface = parts[1].strip()
                    # MAC line: "    link/ether 00:1a:2b:3c:4d:ef brd ff:ff:ff:ff:ff:ff"
                    elif current_interface and 'link/ether' in line:
                        mac_match = re.search(r'link/ether ([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})', 
                                            line, re.IGNORECASE)
                        if mac_match:
                            interfaces[current_interface] = mac_match.group(1)
                            
        elif system == 'darwin':  # macOS
            # Use ifconfig
            result = subprocess.run(['ifconfig'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                current_interface = None
                for line in result.stdout.split('\n'):
                    # Interface line: "en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500"
                    if not line.startswith('\t') and ':' in line and 'flags=' in line:
                        current_interface = line.split(':')[0]
                    # MAC line: "\tether 00:1a:2b:3c:4d:ef"
                    elif current_interface and line.strip().startswith('ether '):
                        mac_match = re.search(r'ether ([0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2})', 
                                            line, re.IGNORECASE)
                        if mac_match:
                            interfaces[current_interface] = mac_match.group(1)
                            
        elif system == 'windows':
            # Use getmac command
            result = subprocess.run(['getmac', '/fo', 'csv', '/v'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split(',')
                        if len(parts) >= 3:
                            name = parts[0].strip('"')
                            mac = parts[2].strip('"')
                            if mac and mac != 'N/A':
                                interfaces[name] = mac
                                
    except Exception:
        pass
    
    return interfaces


@standardize_tool_output()
def check_internet_connection() -> str:
    """Check if the internet is reachable"""
    try:
        # Try to connect to a reliable server
        socket.create_connection((DNS_TEST_SERVERS[0], 53), timeout=3)
        return "Connected"
    except Exception:
        return "Disconnected"


@standardize_tool_output()
def check_dns_resolvers() -> str:
    """Check if DNS resolvers are working properly"""
    # Use the migrated resolver_check module
    try:
        return monitor_dns_resolvers()
    except Exception as e:
        print(f"{Fore.YELLOW}Error using migrated DNS resolver check: {e}{Style.RESET_ALL}")
        
        # Fallback implementation if the migrated module fails
        # Use centralized DNS server configuration
        all_servers = get_dns_servers(include_additional=True)
        resolver_names = ["Google Public DNS", "Cloudflare DNS", "OpenDNS", "Quad9 DNS", "Google Secondary", "Cloudflare Secondary", "OpenDNS Secondary"]
        resolvers = {}
        for i, server in enumerate(all_servers[:len(resolver_names)]):
            resolvers[resolver_names[i]] = server

        results = []
        for name, ip in resolvers.items():
            try:
                socket.create_connection((ip, 53), timeout=2)
                results.append(f"{name} ({ip}): Reachable")
            except Exception:
                results.append(f"{name} ({ip}): Unreachable")

        return "\n".join(results)


@standardize_tool_output()
def get_network_routes() -> str:
    """Get complete routing table information"""
    try:
        system = platform.system().lower()
        route_info = []
        
        if system == 'linux':
            # Get full routing table using ip command (Linux)
            result = subprocess.run(['ip', 'route', 'show'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                route_info.append("=== IP Routing Table ===")
                
                for line in lines:
                    if line.strip():
                        # Parse route information
                        parts = line.split()
                        if len(parts) >= 1:
                            destination = parts[0]
                            
                            # Extract gateway if present
                            gateway = "direct"
                            if 'via' in parts:
                                try:
                                    gateway = parts[parts.index('via') + 1]
                                except IndexError:
                                    pass
                            
                            # Extract interface if present
                            interface = "unknown"
                            if 'dev' in parts:
                                try:
                                    interface = parts[parts.index('dev') + 1]
                                except IndexError:
                                    pass
                            
                            # Extract metric if present
                            metric = "0"
                            if 'metric' in parts:
                                try:
                                    metric = parts[parts.index('metric') + 1]
                                except IndexError:
                                    pass
                            
                            # Extract protocol if present
                            proto = "unknown"
                            if 'proto' in parts:
                                try:
                                    proto = parts[parts.index('proto') + 1]
                                except IndexError:
                                    pass
                            
                            route_entry = f"  {destination:<18} -> {gateway:<15} via {interface:<8} (metric: {metric}, proto: {proto})"
                            route_info.append(route_entry)
            
            # Also get IPv6 routes if available
            try:
                result_v6 = subprocess.run(['ip', '-6', 'route', 'show'], 
                                         capture_output=True, text=True, timeout=5)
                if result_v6.returncode == 0 and result_v6.stdout.strip():
                    route_info.append("\n=== IPv6 Routing Table ===")
                    lines_v6 = result_v6.stdout.strip().split('\n')
                    for line in lines_v6[:10]:  # Limit to first 10 IPv6 routes
                        if line.strip():
                            route_info.append(f"  {line}")
            except Exception:
                pass  # IPv6 routes are optional
                
        elif system == 'darwin':  # macOS
            # Use netstat for routing table on macOS
            result = subprocess.run(['netstat', '-rn'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                route_info.append("=== macOS Routing Table ===")
                
                in_ipv4_section = False
                for line in lines:
                    if 'Routing tables' in line or 'Internet:' in line:
                        in_ipv4_section = True
                        continue
                    elif 'Internet6:' in line:
                        in_ipv4_section = False
                        continue
                    
                    if in_ipv4_section and line.strip():
                        # Look for route entries
                        if any(char.isdigit() for char in line) and ('.' in line or 'default' in line):
                            parts = line.split()
                            if len(parts) >= 2:
                                destination = parts[0]
                                gateway = parts[1] if len(parts) > 1 else 'direct'
                                interface = parts[-1] if len(parts) > 2 else 'unknown'
                                
                                route_entry = f"  {destination:<18} -> {gateway:<15} via {interface}"
                                route_info.append(route_entry)
        
        elif system == 'windows':
            # Use route print on Windows
            result = subprocess.run(['route', 'print'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                route_info.append("=== Windows Routing Table ===")
                
                in_ipv4_section = False
                for line in lines:
                    if 'IPv4 Route Table' in line:
                        in_ipv4_section = True
                        continue
                    elif 'IPv6 Route Table' in line:
                        in_ipv4_section = False
                        continue
                    
                    if in_ipv4_section and line.strip():
                        # Look for route entries (contain IP addresses)
                        if any(char.isdigit() for char in line) and '.' in line:
                            route_info.append(f"  {line.strip()}")
        
        # Add summary information
        if route_info:
            route_count = len([line for line in route_info if line.startswith('  ') and not line.startswith('  ===')])
            route_info.insert(1, f"Total routes: {route_count}\n")
        
        return '\n'.join(route_info) if route_info else "No routing information available"
        
    except subprocess.TimeoutExpired:
        return "Timeout while getting routing information"
    except FileNotFoundError:
        return "Routing commands not available on this system"
    except Exception as e:
        return f"Error getting routing information: {str(e)}"


@standardize_tool_output()
def get_dns_config() -> str:
    """Get the actual DNS servers configured on this system"""
    try:
        system = platform.system().lower()
        dns_info = []
        
        if system in ['linux', 'darwin']:  # Linux or macOS
            # Check /etc/resolv.conf first
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    resolv_content = f.read()
                    
                dns_servers = []
                for line in resolv_content.split('\n'):
                    line = line.strip()
                    if line.startswith('nameserver'):
                        parts = line.split()
                        if len(parts) >= 2:
                            dns_servers.append(parts[1])
                
                if dns_servers:
                    dns_info.append("=== DNS Configuration ===")
                    dns_info.append("Source: /etc/resolv.conf")
                    for i, server in enumerate(dns_servers, 1):
                        dns_info.append(f"  DNS Server {i}: {server}")
                else:
                    dns_info.append("No nameservers found in /etc/resolv.conf")
                    
            except FileNotFoundError:
                dns_info.append("Warning: /etc/resolv.conf not found")
            except PermissionError:
                dns_info.append("Warning: Cannot read /etc/resolv.conf (permission denied)")
            
            # On macOS, also check scutil for more detailed info
            if system == 'darwin':
                try:
                    result = subprocess.run(['scutil', '--dns'], 
                                          capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        dns_info.append("\n=== macOS DNS Configuration (scutil) ===")
                        lines = result.stdout.split('\n')
                        current_resolver = None
                        
                        for line in lines:
                            line = line.strip()
                            if 'resolver #' in line:
                                current_resolver = line
                                dns_info.append(f"\n{current_resolver}")
                            elif 'nameserver[' in line and current_resolver:
                                dns_info.append(f"  {line}")
                            elif 'domain' in line and current_resolver and ': ' in line:
                                dns_info.append(f"  {line}")
                                
                except FileNotFoundError:
                    dns_info.append("Note: scutil command not available")
                except Exception as e:
                    dns_info.append(f"Note: scutil error: {str(e)}")
        
        elif system == 'windows':
            # Use ipconfig /all on Windows
            try:
                result = subprocess.run(['ipconfig', '/all'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    dns_info.append("=== Windows DNS Configuration ===")
                    lines = result.stdout.split('\n')
                    current_adapter = None
                    
                    for line in lines:
                        line = line.strip()
                        if 'adapter' in line.lower() and ':' in line:
                            current_adapter = line
                            dns_info.append(f"\n{current_adapter}")
                        elif 'DNS Servers' in line and current_adapter:
                            dns_server = line.split(':')[-1].strip()
                            if dns_server:
                                dns_info.append(f"  Primary DNS: {dns_server}")
                        elif line and current_adapter and '.' in line and any(c.isdigit() for c in line):
                            # Additional DNS servers (usually indented)
                            if not any(skip in line.lower() for skip in ['adapter', 'description', 'physical']):
                                dns_info.append(f"  Secondary DNS: {line}")
                                
            except FileNotFoundError:
                dns_info.append("Error: ipconfig command not available")
            except Exception as e:
                dns_info.append(f"Error running ipconfig: {str(e)}")
        
        return '\n'.join(dns_info) if dns_info else "No DNS configuration information available"
        
    except Exception as e:
        return f"Error getting DNS configuration: {str(e)}"


@standardize_tool_output()
def get_network_config() -> str:
    """Get network configuration including IP addresses, netmasks, and subnet information"""
    try:
        system = platform.system().lower()
        network_info = []
        
        if system == 'linux':
            # Use ip addr show for detailed interface info
            result = subprocess.run(['ip', 'addr', 'show'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                network_info.append("=== Network Interface Configuration ===")
                current_interface = None
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and not line.startswith(' '):
                        # New interface line
                        parts = line.split(':')
                        if len(parts) >= 2:
                            current_interface = parts[1].strip()
                            status = 'UP' if 'UP' in line else 'DOWN'
                            network_info.append(f"\nInterface: {current_interface} ({status})")
                    elif line.startswith('inet ') and current_interface:
                        # IPv4 address line with CIDR notation
                        parts = line.split()
                        if len(parts) >= 2:
                            addr_cidr = parts[1]  # e.g., "192.168.1.100/24"
                            if '/' in addr_cidr:
                                ip, prefix = addr_cidr.split('/')
                                # Convert CIDR to netmask
                                netmask = cidr_to_netmask(int(prefix))
                                network_info.append(f"  IP Address: {ip}")
                                network_info.append(f"  Netmask: {netmask} (/{prefix})")
                                network_info.append(f"  Network: {calculate_network(ip, netmask)}")
                            else:
                                network_info.append(f"  IP Address: {addr_cidr}")
                                
        elif system == 'darwin':  # macOS
            # Use ifconfig for detailed interface info
            result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                network_info.append("=== Network Interface Configuration ===")
                current_interface = None
                
                for line in result.stdout.split('\n'):
                    original_line = line
                    line = line.strip()
                    
                    # Interface header: starts at beginning of line, contains colon
                    if line and not original_line.startswith('\t') and not original_line.startswith(' ') and ':' in line:
                        # New interface line
                        interface_name = line.split(':')[0]
                        current_interface = interface_name
                        status = 'UP' if 'UP' in line else 'DOWN'
                        network_info.append(f"\nInterface: {interface_name} ({status})")
                    
                    # IPv4 address: usually indented, starts with 'inet '
                    elif 'inet ' in line and current_interface and 'inet6' not in line:
                        # IPv4 address line: inet 192.168.1.244 netmask 0xffffff00 broadcast 192.168.1.255
                        parts = line.split()
                        if len(parts) >= 2:
                            ip = parts[1]
                            netmask_hex = None
                            
                            # Find netmask in the line
                            try:
                                netmask_idx = parts.index('netmask')
                                if netmask_idx + 1 < len(parts):
                                    netmask_hex = parts[netmask_idx + 1]
                            except ValueError:
                                pass
                            
                            # Convert hex netmask to decimal
                            if netmask_hex and netmask_hex.startswith('0x'):
                                try:
                                    netmask = hex_to_netmask(netmask_hex)
                                    network_info.append(f"  IP Address: {ip}")
                                    network_info.append(f"  Netmask: {netmask}")
                                    network_info.append(f"  Network: {calculate_network(ip, netmask)}")
                                except:
                                    network_info.append(f"  IP Address: {ip}")
                                    network_info.append(f"  Netmask: {netmask_hex} (hex)")
                            else:
                                network_info.append(f"  IP Address: {ip}")
                                
        elif system == 'windows':
            # Use ipconfig for Windows
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                network_info.append("=== Network Interface Configuration ===")
                current_adapter = None
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if 'adapter' in line.lower() and ':' in line:
                        current_adapter = line
                        network_info.append(f"\n{current_adapter}")
                    elif 'IPv4 Address' in line and current_adapter:
                        ip = line.split(':')[-1].strip()
                        network_info.append(f"  IP Address: {ip}")
                    elif 'Subnet Mask' in line and current_adapter:
                        netmask = line.split(':')[-1].strip()
                        network_info.append(f"  Netmask: {netmask}")
        
        return '\n'.join(network_info) if network_info else "No network configuration information available"
        
    except subprocess.TimeoutExpired:
        return "Timeout while getting network configuration"
    except FileNotFoundError:
        return "Network configuration commands not available"
    except Exception as e:
        return f"Error getting network configuration: {str(e)}"


def cidr_to_netmask(prefix_length: int) -> str:
    """Convert CIDR prefix length to dotted decimal netmask"""
    try:
        # Create a 32-bit mask with prefix_length bits set to 1
        mask = (0xffffffff >> (32 - prefix_length)) << (32 - prefix_length)
        # Convert to dotted decimal
        return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"
    except:
        return f"/{prefix_length}"


def hex_to_netmask(hex_mask: str) -> str:
    """Convert hexadecimal netmask to dotted decimal"""
    try:
        # Remove 0x prefix and convert to integer
        mask_int = int(hex_mask, 16)
        # Convert to dotted decimal
        return f"{(mask_int >> 24) & 0xff}.{(mask_int >> 16) & 0xff}.{(mask_int >> 8) & 0xff}.{mask_int & 0xff}"
    except:
        return hex_mask


def calculate_network(ip: str, netmask: str) -> str:
    """Calculate network address from IP and netmask"""
    try:
        ip_parts = [int(x) for x in ip.split('.')]
        mask_parts = [int(x) for x in netmask.split('.')]
        
        network_parts = [ip_parts[i] & mask_parts[i] for i in range(4)]
        return '.'.join(map(str, network_parts))
    except:
        return "Unable to calculate"


@standardize_tool_output()
def get_external_ip_netmask(ip: str = None) -> str:
    """Get the netmask/network range of an external IP address using WHOIS data
    
    Args:
        ip: External IP address to lookup (uses current external IP if not provided)
    
    Returns:
        String containing network range information
    """
    try:
        # If no IP provided, get our external IP
        if ip is None:
            if ORIGINAL_TOOLS_AVAILABLE:
                try:
                    # Use the migrated tool from network_tools
                    from network_tools import get_public_ip
                    ip = get_public_ip()
                except Exception:
                    return "Error: Unable to determine external IP address"
            else:
                return "Error: External IP lookup not available"
        
        # Use whois to get network information
        try:
            # First try using whois command if available
            result = subprocess.run(['whois', ip], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                whois_output = result.stdout.lower()
                
                # Look for common network range patterns
                network_patterns = [
                    r'netrange:\s*([0-9.]+)\s*-\s*([0-9.]+)',
                    r'inetnum:\s*([0-9.]+)\s*-\s*([0-9.]+)',
                    r'cidr:\s*([0-9./]+)',
                    r'network:\s*([0-9./]+)',
                    r'route:\s*([0-9./]+)'
                ]
                
                import re
                network_info = []
                
                for pattern in network_patterns:
                    matches = re.findall(pattern, whois_output)
                    if matches:
                        for match in matches:
                            if isinstance(match, tuple):
                                # Range format (start - end)
                                network_info.append(f"Range: {match[0]} - {match[1]}")
                            else:
                                # CIDR format
                                network_info.append(f"Network: {match}")
                
                # Look for netname/organization
                org_patterns = [
                    r'netname:\s*([^\n\r]+)',
                    r'orgname:\s*([^\n\r]+)',
                    r'org-name:\s*([^\n\r]+)',
                    r'organisation:\s*([^\n\r]+)'
                ]
                
                org_info = []
                for pattern in org_patterns:
                    matches = re.findall(pattern, whois_output)
                    if matches:
                        org_info.extend([match.strip() for match in matches[:2]])  # Limit to first 2
                
                # Format result
                result_lines = [f"IP: {ip}"]
                
                if org_info:
                    result_lines.append(f"Organization: {org_info[0]}")
                
                if network_info:
                    result_lines.extend(network_info[:3])  # Limit to first 3 network entries
                else:
                    result_lines.append("Network range: Not found in WHOIS data")
                
                return "\n".join(result_lines)
            
        except subprocess.TimeoutExpired:
            return f"Error: WHOIS lookup for {ip} timed out"
        except FileNotFoundError:
            pass  # whois command not available, try alternative
        
        # Fallback: try to extract network info using simple IP analysis
        try:
            ip_parts = [int(x) for x in ip.split('.')]
            
            # Determine class and typical netmask
            if ip_parts[0] < 128:
                # Class A (typically /8 but ISPs use smaller blocks)
                typical_mask = "/16 to /24"
            elif ip_parts[0] < 192:
                # Class B (typically /16 but ISPs use smaller blocks)  
                typical_mask = "/20 to /24"
            else:
                # Class C (typically /24)
                typical_mask = "/24 to /28"
            
            return f"IP: {ip}\nEstimated ISP block size: {typical_mask}\nNote: Use WHOIS for exact network range"
            
        except Exception:
            return f"Error: Unable to analyze IP address {ip}"
            
    except Exception as e:
        return f"Error looking up network information for {ip}: {str(e)}"


@standardize_tool_output()
def ping_target(host: str = None, target: str = None, arg_name: str = None, count: int = 4) -> str:
    """Ping a target host and measure response time
    
    Args:
        host: Target host to ping (default: 8.8.8.8)
        target: Alternative parameter name for host (for compatibility)
        arg_name: Generic parameter name used by chatbot (for compatibility)
        count: Number of ping packets to send (default: 4)
    
    Returns:
        String containing ping results
    """

    destination = None

    try:
        # Allow multiple parameter names (precedence: arg_name > target > host)
        if arg_name is not None:
            destination = arg_name
        elif target is not None:
            destination = target
        elif host is not None:
            destination = host
        else:
            # Use default DNS server from configuration
            destination = DNS_TEST_SERVERS[0]
        
        # Determine command based on operating system
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", str(count), destination]
        else:
            cmd = ["ping", "-c", str(count), destination]

        # Run the ping command
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            # Extract average time from output
            output = result.stdout

            # Try to extract average time (format varies by OS)
            if "Average" in output or "average" in output:
                for line in output.split("\n"):
                    if "Average" in line or "average" in line:
                        return line.strip()

            # If we can't extract the average, return the entire output
            return output
        else:
            return f"Ping failed with exit code {result.returncode}: {result.stderr}"
    except subprocess.TimeoutExpired:
        return f"Ping to {destination} timed out after 10 seconds"
    except Exception as e:
        return f"Error pinging {destination}: {Fore.RED}{e}{Style.RESET_ALL}"


@standardize_tool_output()
def check_dns_root_servers() -> str:
    """Check if DNS root servers are reachable"""
    # Use the migrated dns_check module
    try:
        return dns_check_main(silent=True, polite=False)
    except Exception as e:
        print(f"{Fore.YELLOW}Error using migrated DNS root server check: {e}{Style.RESET_ALL}")
        
        # Fallback implementation if the migrated module fails
        root_servers = {
            "a.root-servers.net": "198.41.0.4",
            "b.root-servers.net": "199.9.14.201",
            "c.root-servers.net": "192.33.4.12",
            "d.root-servers.net": "199.7.91.13",
            "e.root-servers.net": "192.203.230.10",
            "f.root-servers.net": "192.5.5.241"
        }

        results = []
        for name, ip in root_servers.items():
            try:
                socket.create_connection((ip, 53), timeout=2)
                results.append(f"{name} ({ip}): Reachable")
            except Exception:
                results.append(f"{name} ({ip}): Unreachable")

        return "\n".join(results)


@standardize_tool_output()
def check_websites() -> str:
    """Check if major websites are reachable"""
    # Use the migrated web_check module
    try:
        return web_check_main(silent=True, polite=False)
    except Exception as e:
        print(f"{Fore.YELLOW}Error using migrated website check: {e}{Style.RESET_ALL}")
        
        # Fallback implementation if the migrated module fails
        websites = [
            "google.com",
            "amazon.com",
            "cloudflare.com",
            "microsoft.com",
            "apple.com",
            "github.com"
        ]

        results = []
        for site in websites:
            try:
                # Try DNS resolution
                ip = socket.gethostbyname(site)

                # Try connecting to port 80 (HTTP)
                socket.create_connection((site, 80), timeout=2)
                results.append(f"{site} ({ip}): Reachable")
            except socket.gaierror:
                results.append(f"{site}: DNS resolution failed")
            except Exception as e:
                results.append(f"{site}: Error - {str(e)}")

        return "\n".join(results)


@standardize_tool_output()
def check_local_network() -> str:
    """Check local network interfaces and link status"""
    if ORIGINAL_TOOLS_AVAILABLE:
        try:
            return report_link_status_and_type()
        except Exception as e:
            print(f"{Fore.YELLOW}Error using original network check: {e}{Style.RESET_ALL}")

    # Fallback implementation (platform-specific)
    try:
        if platform.system().lower() == "linux":
            cmd = ["ip", "addr", "show"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.stdout
        elif platform.system().lower() == "darwin":  # macOS
            cmd = ["ifconfig"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.stdout
        elif platform.system().lower() == "windows":
            cmd = ["ipconfig", "/all"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.stdout
        else:
            return f"Unsupported platform: {platform.system()}"
    except Exception as e:
        return f"Error checking local network: {Fore.RED}{e}{Style.RESET_ALL}"


# WHOIS servers and their IP addresses with descriptions
# Comprehensive list covering global IP allocation and domain registries
WHOIS_SERVERS_DICT = {
    "whois.apnic.net": (
    "APNIC WHOIS server for IP address and AS number allocation in the Asia-Pacific region", "202.12.29.140"),
    "whois.ripe.net": ("RIPE NCC WHOIS server for European IP addresses and AS number registrations", "193.0.6.135"),
    "whois.arin.net": ("ARIN WHOIS server for North American IP address and ASN allocations", "199.212.0.43"),
    "whois.afrinic.net": ("AFRINIC WHOIS server for African IP address space and AS number management", "196.216.2.2"),
    "whois.lacnic.net": (
    "LACNIC WHOIS server for Latin American and Caribbean IP address registrations", "200.3.14.10"),
    "whois.pir.org": ("Public Interest Registry WHOIS server for dot ORG domain registrations", "199.19.56.1"),
    "whois.educause.edu": (
    "EDUCAUSE WHOIS server for dot EDU domain name registrations in United States", "192.52.178.30"),
    "whois.iana.org": ("IANA WHOIS server for the root zone database and overall global IP address allocations to regional registries like ARIN and RIPE", "192.0.32.59"),
    "riswhois.ripe.net": ("RIPE RIS WHOIS server for BGP routing information and analysis", "193.0.19.33"),
    "whois.nic.mobi": ("Registry WHOIS server for dot MOBI top-level domain registrations", "194.169.218.57"),
    "whois.verisign-grs.com": ("Verisign Global Registry WHOIS server for looking up dot COM and dot NET domains", "199.7.59.74"),
    "whois.nic.google": ("Google Registry WHOIS server for Google-operated TLD registrations", "216.239.32.10"),
    "whois.nic.io": ("Internet Computer Bureau WHOIS server for .io domain registrations", "193.223.78.42"),
    "whois.nic.co": (".CO Internet S.A.S. WHOIS server for .co domain registrations", "156.154.100.224"),
    "whois.nic.xyz": ("XYZ.COM LLC WHOIS server for .xyz domain registrations", "185.24.64.96"),
    "whois.nic.club": (".CLUB Domains, LLC WHOIS server for .club domain registrations", "108.59.160.175"),
    "whois.nic.info": ("Afilias WHOIS server for .info domain registrations", "199.19.56.1"),
    "whois.nic.biz": ("Neustar WHOIS server for .biz domain registrations", "156.154.100.224"),
    "whois.nic.us": ("NeuStar, Inc. WHOIS server for .us domain registrations", "156.154.100.224"),
    "whois.nic.tv": ("Verisign WHOIS server for .tv domain registrations", "192.42.93.30"),
    "whois.nic.asia": ("DotAsia WHOIS server for .asia domain registrations", "203.119.86.101"),
    "whois.nic.me": ("doMEn WHOIS server for .me domain registrations", "185.24.64.96"),
    "whois.nic.pro": ("RegistryPro WHOIS server for .pro domain registrations", "199.7.59.74"),
    "whois.nic.museum": ("Museum Domain Management Association WHOIS server for .museum domain registrations", "130.242.24.5"),
    "whois.nic.ai": ("Government of Anguilla WHOIS server for .ai domain registrations", "209.59.119.34"),
    "whois.nic.de": ("DENIC eG WHOIS server for .de domain registrations", "81.91.164.5"),
    "whois.registry.in": ("National Internet Exchange of India WHOIS server for .in domain registrations for India", "103.132.247.21"),
    "whois.jprs.jp": ("Japan Registry Services Co., Ltd. WHOIS server for .jp domain registrations for Japan", "117.104.133.169"),
    "whois.nic.fr": ("AFNIC WHOIS server for .fr domain registrations for France", "192.134.5.73"),
    "whois.registro.br": ("Comitê Gestor da Internet no Brasil WHOIS server for .br domain registrations for Brazil", "200.160.2.3"),
    "whois.nic.uk": ("Nominet UK WHOIS server for .uk domain registrations for the UK", "213.248.242.79"),
    "whois.auda.org.au": ("auDA WHOIS server for .au domain registrations for Australia", "199.15.80.233"),
    "whois.nic.it": ("IIT - CNR WHOIS server for .it domain registrations for Italy", "192.12.192.242"),
    "whois.cira.ca": ("Canadian Internet Registration Authority WHOIS server for .ca domain registrations", "192.228.29.2"),
    "whois.kr": ("KISA WHOIS server for .kr domain registrations for South Korea", "49.8.14.101")
}


def run_whois_command(whois_server_name: str, whois_server_ip: str) -> tuple:
    """Run the whois command for a specific server and IP.
    
    Args:
        whois_server_name: The hostname of the WHOIS server
        whois_server_ip: The IP address of the WHOIS server
        
    Returns:
        Tuple of (status, error) where status is "reachable" or "unreachable"
    """
    try:
        if platform.system().lower() in ["darwin", "linux"]:
            # Use socket connection test instead of actual whois command for speed
            socket.create_connection((whois_server_name, 43), timeout=10)
            return "reachable", None
        elif platform.system().lower() == "windows":
            # Use socket connection test for Windows too for consistency
            socket.create_connection((whois_server_name, 43), timeout=10)
            return "reachable", None
    except Exception as e:
        return "unreachable", str(e)


@standardize_tool_output()
def check_whois_servers() -> str:
    """Check if WHOIS servers are reachable (comprehensive global server list)"""
    from utils import ollama_shorten_output
    
    reachable_servers = []
    unreachable_servers = []
    whois_results = ""

    print(f"{Fore.CYAN}Starting WHOIS server monitoring at {time.ctime()}{Style.RESET_ALL}")
    whois_results += f"Starting WHOIS server monitoring at {time.ctime()}\n"
    
    # Count servers being checked
    num_servers = len(WHOIS_SERVERS_DICT)
    whois_results += f"Checking reachability of {num_servers} WHOIS servers worldwide...\n\n"

    # First round of checks
    for whois_server_name, (whois_server_description, ip) in WHOIS_SERVERS_DICT.items():
        status, error = run_whois_command(whois_server_name, ip)
        if status == "reachable":
            reachable_servers.append((whois_server_name, whois_server_description))
            whois_results += f"{whois_server_name} was reachable. It is the {whois_server_description}.\n"
        else:
            unreachable_servers.append((whois_server_name, error, whois_server_description))
            whois_results += f"{whois_server_name} was unreachable. The error was: {error}. It is the {whois_server_description}.\n"

    # Retry unreachable servers after a delay
    if unreachable_servers:
        whois_results += "\nRetrying unreachable servers...\n"
        time.sleep(2)  # Wait 2 seconds before retrying (reduced from 5)

        remaining_unreachable = []
        for whois_server_name, error, whois_server_description in unreachable_servers:
            # Get IP from the original dict for retry
            ip = WHOIS_SERVERS_DICT[whois_server_name][1]
            status, retry_error = run_whois_command(whois_server_name, ip)
            if status == "reachable":
                reachable_servers.append((whois_server_name, whois_server_description))
                whois_results += f"After retrying, {whois_server_name} was reachable.\n"
            else:
                remaining_unreachable.append((whois_server_name, retry_error, whois_server_description))
                whois_results += f"After retrying, {whois_server_name} was still unreachable. The error was: {retry_error}.\n"

        unreachable_servers = remaining_unreachable

    # Summary section
    whois_results += f"\nReachable WHOIS Servers ({len(reachable_servers)}):\n"
    for whois_server_name, _ in reachable_servers:
        whois_results += f"- {whois_server_name}\n"

    if len(unreachable_servers) == 0:
        whois_results += "\nAll WHOIS servers were reachable.\n"
    else:
        whois_results += f"\nUnreachable WHOIS Servers ({len(unreachable_servers)}):\n"
        for whois_server_name, error, _ in unreachable_servers:
            whois_results += f"- {whois_server_name}: Unreachable\n"

    # Apply Ollama shortening to reduce verbosity
    try:
        shortened_results = ollama_shorten_output(whois_results, max_lines=20, max_chars=1500)
        return shortened_results
    except Exception as e:
        print(f"{Fore.YELLOW}Warning: Could not shorten WHOIS results: {e}{Style.RESET_ALL}")
        # Fallback to simple truncation if Ollama fails
        lines = whois_results.split('\n')
        if len(lines) > 25:
            truncated = '\n'.join(lines[:25]) + f"\n\n[Output truncated - showed first 25 lines of {len(lines)} total lines]"
            return truncated
        return whois_results


def is_private_ip(ip: str) -> bool:
    """Check if an IP address is in RFC 1918 private address space"""
    try:
        import ipaddress
        ip_obj = ipaddress.IPv4Address(ip)
        
        # RFC 1918 private address ranges:
        # 10.0.0.0/8 (10.0.0.0 to 10.255.255.255)
        # 172.16.0.0/12 (172.16.0.0 to 172.31.255.255)  
        # 192.168.0.0/16 (192.168.0.0 to 192.168.255.255)
        private_networks = [
            ipaddress.IPv4Network('10.0.0.0/8'),
            ipaddress.IPv4Network('172.16.0.0/12'),
            ipaddress.IPv4Network('192.168.0.0/16')
        ]
        
        return any(ip_obj in network for network in private_networks)
    except Exception:
        return False


@standardize_tool_output()
def check_nat_status() -> str:
    """Check if we are running behind NAT by comparing local and external IP addresses.
    
    Returns:
        Detailed analysis including NAT status confirmation and labeled IP addresses
    """
    try:
        # Get local and external IP addresses - extract actual IPs from standardized results
        local_ip_result = get_local_ip()
        external_ip_result = get_external_ip()
        
        # Extract the actual IP addresses from the standardized result format
        if isinstance(local_ip_result, dict) and 'stdout' in local_ip_result:
            local_ip = local_ip_result['stdout']
        else:
            local_ip = str(local_ip_result)
            
        if isinstance(external_ip_result, dict) and 'stdout' in external_ip_result:
            external_ip = external_ip_result['stdout']
        else:
            external_ip = str(external_ip_result)
        
        # Check for errors in IP retrieval
        if "Error" in local_ip or "Could not determine" in external_ip:
            return f"Unable to determine NAT status.\nLocal IP: {local_ip}\nExternal IP: {external_ip}"
        
        # Build detailed response
        result = [f"Local IP Address: {local_ip}", f"External IP Address: {external_ip}"]

        # Determine NAT status
        is_nat = local_ip != external_ip and is_private_ip(local_ip)
        
        if is_nat:
            result.append("\nNAT Status: You ARE running behind NAT.")
            result.append(f"Your device has a private IP address ({local_ip}) on the local network,")
            result.append(f"but appears to the internet with a public IP address ({external_ip}).")
        else:
            if local_ip == external_ip:
                result.append("\nNAT Status: You are NOT running behind NAT.")
                result.append("Your device has the same IP address locally and externally,")
                result.append("indicating a direct internet connection.")
            else:
                result.append("\nNAT Status: Uncertain - unusual IP configuration detected.")
                result.append(f"Local IP ({local_ip}) differs from external IP ({external_ip}),")
                result.append("but local IP is not a standard private address.")
        
        return "\n".join(result)
            
    except Exception as e:
        return f"Error checking NAT status: {Fore.RED}{e}{Style.RESET_ALL}"


@standardize_tool_output()
def run_speed_test() -> str:
    """Use this tool to run a speed test.
    This speed test tool will first check to make sure we are running macOS, also called Darwin.
    This means that it is not necessary to first run the get_os_info tool because this tool will do that for you.
    
    This tool uses the built-in networkQuality command on macOS 12 (Monterey) 
    or later to measure network speed, latency, and responsiveness.
    
    Returns:
        Formatted string with network quality metrics
    """
    # Check if running on macOS
    if platform.system().lower() != "darwin":
        return "This tool only works on macOS 12 (Monterey) or later."
    
    try:
        # Run the networkQuality command
        process = subprocess.run(
            ["networkQuality", "-p", "-s"],
            capture_output=True,
            text=True,
            timeout=90  # Network quality tests can take time
        )
        
        # Check for errors
        if process.returncode != 0:
            return f"Error running network quality test: {process.stderr}"
        
        # Parse the output
        result = parse_network_quality_output(process.stdout)
        
        if result:
            return generate_speed_test_report(result)
        else:
            return "Could not parse network quality test results."
            
    except FileNotFoundError:
        return "Error: networkQuality command not found. This requires macOS 12 (Monterey) or later."
    except subprocess.TimeoutExpired:
        return "Network quality test timed out after 90 seconds."
    except Exception as e:
        return f"Error running network quality test: {str(e)}"


def parse_network_quality_output(output: str) -> dict:
    """Parse the output of the networkQuality command
    
    Args:
        output: Raw output from the networkQuality command
        
    Returns:
        Dictionary with parsed results
    """
    lines = output.splitlines()
    summary = {}

    for line in lines:
        if "Uplink capacity" in line:
            summary['uplink_capacity'] = line.split(': ')[1]
        elif "Downlink capacity" in line:
            summary['downlink_capacity'] = line.split(': ')[1]
        elif "Uplink Responsiveness" in line:
            summary['uplink_responsiveness'] = line.split(': ')[1]
        elif "Downlink Responsiveness" in line:
            summary['downlink_responsiveness'] = line.split(': ')[1]
        elif "Idle Latency" in line:
            summary['idle_latency'] = line.split(': ')[1]

    return summary


@standardize_tool_output()
def generate_speed_test_report(summary: dict) -> str:
    """Generate a human-readable report from speed test results
    
    Args:
        summary: Dictionary with parsed network quality results
        
    Returns:
        Formatted string with results and comparisons
    """
    # Extract speeds (handle potential format issues gracefully)
    try:
        uplink_mbps = float(summary.get('uplink_capacity', '0 Mbps').split(' ')[0])
        downlink_mbps = float(summary.get('downlink_capacity', '0 Mbps').split(' ')[0])
        
        # Generate comparison sentences
        uplink_comparison = compare_speed_to_telecom(uplink_mbps) if uplink_mbps > 0 else "uplink capacity could not be measured"
        downlink_comparison = compare_speed_to_telecom(downlink_mbps) if downlink_mbps > 0 else "downlink capacity could not be measured"
    except (ValueError, IndexError):
        uplink_comparison = "uplink capacity format could not be parsed"
        downlink_comparison = "downlink capacity format could not be parsed"
    
    # Format the report
    report = [
        "Network Quality Test Results:",
        "-----------------------------",
        f"Upload speed: {summary.get('uplink_capacity', 'unknown')}",
        f"Download speed: {summary.get('downlink_capacity', 'unknown')}",
        f"Upload responsiveness: {summary.get('uplink_responsiveness', 'unknown')}",
        f"Download responsiveness: {summary.get('downlink_responsiveness', 'unknown')}",
        f"Idle latency: {summary.get('idle_latency', 'unknown')}",
        "",
        "Speed Comparisons:",
        f"Upload: {uplink_comparison}",
        f"Download: {downlink_comparison}"
    ]
    
    return "\n".join(report)


@standardize_tool_output()
def compare_speed_to_telecom(speed_mbps: float) -> str:
    """Compare a network speed to common telecom reference points
    
    Args:
        speed_mbps: Speed in Megabits per second
        
    Returns:
        String describing how the speed compares to common standards
    """
    telecom_speeds = [
        (0.064, "an ISDN line (single channel)"),
        (0.128, "a dual-channel ISDN line"),
        (0.384, "basic DSL at 384 kbps"),
        (1.0, "roughly one Mbps"),
        (1.544, "a single T-1 line"),
        (0.772, "half a T-1 line"),
        (2.0, "DSL2 at 2 Mbps"),
        (3.0, "typical DSL speeds"),
        (5.0, "a basic cable internet connection or ADSL"),
        (10.0, "ten T-1 bonded lines, or old school Ethernet"),
        (22.368, "about 15 bonded T-1 lines"),
        (45.0, "a DS-3 line or T-3 line"),
        (22.5, "half a T-3 line"),
        (100.0, "Fast Ethernet"),
        (155.0, "an OC-3 circuit"),
        (310.0, "two OC-3 circuits"),
        (622.0, "an OC-12 circuit"),
        (1244.0, "two OC-12 circuits"),
        (2488.0, "an OC-48 circuit"),
        (4976.0, "two OC-48 circuits"),
        (10000.0, "10 Gigabit Ethernet"),
        (40000.0, "40 Gigabit Ethernet"),
        (100000.0, "100 Gigabit Ethernet"),
    ]

    # Find the closest telecom speed
    closest_speed = min(telecom_speeds, key=lambda x: abs(speed_mbps - x[0]))

    # Generate the sentence fragment
    return f"this speed is similar to {closest_speed[1]}"


# Tool registry - dict mapping tool names to functions
def get_available_tools() -> Dict[str, Callable]:
    """
    Get a dictionary of all available diagnostic tools

    Returns:
        Dict mapping tool names to their functions
    """
    tools = {
        "get_os_info": get_os_info,
        "get_local_ip": get_local_ip,
        "get_external_ip": get_external_ip,
        "get_default_gateway": get_default_gateway,
        "get_interface_config": get_interface_config,
        "get_interface_mac_address": get_interface_mac_address,
        "get_network_routes": get_network_routes,
        "get_dns_config": get_dns_config,
        "get_network_config": get_network_config,
        "get_external_ip_netmask": get_external_ip_netmask,
        "check_internet_connection": check_internet_connection,
        "check_dns_resolvers": check_dns_resolvers,
        "ping_target": ping_target,
        "check_dns_root_servers": check_dns_root_servers,
        "check_websites": check_websites,
        "check_local_network": check_local_network,
        "check_whois_servers": check_whois_servers,
        "check_nat_status": check_nat_status,
        "run_speed_test": run_speed_test
    }

    # Add pentest tools if available
    if PENTEST_TOOLS_AVAILABLE:
        # Create wrapper functions that provide better descriptions for the chatbot
        def nmap_scan_wrapper(target: str, scan_type: str = "basic", ports: str = None, **kwargs):
            """Run nmap scan with specified parameters. Requires target IP/hostname."""
            return run_nmap_scan(target=target, scan_type=scan_type, ports=ports, **kwargs)
        
        def quick_port_scan_wrapper(target: str, ports: str = "80,443,22,21,25,53,110,143,993,995", **kwargs):
            """Quick port scan for common services. Requires target IP/hostname."""
            return quick_port_scan(target=target, ports=ports, **kwargs)
        
        def network_discovery_wrapper(network: str, **kwargs):
            """Discover live hosts on a network. Requires network in CIDR notation (e.g., 192.168.1.0/24)."""
            return network_discovery(network=network, **kwargs)
        
        def service_version_scan_wrapper(target: str, ports: str = None, **kwargs):
            """Scan for service versions on open ports. Requires target IP/hostname."""
            return service_version_scan(target=target, ports=ports, **kwargs)
        
        def os_detection_scan_wrapper(target: str, **kwargs):
            """Attempt to detect target operating system. Requires target IP/hostname."""
            return os_detection_scan(target=target, **kwargs)
        
        def comprehensive_scan_wrapper(target: str, **kwargs):
            """Comprehensive scan with service detection and OS fingerprinting. Requires target IP/hostname."""
            return comprehensive_scan(target=target, **kwargs)
        
        tools.update({
            "nmap_scan": nmap_scan_wrapper,
            "quick_port_scan": quick_port_scan_wrapper,
            "network_discovery": network_discovery_wrapper,
            "service_version_scan": service_version_scan_wrapper,
            "os_detection_scan": os_detection_scan_wrapper,
            "comprehensive_scan": comprehensive_scan_wrapper
        })

    # Add v3 layer2 diagnostic tools if available
    if LAYER2_TOOLS_AVAILABLE:
        tools.update({
            "check_interface_status": check_interface_status,
            "get_system_info_v3": get_system_info_v3,
            "get_gateway_info": get_gateway_info
        })

    # Add more original tools if available - example of how to add more
    if ORIGINAL_TOOLS_AVAILABLE:
        try:
            # Example of potentially importing additional tools from original codebase
            # Only if we need more tools and they exist in the original codebase
            pass
        except Exception as e:
            print(f"{Fore.YELLOW}Error adding additional tools: {e}{Style.RESET_ALL}")

    return tools


def execute_tool(tool_name: str, args: Optional[Dict[str, Any]] = None) -> Any:
    """
    Execute a specific tool with optional arguments

    Args:
        tool_name: The name of the tool to execute
        args: Optional arguments to pass to the tool

    Returns:
        The result of the tool execution
    """
    # Get available tools
    tools = get_available_tools()

    # Check if the tool exists
    if tool_name not in tools:
        raise ValueError(f"Tool '{tool_name}' not found. Available tools: {', '.join(tools.keys())}")

    # Get the tool function
    tool_func = tools[tool_name]

    # Execute with args if provided, otherwise without args
    if args:
        return tool_func(**args)
    else:
        return tool_func()


@standardize_tool_output()
def list_tool_help() -> str:
    """
    List all available tools with their descriptions

    Returns:
        Formatted string with tool information
    """
    tools = get_available_tools()

    output = ["Available Network Diagnostic Tools:", "=================================="]

    for name, func in tools.items():
        desc = func.__doc__.split('\n')[0].strip() if func.__doc__ else "No description available"
        output.append(f"{name}: {desc}")

    return "\n".join(output)


# Additional helper functions for working with tools

def get_module_tools():
    """
    Get properly defined tool metadata for the network diagnostics module.
    This ensures the chatbot understands the correct function signatures.
    """
    from core.tools_registry import ToolMetadata, ParameterInfo, ParameterType, ToolCategory
    
    return {
        "check_nat_status": ToolMetadata(
            name="check_nat_status",
            function_name="check_nat_status", 
            module_path="network_diagnostics",
            description="Check if we are running behind NAT by comparing local and external IP addresses",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={},  # This function takes NO parameters
            examples=["check_nat_status"]
        ),
        "get_local_ip": ToolMetadata(
            name="get_local_ip",
            function_name="get_local_ip",
            module_path="network_diagnostics", 
            description="Get the local IP address of this machine",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={},  # This function takes NO parameters
            examples=["get_local_ip"]
        ),
        "get_external_ip": ToolMetadata(
            name="get_external_ip",
            function_name="get_external_ip",
            module_path="network_diagnostics",
            description="Get the external/public IP address",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={},  # This function takes NO parameters
            examples=["get_external_ip"]
        ),
        "ping_target": ToolMetadata(
            name="ping_target", 
            function_name="ping_target",
            module_path="network_diagnostics",
            description="Ping a target host and measure response time",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "target": ParameterInfo(ParameterType.STRING, required=False, 
                                      description="Target host to ping (default: 8.8.8.8)"),
                "count": ParameterInfo(ParameterType.INTEGER, required=False, default=4,
                                     description="Number of ping packets to send")
            },
            examples=["ping_target", "ping_target google.com", "ping_target 192.168.1.1 count=3"]
        ),
        "get_os_info": ToolMetadata(
            name="get_os_info",
            function_name="get_os_info",
            module_path="network_diagnostics",
            description="Get information about the local operating system and environment (this machine)",
            category=ToolCategory.SYSTEM_INFO,
            parameters={},  # This function takes NO parameters
            examples=["get_os_info"]
        ),
        "check_internet_connection": ToolMetadata(
            name="check_internet_connection",
            function_name="check_internet_connection",
            module_path="network_diagnostics",
            description="Check if the internet is reachable from this machine",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={},  # This function takes NO parameters
            examples=["check_internet_connection"]
        ),
        "check_dns_resolvers": ToolMetadata(
            name="check_dns_resolvers",
            function_name="check_dns_resolvers",
            module_path="network_diagnostics",
            description="Check if DNS resolvers are working properly",
            category=ToolCategory.DNS,
            parameters={},
            examples=["check_dns_resolvers"]
        ),
        "check_websites": ToolMetadata(
            name="check_websites",
            function_name="check_websites",
            module_path="network_diagnostics",
            description="Check if major websites are reachable",
            category=ToolCategory.WEB,
            parameters={},
            examples=["check_websites"]
        ),
        "check_dns_root_servers": ToolMetadata(
            name="check_dns_root_servers",
            function_name="check_dns_root_servers",
            module_path="network_diagnostics",
            description="Check if DNS root servers are reachable",
            category=ToolCategory.DNS,
            parameters={},
            examples=["check_dns_root_servers"]
        ),
        "check_local_network": ToolMetadata(
            name="check_local_network",
            function_name="check_local_network",
            module_path="network_diagnostics",
            description="Check local network interfaces and link status",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={},
            examples=["check_local_network"]
        ),
        "run_speed_test": ToolMetadata(
            name="run_speed_test",
            function_name="run_speed_test",
            module_path="network_diagnostics",
            description="Run a network speed test (macOS only)",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={},
            examples=["run_speed_test"]
        ),
        "check_whois_servers": ToolMetadata(
            name="check_whois_servers",
            function_name="check_whois_servers",
            module_path="network_diagnostics",
            description="Check if WHOIS servers are reachable",
            category=ToolCategory.WEB,
            parameters={},
            examples=["check_whois_servers"]
        ),
        "get_default_gateway": ToolMetadata(
            name="get_default_gateway",
            function_name="get_default_gateway",
            module_path="network_diagnostics",
            description="Get the default gateway IP address and interface information",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={},
            examples=["get_default_gateway"]
        ),
        "get_interface_config": ToolMetadata(
            name="get_interface_config",
            function_name="get_interface_config",
            module_path="network_diagnostics",
            description="Get network interface configuration including DHCP vs static detection",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={},
            examples=["get_interface_config"]
        ),
        "get_network_routes": ToolMetadata(
            name="get_network_routes",
            function_name="get_network_routes",
            module_path="network_diagnostics",
            description="Get complete routing table information",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={},
            examples=["get_network_routes"]
        ),
        "get_dns_config": ToolMetadata(
            name="get_dns_config",
            function_name="get_dns_config",
            module_path="network_diagnostics",
            description="Get the actual DNS servers configured on this system",
            category=ToolCategory.DNS,
            parameters={},
            examples=["get_dns_config"]
        ),
        "get_network_config": ToolMetadata(
            name="get_network_config",
            function_name="get_network_config",
            module_path="network_diagnostics",
            description="Get network configuration including IP addresses, netmasks, and subnet information",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={},
            examples=["get_network_config"]
        ),
        "get_external_ip_netmask": ToolMetadata(
            name="get_external_ip_netmask",
            function_name="get_external_ip_netmask",
            module_path="network_diagnostics",
            description="Get the netmask/network range of an external IP address using WHOIS data",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "ip": ParameterInfo(ParameterType.STRING, required=False,
                                  description="External IP address to lookup (uses current external IP if not provided)")
            },
            examples=["get_external_ip_netmask", "get_external_ip_netmask 8.8.8.8"]
        ),
        "get_interface_mac_address": ToolMetadata(
            name="get_interface_mac_address",
            function_name="get_interface_mac_address",
            module_path="network_diagnostics",
            description="Get MAC address of a specific interface or all interfaces",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "interface": ParameterInfo(ParameterType.STRING, required=False,
                                         description="Interface name (e.g., 'eth0', 'en0', 'WiFi'). If None, lists all interfaces with MAC addresses.")
            },
            examples=["get_interface_mac_address", "get_interface_mac_address eth0", "get_interface_mac_address en0"]
        ),
        "check_interface_status": ToolMetadata(
            name="check_interface_status",
            function_name="check_interface_status",
            module_path="network_diagnostics",
            description="Check network interface status and configuration for all interfaces or a specific one. Shows which interfaces are up/down with IP addresses and MAC addresses.",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "interface": ParameterInfo(ParameterType.STRING, required=False,
                                         description="Specific interface to check (if None, checks all interfaces)"),
                "silent": ParameterInfo(ParameterType.BOOLEAN, required=False, default=False,
                                      description="If True, suppress output except errors")
            },
            aliases=["list_interfaces", "show_interfaces", "interface_status"],
            examples=["check_interface_status", "check_interface_status en0", "check_interface_status interface=eth0"]
        ),
        "get_system_info_v3": ToolMetadata(
            name="get_system_info_v3",
            function_name="get_system_info_v3",
            module_path="network_diagnostics",
            description="Get comprehensive system information including hostname, OS, architecture, and user details",
            category=ToolCategory.SYSTEM_INFO,
            parameters={
                "silent": ParameterInfo(ParameterType.BOOLEAN, required=False, default=False,
                                      description="If True, suppress output except errors")
            },
            examples=["get_system_info_v3"]
        ),
        "get_gateway_info": ToolMetadata(
            name="get_gateway_info",
            function_name="get_gateway_info",
            module_path="network_diagnostics",
            description="Get default gateway information including IP address and MAC address",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "silent": ParameterInfo(ParameterType.BOOLEAN, required=False, default=False,
                                      description="If True, suppress output except errors")
            },
            examples=["get_gateway_info"]
        )
    }


def get_tool_details(tool_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific tool

    Args:
        tool_name: The name of the tool

    Returns:
        Dictionary with tool details
    """
    tools = get_available_tools()

    if tool_name not in tools:
        raise ValueError(f"Tool '{tool_name}' not found")

    tool_func = tools[tool_name]

    # Get tool docstring
    doc = tool_func.__doc__ or "No documentation available"

    # Get source code if possible
    import inspect
    try:
        source = inspect.getsource(tool_func)
    except Exception:
        source = "Source code not available"

    details = {
        "name": tool_name,
        "description": doc,
        "source": source,
        "signature": str(inspect.signature(tool_func)),
        "is_original": False  # Default to False
    }

    # Try to determine if this is an original tool
    if ORIGINAL_TOOLS_AVAILABLE:
        module = inspect.getmodule(tool_func)
        if module and parent_dir in str(module):
            details["is_original"] = True

    return details
