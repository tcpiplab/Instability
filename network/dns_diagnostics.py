"""
DNS Diagnostics Module

Comprehensive DNS testing including resolution, server testing, and reverse lookups.
Part of the instability.py v3 network diagnostics suite.
"""

import socket
import subprocess
import platform
from typing import Dict, Any, List, Optional
from colorama import Fore

def resolve_hostname(hostname: str, record_type: str = "A", silent: bool = False) -> Dict[str, Any]:
    """
    Resolve hostname to IP addresses using specified DNS record type.
    
    Args:
        hostname: Target hostname to resolve
        record_type: DNS record type (A, AAAA, MX, NS, TXT, CNAME)
        silent: Suppress console output if True
        
    Returns:
        Dict containing resolution results, IPs, and error information
    """
    if not silent:
        print(f"{Fore.CYAN}Resolving {hostname} ({record_type} record)...{Fore.RESET}")
    
    result = {
        "success": False,
        "hostname": hostname,
        "record_type": record_type,
        "resolved_ips": [],
        "resolution_time_ms": None,
        "error": None
    }
    
    try:
        import time
        start_time = time.time()
        
        if record_type.upper() == "A":
            ip_addresses = socket.gethostbyname_ex(hostname)[2]
            result["resolved_ips"] = ip_addresses
        elif record_type.upper() == "AAAA":
            try:
                ip_addresses = socket.getaddrinfo(hostname, None, socket.AF_INET6)
                result["resolved_ips"] = [addr[4][0] for addr in ip_addresses]
            except socket.gaierror:
                result["resolved_ips"] = []
        else:
            # For other record types, try using nslookup/dig
            cmd = _get_dns_lookup_command(hostname, record_type)
            if cmd:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if proc.returncode == 0:
                    result["resolved_ips"] = _parse_dns_output(proc.stdout, record_type)
                else:
                    result["error"] = f"DNS lookup failed: {proc.stderr.strip()}"
        
        end_time = time.time()
        result["resolution_time_ms"] = round((end_time - start_time) * 1000, 2)
        
        if result["resolved_ips"]:
            result["success"] = True
            if not silent:
                print(f"{Fore.GREEN}✓ Resolved to: {', '.join(result['resolved_ips'])}{Fore.RESET}")
        else:
            result["error"] = "No records found"
            if not silent:
                print(f"{Fore.RED}✗ No {record_type} records found{Fore.RESET}")
                
    except socket.gaierror as e:
        result["error"] = f"DNS resolution failed: {str(e)}"
        if not silent:
            print(f"{Fore.RED}✗ DNS resolution failed: {e}{Fore.RESET}")
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        if not silent:
            print(f"{Fore.RED}✗ Error: {e}{Fore.RESET}")
    
    return result

def test_dns_servers(servers: List[str] = None, test_domain: str = "google.com", silent: bool = False) -> Dict[str, Any]:
    """
    Test connectivity and response time to DNS servers.
    
    Args:
        servers: List of DNS server IPs to test (defaults to common public DNS)
        test_domain: Domain to use for testing resolution
        silent: Suppress console output if True
        
    Returns:
        Dict containing test results for each DNS server
    """
    if servers is None:
        servers = ["8.8.8.8", "1.1.1.1", "208.67.222.222", "9.9.9.9"]
    
    if not silent:
        print(f"{Fore.CYAN}Testing DNS servers with domain: {test_domain}...{Fore.RESET}")
    
    result = {
        "success": False,
        "test_domain": test_domain,
        "servers_tested": len(servers),
        "working_servers": 0,
        "server_results": {},
        "fastest_server": None,
        "fastest_time_ms": None
    }
    
    fastest_time = float('inf')
    
    for server in servers:
        server_result = {
            "reachable": False,
            "resolution_time_ms": None,
            "resolved_ip": None,
            "error": None
        }
        
        try:
            # Test DNS resolution using specific server
            cmd = _get_dns_server_test_command(test_domain, server)
            if cmd:
                import time
                start_time = time.time()
                
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                end_time = time.time()
                response_time = round((end_time - start_time) * 1000, 2)
                
                if proc.returncode == 0:
                    server_result["reachable"] = True
                    server_result["resolution_time_ms"] = response_time
                    server_result["resolved_ip"] = _extract_ip_from_output(proc.stdout)
                    result["working_servers"] += 1
                    
                    if response_time < fastest_time:
                        fastest_time = response_time
                        result["fastest_server"] = server
                        result["fastest_time_ms"] = response_time
                    
                    if not silent:
                        print(f"{Fore.GREEN}✓ {server}: {response_time}ms{Fore.RESET}")
                else:
                    server_result["error"] = "DNS query failed"
                    if not silent:
                        print(f"{Fore.RED}✗ {server}: Failed{Fore.RESET}")
            else:
                server_result["error"] = "No DNS tool available"
                if not silent:
                    print(f"{Fore.YELLOW}? {server}: No DNS tool available{Fore.RESET}")
                    
        except subprocess.TimeoutExpired:
            server_result["error"] = "Timeout"
            if not silent:
                print(f"{Fore.RED}✗ {server}: Timeout{Fore.RESET}")
        except Exception as e:
            server_result["error"] = str(e)
            if not silent:
                print(f"{Fore.RED}✗ {server}: {e}{Fore.RESET}")
        
        result["server_results"][server] = server_result
    
    result["success"] = result["working_servers"] > 0
    
    if not silent and result["fastest_server"]:
        print(f"{Fore.GREEN}Fastest DNS server: {result['fastest_server']} ({result['fastest_time_ms']}ms){Fore.RESET}")
    
    return result

