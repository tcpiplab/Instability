"""
Layer 3 network diagnostics for Instability v3.

Provides external IP detection, routing information, connectivity testing,
and basic network performance metrics.
"""

import socket
import subprocess
import platform
import time
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from requests.exceptions import RequestException

# Import colorama for terminal colors
from colorama import Fore, Style

# Import centralized error handling
from core.error_handling import (
    create_error_response, ErrorType, ErrorCode, get_timeout, ErrorRecovery,
    create_network_error, create_system_error, create_input_error
)

# Import configuration
from config import PING_TIMEOUT, TRACEROUTE_TIMEOUT


def get_external_ip(timeout: int = 10, silent: bool = False) -> Dict[str, Any]:
    """
    Get the external IP address using multiple methods.
    
    Args:
        timeout: Timeout in seconds for the request
        silent: If True, suppress output except errors
        
    Returns:
        Standardized result dictionary
    """
    start_time = datetime.now()
    
    # Try multiple services for reliability
    ip_services = [
        "https://ipinfo.io/ip",
        "https://api.ipify.org",
        "https://icanhazip.com",
        "https://ident.me",
        "https://checkip.amazonaws.com"
    ]
    
    try:
        import requests
        
        for service in ip_services:
            try:
                response = requests.get(service, timeout=timeout)
                if response.status_code == 200:
                    external_ip = response.text.strip()
                    
                    # Validate IP format
                    if is_valid_ip(external_ip):
                        execution_time = (datetime.now() - start_time).total_seconds()
                        
                        if not silent:
                            print(f"External IP: {external_ip}")
                        
                        return {
                            "success": True,
                            "exit_code": 0,
                            "execution_time": execution_time,
                            "timestamp": start_time.isoformat(),
                            "tool_name": "get_external_ip",
                            "command_executed": f"get_external_ip(timeout={timeout})",
                            "stdout": external_ip,
                            "stderr": "",
                            "parsed_data": {
                                "external_ip": external_ip,
                                "service_used": service
                            },
                            "error_type": None,
                            "error_message": None,
                            "target": None,
                            "options_used": {"timeout": timeout}
                        }
            except RequestException as error_trying_to_get_external_ip:
                # RequestException is the base class for all requests-specific exceptions
                print(f"{Fore.RED}Error: Failed to get external IP from {service}: {error_trying_to_get_external_ip}{Style.RESET_ALL}")
                print(f"Retrying with next service...")
                continue
        
        # If all services failed
        print(f"{Fore.RED}Error: All external IP detection services failed.{Style.RESET_ALL}")
        execution_time = (datetime.now() - start_time).total_seconds()
        print(f"This might mean that our local network has no connectivity to the internet.")

        return create_network_error(
            ErrorCode.UNREACHABLE,
            tool_name="get_external_ip",
            execution_time=execution_time,
            details={
                "command": f"get_external_ip(timeout={timeout})",
                "options": {"timeout": timeout}
            },
            error_type=ErrorType.NETWORK,
            error_message="All external IP detection services failed"
        )
    
    except ImportError:
        execution_time = (datetime.now() - start_time).total_seconds()
        if not silent:
            print(f"{Fore.RED}Error: requests library not available for external IP detection{Style.RESET_ALL}")
        
        return create_system_error(
            ErrorCode.TOOL_MISSING,
            tool_name="get_external_ip",
            execution_time=execution_time,
            details={
                "command": f"get_external_ip(timeout={timeout})",
                "options": {"timeout": timeout}
            },
            tool="requests library"
        )
    
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Determine specific error type
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            error_code = ErrorCode.TIMEOUT
        elif "connection" in error_msg.lower():
            error_code = ErrorCode.CONNECTION_FAILED
        else:
            error_code = ErrorCode.UNREACHABLE
        
        if not silent:
            print(f"{Fore.RED}Error: Failed to get external IP: {e}{Style.RESET_ALL}")
        
        return create_network_error(
            error_code,
            tool_name="get_external_ip",
            execution_time=execution_time,
            details={
                "command": f"get_external_ip(timeout={timeout})",
                "stderr": str(e),
                "options": {"timeout": timeout}
            },
            timeout=timeout
        )


