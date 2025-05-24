"""
DNS Resolver Check module for Instability v2

This module checks the reachability of popular DNS resolvers and the local default
resolver. It includes functionality to test response times and reliability of DNS
resolvers, which is critical for diagnosing network connectivity issues.
"""

import dns.resolver
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from colorama import Fore, Style

# List of DNS resolvers and their IP addresses
DEFAULT_DNS_RESOLVERS = {
    "Google Public DNS - Primary": "8.8.8.8",
    "Google Public DNS - Secondary": "8.8.4.4",
    "Cloudflare DNS - Primary": "1.1.1.1",
    "Cloudflare DNS - Secondary": "1.0.0.1",
    "OpenDNS - Primary": "208.67.222.222",
    "OpenDNS - Secondary": "208.67.220.220",
    "Quad9 - Primary": "9.9.9.9",
    "Quad9 - Secondary": "149.112.112.112",
    "Comodo Secure DNS - Primary": "8.26.56.26",
    "Comodo Secure DNS - Secondary": "8.20.247.20"
}


def get_local_default_dns_resolver() -> str:
    """Get the IP address of the local default DNS resolver.
    
    Returns:
        str: The IP address of the local default DNS resolver
    """
    # Create a resolver object instance
    resolver = dns.resolver.Resolver()

    # Get the IP address of the first nameserver in the resolver configuration
    return resolver.nameservers[0]


def check_resolver(resolver_name: str, resolver_ip: str, query_domain: str = 'example.com', 
                  retry_attempts: int = 3, timeout: int = 5, lifetime: int = 10) -> Tuple[bool, Optional[float], Optional[str]]:
    """Check if a specific DNS resolver is reachable.
    
    Args:
        resolver_name: Name of the resolver (for reporting purposes)
        resolver_ip: IP address of the resolver
        query_domain: Domain to query (default: example.com)
        retry_attempts: Number of retry attempts before giving up
        timeout: Timeout in seconds for each query
        lifetime: Total lifetime in seconds for all retries
        
    Returns:
        Tuple containing:
            - Boolean indicating if resolver is reachable
            - Response time in seconds (or None if unreachable)
            - Error message (or None if reachable)
    """
    for attempt in range(retry_attempts):
        try:
            # Create a resolver instance and set the DNS server IP address
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [resolver_ip]
            resolver.timeout = timeout
            resolver.lifetime = lifetime

            start_time = datetime.now()
            # Query for 'A' record of the specified domain
            answer = resolver.resolve(query_domain, 'A')
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            # If we get an answer, consider the resolver reachable
            if answer:
                return True, response_time, None
            
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout, dns.exception.DNSException) as e:
            if attempt == retry_attempts - 1:
                return False, None, str(e)
            time.sleep(2)  # Sleep for 2 seconds before retrying
    
    # If we reach here, all attempts failed but didn't raise exceptions
    return False, None, "No valid DNS response received"


def monitor_dns_resolvers(custom_resolvers: Optional[Dict[str, str]] = None) -> str:
    """Monitor the reachability of DNS resolvers.
    
    Args:
        custom_resolvers: Optional dictionary of custom resolvers to check (name -> IP)
                        If None, uses default resolvers plus local default resolver
    
    Returns:
        str: Formatted report of resolver statuses and response times
    """
    reachable_resolvers = []
    unreachable_resolvers = []
    results = ""
    results += f"Starting DNS Resolver monitoring report at: {datetime.now()}\n"
    results += "This will check the reachability of several of the most popular DNS resolvers.\n"
    
    # Start with default resolvers
    resolvers_to_check = DEFAULT_DNS_RESOLVERS.copy()
    
    # Use custom resolvers if provided
    if custom_resolvers:
        resolvers_to_check.update(custom_resolvers)
    
    # Append the local default DNS resolver IP address to the list of resolvers
    try:
        local_default_resolver_ip = get_local_default_dns_resolver()
        resolvers_to_check["Local Default DNS Resolver"] = local_default_resolver_ip
    except Exception as e:
        results += f"Unable to determine local default DNS resolver: {e}\n"

    # Iterate through the list of DNS resolvers and check their reachability
    for resolver_name, resolver_ip in resolvers_to_check.items():
        is_reachable, response_time, error = check_resolver(resolver_name, resolver_ip)
        
        if is_reachable and response_time is not None:
            print(f"{Fore.GREEN} - Successfully queried {resolver_name} ({resolver_ip}): Response time {response_time:.3f} seconds{Style.RESET_ALL}")
            reachable_resolvers.append(f"{resolver_name}: Response Time: {response_time:.3f} seconds")
        else:
            error_msg = f": {error}" if error else ""
            print(f"{Fore.RED} - Failed to query {resolver_name} ({resolver_ip}){error_msg}{Style.RESET_ALL}")
            unreachable_resolvers.append(f"{resolver_name}: unreachable{error_msg}")

    # Build results report
    results += "Reachable DNS Resolvers:\n"
    for resolver_info in reachable_resolvers:
        results += f"- {resolver_info}\n"

    if not unreachable_resolvers:
        results += "\nAll DNS resolvers are reachable.\n"
    else:
        results += "\nUnreachable DNS Resolvers:\n"
        for resolver_info in unreachable_resolvers:
            results += f"- {resolver_info}\n"

    return results


def main(silent: bool = False, polite: bool = False) -> str:
    """Main function to run the DNS resolver check.
    
    Args:
        silent: If True, suppress detailed console output
        polite: If True, use more verbose/polite messaging (not currently used)
        
    Returns:
        str: Report of the DNS resolver check
    """
    print(f"Starting DNS Resolver monitoring at {datetime.now()}\n")
    resolver_check_results = monitor_dns_resolvers()
    
    # Only print the raw results if not in silent mode
    if not silent:
        print(resolver_check_results)
    
    return resolver_check_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check DNS resolver reachability")
    parser.add_argument("--silent", action="store_true", help="Suppress detailed output")
    parser.add_argument("--polite", action="store_true", help="Use more verbose/polite messaging")
    
    args = parser.parse_args()
    main(silent=args.silent, polite=args.polite)