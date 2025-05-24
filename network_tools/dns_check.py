"""
DNS Root Servers Check module for Instability v2

This module checks the reachability of DNS Root Servers, which are crucial
to the functioning of the internet. DNS Root Servers are responsible for
providing the IP addresses of top-level domain (TLD) servers, which in turn
provide the IP addresses of individual domain names.
"""

import dns.resolver
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from colorama import Fore, Style

# List of DNS root servers with their IP addresses
DNS_ROOT_SERVERS = {
    "A": "198.41.0.4",
    "B": "199.9.14.201",
    "C": "192.33.4.12",
    "D": "199.7.91.13",
    "E": "192.203.230.10",
    "F": "192.5.5.241",
    "G": "192.112.36.4",
    "H": "198.97.190.53",
    "I": "192.36.148.17",
    "J": "192.58.128.30",
    "K": "193.0.14.129",
    "L": "199.7.83.42",
    "M": "202.12.27.33"
}


def check_dns_server(name: str, ip: str, query_name: str = "example.com") -> Tuple[bool, Optional[str]]:
    """Check if a specific DNS root server is reachable.
    
    Args:
        name: The name of the root server (e.g., "A", "B", etc.)
        ip: The IP address of the root server
        query_name: The domain name to query (default: example.com)
        
    Returns:
        Tuple containing:
            - Boolean indicating if server is reachable
            - Error message (None if reachable)
    """
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        resolver.nameservers = [ip]
        query_response = resolver.resolve(query_name, "A")

        print(f"{Fore.GREEN} - Successfully queried the '{name}' root server at {ip} for '{query_name}'{Style.RESET_ALL}")
        return True, None

    except Exception as e:
        print(f"{Fore.RED} - Failed to query {name} root server at {ip}: {e}{Style.RESET_ALL}")
        return False, str(e)


def check_dns_root_servers(servers: Optional[Dict[str, str]] = None, retry_failed: bool = True) -> Tuple[List[str], List[str]]:
    """Check if DNS root servers are reachable.
    
    Args:
        servers: Optional dictionary of DNS root servers to check (name -> IP)
                If None, uses the default DNS_ROOT_SERVERS
        retry_failed: Whether to retry unreachable servers after a delay
        
    Returns:
        Tuple containing:
            - List of reachable server descriptions
            - List of unreachable server descriptions
    """
    if servers is None:
        servers = DNS_ROOT_SERVERS

    reachable_servers = []
    unreachable_servers = []

    # First round of checks
    for name, ip in servers.items():
        is_reachable, error = check_dns_server(name, ip)
        if not is_reachable:
            unreachable_servers.append(f"- {name} ({ip}) - Error: {error}")
        else:
            reachable_servers.append(f"- {name} ({ip})")

    # Retry unreachable servers after a delay, if desired
    if retry_failed and unreachable_servers:
        print(f"{Fore.YELLOW}Retrying unreachable servers after delay...{Style.RESET_ALL}")
        time.sleep(5)
        new_unreachable = []
        for entry in unreachable_servers:
            ip_part = entry.split('(')[1].split(')')[0]
            name_part = entry.split('- ')[1].split(' (')[0]
            is_reachable, error = check_dns_server(name_part, ip_part)
            if not is_reachable:
                new_unreachable.append(f"- {name_part} ({ip_part}) - Error: {error}")
            else:
                reachable_servers.append(f"- {name_part} ({ip_part})")
        unreachable_servers = new_unreachable

    return reachable_servers, unreachable_servers


def generate_dns_report(reachable: List[str], unreachable: List[str]) -> str:
    """Generate a formatted report of DNS root server reachability.
    
    Args:
        reachable: List of reachable server descriptions
        unreachable: List of unreachable server descriptions
        
    Returns:
        str: Formatted report
    """
    report = ("This script checks the reachability of DNS Root Servers, which are crucial to the functioning of the "
              "internet. DNS Root Servers are responsible for providing the IP addresses of top-level domain (TLD) "
              "servers, which in turn provide the IP addresses of individual domain names. If DNS Root Servers are "
              "unreachable, it can cause widespread internet outages and disruptions.\n\n")

    if reachable:
        report += "Reachable DNS Root Servers:\n"
        for server in reachable:
            report += server + "\n"

    if unreachable:
        report += "\nUnreachable DNS Root Servers:\n"
        for server in unreachable:
            report += server + "\n"

    if not unreachable:
        report += "\nDNS Root Servers reachability summary: All DNS Root Servers are reachable.\n"
    else:
        report += "\nDNS Root Servers reachability summary: Some DNS Root Servers are unreachable.\n"

    return report


def main(silent: bool = False, polite: bool = False) -> str:
    """Main function to run the DNS root servers check.
    
    Args:
        silent: If True, suppress detailed console output
        polite: If True, use more verbose/polite messaging (not currently used)
        
    Returns:
        str: Report of the DNS root servers check
    """
    print(f"Starting DNS Root Servers check at {datetime.now()}\n")
    
    reachable, unreachable = check_dns_root_servers(DNS_ROOT_SERVERS)
    report = generate_dns_report(reachable, unreachable)
    
    # Only print detailed output if not in silent mode
    if not silent:
        print(f"\n{report}")
    
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check DNS root servers reachability")
    parser.add_argument("--silent", action="store_true", help="Suppress detailed output")
    parser.add_argument("--polite", action="store_true", help="Use more verbose/polite messaging")
    
    args = parser.parse_args()
    main(silent=args.silent, polite=args.polite)