def ping_host(target: str, count: int = 4, timeout: int = 5, silent: bool = False) -> Dict[str, Any]:
    """
    Ping a host to test connectivity and measure latency.
    
    Args:
        target: Host to ping (IP or hostname)
        count: Number of ping packets to send
        timeout: Timeout in seconds per ping
        silent: If True, suppress output except errors
        
    Returns:
        Standardized result dictionary
    """
    start_time = datetime.now()
    
    try:
        # Build ping command based on platform
        system = platform.system()
        if system == "Windows":
            cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), target]
        else:
            cmd = ["ping", "-c", str(count), "-W", str(timeout), target]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout * count + 10
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Parse ping results
        parsed_data = parse_ping_output(result.stdout, system)
        
        success = result.returncode == 0 and parsed_data["packets_received"] > 0
        
        if not silent:
            if success:
                print(f"Ping to {target}: {parsed_data['packets_received']}/{parsed_data['packets_sent']} packets, avg {parsed_data['avg_time']:.1f}ms")
            else:
                print(f"Ping to {target}: Failed")
        
        return {
            "success": success,
            "exit_code": result.returncode,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "ping_host",
            "command_executed": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "parsed_data": parsed_data,
            "error_type": None if success else "network",
            "error_message": None if success else f"Ping failed: {parsed_data.get('error', 'Unknown error')}",
            "target": target,
            "options_used": {"count": count, "timeout": timeout}
        }
    
    except subprocess.TimeoutExpired:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Ping timed out after {timeout * count + 10} seconds"
        
        if not silent:
            print(f"Error: {error_msg}")
        
        return {
            "success": False,
            "exit_code": 124,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "ping_host",
            "command_executed": f"ping {target}",
            "stdout": "",
            "stderr": error_msg,
            "parsed_data": {"packets_sent": count, "packets_received": 0},
            "error_type": "timeout",
            "error_message": error_msg,
            "target": target,
            "options_used": {"count": count, "timeout": timeout}
        }
    
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Ping failed: {Fore.RED}{e}{Style.RESET_ALL}"
        
        if not silent:
            print(f"Error: {error_msg}")
        
        return {
            "success": False,
            "exit_code": 1,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "ping_host",
            "command_executed": f"ping {target}",
            "stdout": "",
            "stderr": str(e),
            "parsed_data": {},
            "error_type": "execution",
            "error_message": error_msg,
            "target": target,
            "options_used": {"count": count, "timeout": timeout}
        }