def reverse_dns_lookup(ip_address: str, silent: bool = False) -> Dict[str, Any]:
    """
    Perform reverse DNS lookup to get hostname from IP address.
    
    Args:
        ip_address: IP address to perform reverse lookup on
        silent: Suppress console output if True
        
    Returns:
        Dict containing reverse lookup results
    """
    if not silent:
        print(f"{Fore.CYAN}Reverse DNS lookup for {ip_address}...{Fore.RESET}")
    
    result = {
        "success": False,
        "ip_address": ip_address,
        "hostname": None,
        "lookup_time_ms": None,
        "error": None
    }
    
    try:
        import time
        start_time = time.time()
        
        hostname = socket.gethostbyaddr(ip_address)[0]
        
        end_time = time.time()
        result["lookup_time_ms"] = round((end_time - start_time) * 1000, 2)
        result["hostname"] = hostname
        result["success"] = True
        
        if not silent:
            print(f"{Fore.GREEN}✓ Resolved to: {hostname}{Fore.RESET}")
            
    except socket.herror as e:
        result["error"] = f"Reverse DNS lookup failed: {str(e)}"
        if not silent:
            print(f"{Fore.RED}✗ Reverse DNS lookup failed: {e}{Fore.RESET}")
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        if not silent:
            print(f"{Fore.RED}✗ Error: {e}{Fore.RESET}")
    
    return result

def check_dns_propagation(domain: str, record_type: str = "A", servers: List[str] = None, silent: bool = False) -> Dict[str, Any]:
    """
    Check DNS propagation across multiple DNS servers.
    
    Args:
        domain: Domain to check propagation for
        record_type: DNS record type to check
        servers: List of DNS servers to check (defaults to major public DNS)
        silent: Suppress console output if True
        
    Returns:
        Dict containing propagation status across servers
    """
    if servers is None:
        servers = ["8.8.8.8", "1.1.1.1", "208.67.222.222", "9.9.9.9", "8.8.4.4"]
    
    if not silent:
        print(f"{Fore.CYAN}Checking DNS propagation for {domain} ({record_type})...{Fore.RESET}")
    
    result = {
        "success": False,
        "domain": domain,
        "record_type": record_type,
        "servers_checked": len(servers),
        "consistent_responses": 0,
        "unique_responses": {},
        "propagation_complete": False,
        "server_responses": {}
    }
    
    responses = {}
    
    for server in servers:
        try:
            cmd = _get_dns_server_test_command(domain, server, record_type)
            if cmd:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if proc.returncode == 0:
                    response = _extract_ip_from_output(proc.stdout)
                    if response:
                        if response not in responses:
                            responses[response] = []
                        responses[response].append(server)
                        result["server_responses"][server] = {"success": True, "response": response}
                        if not silent:
                            print(f"{Fore.GREEN}✓ {server}: {response}{Fore.RESET}")
                    else:
                        result["server_responses"][server] = {"success": False, "error": "No response"}
                        if not silent:
                            print(f"{Fore.RED}✗ {server}: No response{Fore.RESET}")
                else:
                    result["server_responses"][server] = {"success": False, "error": "Query failed"}
                    if not silent:
                        print(f"{Fore.RED}✗ {server}: Query failed{Fore.RESET}")
            else:
                result["server_responses"][server] = {"success": False, "error": "No DNS tool"}
                if not silent:
                    print(f"{Fore.YELLOW}? {server}: No DNS tool{Fore.RESET}")
        except Exception as e:
            result["server_responses"][server] = {"success": False, "error": str(e)}
            if not silent:
                print(f"{Fore.RED}✗ {server}: {e}{Fore.RESET}")
    
    result["unique_responses"] = responses
    result["success"] = len(responses) > 0
    
    # Check if propagation is complete (all servers return same response)
    if len(responses) == 1:
        result["propagation_complete"] = True
        result["consistent_responses"] = sum(len(servers) for servers in responses.values())
        if not silent:
            print(f"{Fore.GREEN}✓ DNS propagation complete - all servers consistent{Fore.RESET}")
    elif len(responses) > 1:
        if not silent:
            print(f"{Fore.YELLOW}⚠ DNS propagation incomplete - {len(responses)} different responses{Fore.RESET}")
    
    return result

def _get_dns_lookup_command(hostname: str, record_type: str) -> Optional[List[str]]:
    """Get appropriate DNS lookup command for the platform."""
    system = platform.system().lower()
    
    if system == "windows":
        return ["nslookup", "-type=" + record_type.lower(), hostname]
    else:
        # Try dig first, fallback to nslookup
        try:
            subprocess.run(["which", "dig"], capture_output=True, check=True)
            return ["dig", "+short", hostname, record_type.upper()]
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ["nslookup", "-type=" + record_type.lower(), hostname]

def _get_dns_server_test_command(domain: str, server: str, record_type: str = "A") -> Optional[List[str]]:
    """Get DNS server test command for the platform."""
    system = platform.system().lower()
    
    if system == "windows":
        return ["nslookup", domain, server]
    else:
        try:
            subprocess.run(["which", "dig"], capture_output=True, check=True)
            return ["dig", f"@{server}", "+short", domain, record_type.upper()]
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ["nslookup", domain, server]

def _parse_dns_output(output: str, record_type: str) -> List[str]:
    """Parse DNS command output to extract relevant records."""
    lines = output.strip().split('\n')
    results = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Basic IP address extraction for A records
        if record_type.upper() == "A":
            import re
            ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            matches = re.findall(ip_pattern, line)
            results.extend(matches)
        else:
            # For other record types, include the whole line
            if line and not line.startswith(';'):
                results.append(line)
    
    return list(set(results))  # Remove duplicates

def _extract_ip_from_output(output: str) -> Optional[str]:
    """Extract first IP address from DNS command output."""
    import re
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    matches = re.findall(ip_pattern, output)
    return matches[0] if matches else None