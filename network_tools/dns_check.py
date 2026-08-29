"""
DNS Root Servers Check module for Instability v2

This module checks the reachability of DNS Root Servers, which are crucial
to the functioning of the internet. DNS Root Servers are responsible for
providing the IP addresses of top-level domain (TLD) servers, which in turn
provide the IP addresses of individual domain names.
"""

import dns.exception
import dns.message
import dns.query
import dns.resolver
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from colorama import Fore, Style

from .dns_interception import (
    describe_icmp_result, dns_interception_detected, icmp_reachable,
    interception_notice,
)

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


def check_dns_server(name: str, ip: str, query_name: str = ".") -> Tuple[bool, Optional[str]]:
    """Check if a specific DNS root server is reachable.

    Queries the server directly for the root zone's NS records, using a plain
    DNS message rather than a Resolver.

    Both of those are deliberate. A root server is not recursive: asked for
    'example.com A' it returns a REFERRAL to the .com nameservers with an empty
    answer section, and dns.resolver.Resolver.resolve() raises NoAnswer on an
    empty answer section -- so the previous implementation may have been
    reporting every root server unreachable whenever it was not being masked by
    a local DNS proxy answering on their behalf. That is a prediction rather
    than a measurement (it could not be confirmed on the intercepted host where
    this was written; see docs/dns_interception_srd.md section 5.7), but '.' NS
    is the correct question either way: it asks the server for the zone it
    actually serves, and it is answered authoritatively.

    Args:
        name: The name of the root server (e.g., "A", "B", etc.)
        ip: The IP address of the root server
        query_name: The name to query (default: the root zone)

    Returns:
        Tuple containing:
            - Boolean indicating if server is reachable
            - Error message (None if reachable)
    """
    try:
        query = dns.message.make_query(query_name, "NS")
        response = dns.query.udp(query, ip, timeout=5)
        if not (response.answer or response.authority):
            raise dns.exception.DNSException("empty response")

        print(f"{Fore.GREEN} - Successfully queried the '{name}' root server at {ip} for '{query_name}'{Style.RESET_ALL}")
        return True, None

    except (OSError, dns.exception.DNSException) as e:
        print(f"{Fore.RED} - Failed to query {name} root server at {ip}: {e}{Style.RESET_ALL}")
        return False, str(e)


def _icmp_fallback(servers: Dict[str, str]) -> List[str]:
    """Probe each root server with ICMP when no DNS signal can be trusted.

    This answers a different and weaker question than the DNS check: whether the
    host replies to a ping, not whether it is serving the root zone. Callers
    must present it that way.

    Note that some root servers legitimately drop ICMP -- G (192.112.36.4) and
    L (199.7.83.42) both did on every attempt, while the other eleven replied in
    2.6 to 65.9 ms -- so a non-reply is reported as "did not answer a ping" and
    never as "down".

    Args:
        servers: Mapping of root server name to IP address.

    Returns:
        One description line per server, for the "could not be checked" section.
    """
    descriptions = []
    for name, ip in servers.items():
        answered, round_trip_ms = icmp_reachable(ip)
        print(describe_icmp_result(f"'{name}' root server", ip, answered,
                                   round_trip_ms))
        if answered:
            descriptions.append(f"- {name} ({ip}) - DNS not testable here; "
                                f"answers a ping in {round_trip_ms:.0f} ms")
        else:
            descriptions.append(f"- {name} ({ip}) - DNS not testable here; "
                                f"did not answer a ping either")
    return descriptions