def traceroute_host(target: str, max_hops: int = 30, timeout: int = 30, silent: bool = False) -> Dict[str, Any]:
    """
    Trace the route to a host.
    
    Args:
        target: Host to trace route to (IP or hostname)
        max_hops: Maximum number of hops
        timeout: Timeout in seconds for the entire operation
        silent: If True, suppress output except errors
        
    Returns:
        Standardized result dictionary
    """
    start_time = datetime.now()
    
    try:
        # Build traceroute command based on platform
        system = platform.system()
        if system == "Windows":
            cmd = ["tracert", "-h", str(max_hops), "-w", "5000", target]
        else:
            cmd = ["traceroute", "-m", str(max_hops), "-w", "5", target]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Parse traceroute results
        parsed_data = parse_traceroute_output(result.stdout, system)
        
        success = result.returncode == 0 and len(parsed_data["hops"]) > 0
        
        if not silent:
            if success:
                print(f"Traceroute to {target}: {len(parsed_data['hops'])} hops")
                for hop in parsed_data["hops"][:5]:  # Show first 5 hops
                    print(f"  {hop['hop_number']}: {hop['ip']} ({hop['hostname']}) {hop['avg_time']:.1f}ms")
                if len(parsed_data["hops"]) > 5:
                    print(f"  ... and {len(parsed_data['hops']) - 5} more hops")
            else:
                print(f"Traceroute to {target}: Failed")
        
        return {
            "success": success,
            "exit_code": result.returncode,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "traceroute_host",
            "command_executed": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "parsed_data": parsed_data,
            "error_type": None if success else "network",
            "error_message": None if success else "Traceroute failed",
            "target": target,
            "options_used": {"max_hops": max_hops, "timeout": timeout}
        }
    
    except subprocess.TimeoutExpired:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Traceroute timed out after {timeout} seconds"
        
        if not silent:
            print(f"Error: {error_msg}")
        
        return {
            "success": False,
            "exit_code": 124,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "traceroute_host",
            "command_executed": f"traceroute {target}",
            "stdout": "",
            "stderr": error_msg,
            "parsed_data": {"hops": []},
            "error_type": "timeout",
            "error_message": error_msg,
            "target": target,
            "options_used": {"max_hops": max_hops, "timeout": timeout}
        }
    
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Traceroute failed: {Fore.RED}{e}{Style.RESET_ALL}"
        
        if not silent:
            print(f"Error: {error_msg}")
        
        return {
            "success": False,
            "exit_code": 1,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "traceroute_host",
            "command_executed": f"traceroute {target}",
            "stdout": "",
            "stderr": str(e),
            "parsed_data": {},
            "error_type": "execution",
            "error_message": error_msg,
            "target": target,
            "options_used": {"max_hops": max_hops, "timeout": timeout}
        }


def test_port_connectivity(target: str, port: int, timeout: int = 5, silent: bool = False) -> Dict[str, Any]:
    """
    Test connectivity to a specific port on a host.
    
    Args:
        target: Host to test (IP or hostname)
        port: Port number to test
        timeout: Timeout in seconds for connection attempt
        silent: If True, suppress output except errors
        
    Returns:
        Standardized result dictionary
    """
    start_time = datetime.now()
    
    try:
        # Test TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        connection_start = time.time()
        result = sock.connect_ex((target, port))
        connection_time = (time.time() - connection_start) * 1000  # Convert to milliseconds
        
        sock.close()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        success = result == 0
        status = "open" if success else "closed/filtered"
        
        if not silent:
            if success:
                print(f"Port {port}/tcp on {target}: open ({connection_time:.1f}ms)")
            else:
                print(f"Port {port}/tcp on {target}: closed/filtered")
        
        return {
            "success": success,
            "exit_code": 0 if success else 1,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "test_port_connectivity",
            "command_executed": f"test_port_connectivity({target}, {port})",
            "stdout": f"Port {port}/tcp: {status}",
            "stderr": "",
            "parsed_data": {
                "host": target,
                "port": port,
                "protocol": "tcp",
                "status": status,
                "connection_time_ms": connection_time if success else None
            },
            "error_type": None,
            "error_message": None,
            "target": f"{target}:{port}",
            "options_used": {"port": port, "timeout": timeout}
        }
    
    except socket.gaierror as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"DNS resolution failed for {target}: {Fore.RED}{e}{Style.RESET_ALL}"
        
        if not silent:
            print(f"Error: {error_msg}")
        
        return {
            "success": False,
            "exit_code": 2,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "test_port_connectivity",
            "command_executed": f"test_port_connectivity({target}, {port})",
            "stdout": "",
            "stderr": error_msg,
            "parsed_data": {"host": target, "port": port},
            "error_type": "invalid_target",
            "error_message": error_msg,
            "target": f"{target}:{port}",
            "options_used": {"port": port, "timeout": timeout}
        }
    
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Port connectivity test failed: {Fore.RED}{e}{Style.RESET_ALL}"
        
        if not silent:
            print(f"Error: {error_msg}")
        
        return {
            "success": False,
            "exit_code": 1,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "test_port_connectivity",
            "command_executed": f"test_port_connectivity({target}, {port})",
            "stdout": "",
            "stderr": str(e),
            "parsed_data": {},
            "error_type": "execution",
            "error_message": error_msg,
            "target": f"{target}:{port}",
            "options_used": {"port": port, "timeout": timeout}
        }


def scan_local_network(network: str = None, timeout: int = 10, silent: bool = False) -> Dict[str, Any]:
    """
    Perform a basic ping sweep of the local network.
    
    Args:
        network: Network to scan (e.g., "192.168.1.0/24"), auto-detected if None
        timeout: Timeout per ping in seconds
        silent: If True, suppress output except errors
        
    Returns:
        Standardized result dictionary
    """
    start_time = datetime.now()
    
    try:
        if not network:
            # Auto-detect local network
            network = detect_local_network()
        
        if not silent:
            print(f"Scanning network {network}...")
        
        # Parse network (simplified - assumes /24)
        if "/" not in network:
            network += "/24"
        
        base_ip = network.split("/")[0].rsplit(".", 1)[0]
        
        active_hosts = []
        
        # Ping common addresses (simplified scan)
        test_ips = [f"{base_ip}.{i}" for i in [1, 10, 20, 50, 100, 150, 200, 254]]
        
        for ip in test_ips:
            try:
                # Quick ping test
                ping_result = ping_host(ip, count=1, timeout=2, silent=True)
                if ping_result["success"]:
                    active_hosts.append({
                        "ip": ip,
                        "hostname": get_hostname_for_ip(ip),
                        "response_time": ping_result["parsed_data"].get("avg_time", 0)
                    })
            except Exception:
                continue
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if not silent:
            print(f"Network scan complete: {len(active_hosts)} hosts found")
            for host in active_hosts:
                hostname_str = f" ({host['hostname']})" if host['hostname'] else ""
                print(f"  • {host['ip']}{hostname_str}")
        
        return {
            "success": True,
            "exit_code": 0,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "scan_local_network",
            "command_executed": f"scan_local_network(network={network})",
            "stdout": f"Found {len(active_hosts)} active hosts",
            "stderr": "",
            "parsed_data": {
                "network": network,
                "hosts_found": len(active_hosts),
                "active_hosts": active_hosts
            },
            "error_type": None,
            "error_message": None,
            "target": network,
            "options_used": {"network": network, "timeout": timeout}
        }
    
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Network scan failed: {Fore.RED}{e}{Style.RESET_ALL}"
        
        if not silent:
            print(f"Error: {error_msg}")
        
        return {
            "success": False,
            "exit_code": 1,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "scan_local_network",
            "command_executed": f"scan_local_network(network={network})",
            "stdout": "",
            "stderr": str(e),
            "parsed_data": {},
            "error_type": "execution",
            "error_message": error_msg,
            "target": network,
            "options_used": {"network": network, "timeout": timeout}
        }


# Helper functions

def is_valid_ip(ip: str) -> bool:
    """Validate IP address format."""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def parse_ping_output(output: str, system: str) -> Dict[str, Any]:
    """Parse ping command output."""
    parsed = {
        "packets_sent": 0,
        "packets_received": 0,
        "packet_loss": 100.0,
        "min_time": 0.0,
        "avg_time": 0.0,
        "max_time": 0.0
    }
    
    try:
        if system == "Windows":
            # Parse Windows ping output
            sent_match = re.search(r'Packets: Sent = (\d+)', output)
            received_match = re.search(r'Received = (\d+)', output)
            loss_match = re.search(r'Lost = \d+ \((\d+)% loss\)', output)
            
            if sent_match:
                parsed["packets_sent"] = int(sent_match.group(1))
            if received_match:
                parsed["packets_received"] = int(received_match.group(1))
            if loss_match:
                parsed["packet_loss"] = float(loss_match.group(1))
            
            # Extract timing information
            time_matches = re.findall(r'time[<=](\d+)ms', output)
            if time_matches:
                times = [float(t) for t in time_matches]
                parsed["min_time"] = min(times)
                parsed["avg_time"] = sum(times) / len(times)
                parsed["max_time"] = max(times)
        else:
            # Parse Unix/Linux/macOS ping output
            stats_match = re.search(r'(\d+) packets transmitted, (\d+) received, (\d+)% packet loss', output)
            if stats_match:
                parsed["packets_sent"] = int(stats_match.group(1))
                parsed["packets_received"] = int(stats_match.group(2))
                parsed["packet_loss"] = float(stats_match.group(3))
            
            # Extract timing information
            timing_match = re.search(r'min/avg/max/stddev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms', output)
            if timing_match:
                parsed["min_time"] = float(timing_match.group(1))
                parsed["avg_time"] = float(timing_match.group(2))
                parsed["max_time"] = float(timing_match.group(3))
    
    except Exception:
        pass
    
    return parsed