def check_dns_root_servers(servers: Optional[Dict[str, str]] = None, retry_failed: bool = True) -> Tuple[List[str], List[str], List[str]]:
    """Check if DNS root servers are reachable.

    Args:
        servers: Optional dictionary of DNS root servers to check (name -> IP)
                If None, uses the default DNS_ROOT_SERVERS
        retry_failed: Whether to retry unreachable servers after a delay

    Returns:
        Tuple containing:
            - List of reachable server descriptions
            - List of unreachable server descriptions
            - List of servers that could not be checked at all. This third list
              is the point: on a host where DNS is intercepted it holds every
              server, and it must never be folded into either of the others.
    """
    if servers is None:
        servers = DNS_ROOT_SERVERS

    reachable_servers = []
    unreachable_servers = []

    # The root servers serve DNS on port 53 and nothing else, and they offer no
    # uniform encrypted alternative (measured: B accepts 853 with a certificate
    # that does not verify, F accepts 443, A and K time out, M refuses). So on a
    # host where a DNS proxy answers for every destination there is no way to
    # test them at all -- and the honest report is that the check could not be
    # run, never that they are fine. ICMP is offered instead as an explicitly
    # weaker signal. See docs/dns_interception_srd.md section 5.5.
    if dns_interception_detected() is not False:
        return [], [], _icmp_fallback(servers)

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

    return reachable_servers, unreachable_servers, []


def generate_dns_report(reachable: List[str], unreachable: List[str],
                        unknown: Optional[List[str]] = None) -> str:
    """Generate a formatted report of DNS root server reachability.

    Args:
        reachable: List of reachable server descriptions
        unreachable: List of unreachable server descriptions
        unknown: List of servers that could not be checked at all. Reported in
            its own section and never folded into either of the others: a
            server nobody could reach a verdict on is not a server that
            answered, and it is not one that failed.

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

    unknown = unknown or []
    if unknown:
        report += "\n" + interception_notice() + "\n"
        report += ("The root servers offer no encrypted alternative to port 53, "
                   "so their DNS reachability cannot be tested from this host at "
                   "all. Ping results below answer a weaker question -- whether "
                   "the host replies -- and some root servers drop ICMP even "
                   "when healthy.\n")
        report += "\nDNS Root Servers That Could Not Be Checked:\n"
        for server in unknown:
            report += server + "\n"

    if unknown and not reachable and not unreachable:
        report += (f"\nDNS Root Servers reachability summary: could not be "
                   f"determined for any of the {len(unknown)} root servers.\n")
    elif unknown:
        report += (f"\nDNS Root Servers reachability summary: {len(reachable)} "
                   f"reachable, {len(unreachable)} unreachable, {len(unknown)} "
                   f"could not be checked.\n")
    elif not unreachable:
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
    
    reachable, unreachable, unknown = check_dns_root_servers(DNS_ROOT_SERVERS)
    report = generate_dns_report(reachable, unreachable, unknown)
    
    # Only print detailed output if not in silent mode
    if not silent:
        print(f"\n{report}")
    
    return report


def get_module_tools():
    """
    Return tool metadata for this module.

    Only expose check_dns_root_servers as the public user-facing tool.
    Internal utilities (check_dns_server, generate_dns_report, main) are hidden.

    Returns:
        Dict of tool metadata for public tools only
    """
    from core.tools_registry import ToolMetadata, ParameterInfo, ParameterType, ToolCategory

    return {
        "check_dns_root_servers": ToolMetadata(
            name="check_dns_root_servers",
            function_name="check_dns_root_servers",
            module_path="network_tools.dns_check",
            description="Check connectivity to DNS root servers to verify DNS infrastructure",
            category=ToolCategory.DNS,
            parameters={
                "servers": ParameterInfo(
                    param_type=ParameterType.DICT,
                    required=False,
                    description="Dict of DNS root servers to check (default: all 13 root servers)"
                ),
                "retry_failed": ParameterInfo(
                    param_type=ParameterType.BOOLEAN,
                    required=False,
                    default=True,
                    description="Whether to retry failed servers"
                )
            },
            modes=["manual", "chatbot"],
            examples=[
                "check_dns_root_servers()",
                "check_dns_root_servers(retry_failed=False)"
            ]
        )
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check DNS root servers reachability")
    parser.add_argument("--silent", action="store_true", help="Suppress detailed output")
    parser.add_argument("--polite", action="store_true", help="Use more verbose/polite messaging")

    args = parser.parse_args()
    main(silent=args.silent, polite=args.polite)