def parse_traceroute_output(output: str, system: str) -> Dict[str, Any]:
    """Parse traceroute command output."""
    parsed = {"hops": []}
    
    try:
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if system == "Windows":
                # Parse Windows tracert output
                match = re.match(r'\s*(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
                if match:
                    hop_num = int(match.group(1))
                    times = [match.group(2), match.group(3), match.group(4)]
                    hostname_ip = match.group(5)
                    
                    # Extract IP from hostname_ip
                    ip_match = re.search(r'\[([\d.]+)\]', hostname_ip)
                    ip = ip_match.group(1) if ip_match else hostname_ip
                    hostname = hostname_ip.split('[')[0].strip() if '[' in hostname_ip else ip
                    
                    # Calculate average time
                    try:
                        numeric_times = [float(t.replace('ms', '')) for t in times if 'ms' in t]
                        avg_time = sum(numeric_times) / len(numeric_times) if numeric_times else 0
                    except Exception:
                        avg_time = 0
                    
                    parsed["hops"].append({
                        "hop_number": hop_num,
                        "ip": ip,
                        "hostname": hostname,
                        "avg_time": avg_time
                    })
            else:
                # Parse Unix/Linux/macOS traceroute output
                match = re.match(r'\s*(\d+)\s+(\S+)\s+\(([\d.]+)\)\s+([\d.]+)', line)
                if match:
                    hop_num = int(match.group(1))
                    hostname = match.group(2)
                    ip = match.group(3)
                    time_ms = float(match.group(4))
                    
                    parsed["hops"].append({
                        "hop_number": hop_num,
                        "ip": ip,
                        "hostname": hostname if hostname != ip else None,
                        "avg_time": time_ms
                    })
    
    except Exception:
        pass
    
    return parsed


def detect_local_network() -> str:
    """Detect the local network range."""
    try:
        # Get local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        
        # Assume /24 network
        network_base = '.'.join(local_ip.split('.')[:-1]) + '.0'
        return f"{network_base}/24"
    
    except Exception:
        return "192.168.1.0/24"  # Default fallback


def get_hostname_for_ip(ip: str) -> Optional[str]:
    """Get hostname for an IP address."""
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname if hostname != ip else None
    except Exception:
        return None


# Quick test function for development
def test_layer3_diagnostics():
    """Test function for development purposes."""
    print("Testing Layer 3 diagnostics...")
    
    # Test functions
    test_functions = [
        ("get_external_ip", lambda: get_external_ip(silent=False)),
        ("ping_host (google.com)", lambda: ping_host("google.com", count=3, silent=False)),
        ("ping_host (localhost)", lambda: ping_host("localhost", count=2, silent=False)),
        ("test_port_connectivity (google.com:80)", lambda: test_port_connectivity("google.com", 80, silent=False)),
        ("test_port_connectivity (localhost:22)", lambda: test_port_connectivity("localhost", 22, silent=False))
    ]
    
    for func_name, func in test_functions:
        print(f"\n--- Testing {func_name} ---")
        try:
            result = func()
            print(f"Success: {result['success']}")
            if result['parsed_data']:
                print(f"Data keys: {list(result['parsed_data'].keys())}")
        except Exception as e:
            print(f"Error: {Fore.RED}{e}{Style.RESET_ALL}")


if __name__ == "__main__":
    test_layer3_diagnostics()