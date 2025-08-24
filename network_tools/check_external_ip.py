"""
External IP Check Module for Instability v2

This module provides functionality to:
1. Get the current external/public IP address
2. (Optionally) Check IP reputation with AbuseIPDB (when API key is available)
"""

import os
import requests
import socket
import subprocess
import json
from typing import Dict, Any, Optional
from colorama import Fore, Style, init

# Initialize colorama for cross-platform color support
init(autoreset=True)


def get_public_ip() -> str:
    """
    Retrieve the public IP address of the current internet connection.
    
    This function tries multiple services to ensure reliability.

    Returns:
        str: The public IP address.
    """
    # Try multiple services in case one is down
    services = [
        "https://api.ipify.org?format=json",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://ident.me"
    ]
    
    for service in services:
        try:
            if "ipify" in service:
                # JSON format
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    return response.json().get("ip")
            else:
                # Plain text format
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    return response.text.strip()
        except Exception as e:
            continue
    
    # If all services fail
    return "Could not determine external IP (offline or no connectivity)"


def check_ip_reputation(ip: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Check the reputation of an IP address using the AbuseIPDB API.
    
    Args:
        ip (str): The IP address to check
        api_key (str): The AbuseIPDB API key
        
    Returns:
        Optional[Dict[str, Any]]: The reputation data or None if the request fails
    """
    if not api_key:
        print(f"{Fore.YELLOW}No AbuseIPDB API key provided. Skipping reputation check.{Style.RESET_ALL}")
        return None
    
    headers = {
        'Accept': 'application/json',
        'Key': api_key
    }
    
    params = {
        'ipAddress': ip,
        'maxAgeInDays': '90',
        'verbose': ''
    }
    
    try:
        response = requests.get(
            'https://api.abuseipdb.com/api/v2/check',
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"{Fore.RED}Error checking IP reputation: {response.status_code}{Style.RESET_ALL}")
            return None
    
    except Exception as e:
        print(f"{Fore.RED}Exception checking IP reputation: {e}{Style.RESET_ALL}")
        return None


def analyze_ip_reputation(reputation_data: Dict[str, Any]) -> str:
    """
    Analyze IP reputation data and return a formatted string with the results.
    
    Args:
        reputation_data (Dict[str, Any]): The reputation data from AbuseIPDB
        
    Returns:
        str: Formatted analysis of the IP reputation
    """
    data = reputation_data.get('data', {})
    
    ip_address = data.get('ipAddress', 'Unknown')
    abuse_score = data.get('abuseConfidenceScore', 0)
    total_reports = data.get('totalReports', 0)
    last_reported = data.get('lastReportedAt', 'Never')
    country_code = data.get('countryCode', 'Unknown')
    isp = data.get('isp', 'Unknown')
    domain = data.get('domain', 'Unknown')
    
    # Determine color based on abuse score
    if abuse_score > 80:
        score_color = Fore.RED
    elif abuse_score > 20:
        score_color = Fore.YELLOW
    else:
        score_color = Fore.GREEN
    
    output = [
        f"IP Address: {ip_address}",
        f"Abuse Confidence Score: {score_color}{abuse_score}%{Style.RESET_ALL}",
        f"Total Reports: {total_reports}",
        f"Last Reported: {last_reported if last_reported != 'Never' else 'Never reported'}",
        f"Country: {country_code}",
        f"ISP: {isp}",
        f"Domain: {domain}"
    ]
    
    return "\n".join(output)


def check_spamhaus_blacklists(ip: str) -> Dict[str, Dict[str, Any]]:
    """
    Check IP address against Spamhaus DNS-based blacklists.
    
    Args:
        ip (str): IP address to check (e.g., "192.168.1.1")
        
    Returns:
        Dict[str, Dict[str, Any]]: Results for each blacklist with status and details
        
    Raises:
        ValueError: If IP address format is invalid
    """
    # Validate IP address format
    parts = ip.split('.')
    if len(parts) != 4:
        raise ValueError(f"Invalid IP address format: {ip}")
    
    try:
        for part in parts:
            num = int(part)
            if not (0 <= num <= 255):
                raise ValueError(f"Invalid IP address format: {ip}")
    except ValueError:
        raise ValueError(f"Invalid IP address format: {ip}")
    
    # Reverse IP address (1.2.3.4 -> 4.3.2.1)
    reversed_ip = '.'.join(parts[::-1])
    
    # Define Spamhaus blacklists to check
    blacklists = {
        'sbl': 'sbl.spamhaus.org',
        'css': 'css.spamhaus.org', 
        'pbl': 'pbl.spamhaus.org'
    }
    
    results = {}
    
    for list_name, domain in blacklists.items():
        query_host = f"{reversed_ip}.{domain}"
        
        result_entry = {
            'listed': False,
            'query': query_host,
            'response': None,
            'error': None
        }
        
        try:
            # Perform DNS query - successful resolution means IP is listed
            response = socket.gethostbyname(query_host)
            result_entry['response'] = response
            
            # Interpret response codes based on list type
            if list_name == 'pbl':
                # PBL listings are informational for residential/dynamic IPs - not necessarily malicious
                result_entry['listed'] = True
                result_entry['severity'] = 'info'  # Informational, not critical
            elif list_name in ['sbl', 'css']:
                # SBL and CSS listings indicate spam sources - more serious
                result_entry['listed'] = True
                result_entry['severity'] = 'warning'  # Actual security concern
            else:
                result_entry['listed'] = True
                result_entry['severity'] = 'warning'
            
        except socket.gaierror as e:
            # DNS resolution failed - IP is clean (not listed)
            result_entry['listed'] = False
            result_entry['severity'] = 'clean'
            result_entry['error'] = None  # This is expected for clean IPs
            
        except Exception as e:
            # Unexpected error during DNS query
            result_entry['listed'] = False
            result_entry['severity'] = 'error'
            result_entry['error'] = str(e)
        
        results[list_name] = result_entry
    
    return results


def analyze_spamhaus_reputation(spamhaus_data: Dict[str, Dict[str, Any]]) -> str:
    """
    Format Spamhaus blacklist results for display.
    
    Args:
        spamhaus_data (Dict[str, Dict[str, Any]]): Results from check_spamhaus_blacklists()
        
    Returns:
        str: Formatted analysis of Spamhaus blacklist status
    """
    if not spamhaus_data:
        return f"{Fore.YELLOW}No Spamhaus data available{Style.RESET_ALL}"
    
    output = [f"{Fore.CYAN}Spamhaus Blacklist Check:{Style.RESET_ALL}"]
    
    # Map blacklist names to human-readable descriptions
    blacklist_names = {
        'sbl': 'SBL (Spamhaus Block List)',
        'css': 'CSS (Composite Spamhaus Source)', 
        'pbl': 'PBL (Policy Block List)'
    }
    
    warning_count = 0  # SBL/CSS listings (actual threats)
    info_count = 0     # PBL listings (informational)
    clean_count = 0    # Not listed
    total_count = len(spamhaus_data)
    
    for list_name, result in spamhaus_data.items():
        display_name = blacklist_names.get(list_name, list_name.upper())
        
        if result['error']:
            # Unexpected error occurred
            status_color = Fore.YELLOW
            status_text = f"ERROR: {result['error']}"
        elif result['listed']:
            severity = result.get('severity', 'warning')
            
            if severity == 'warning':
                # SBL/CSS listings - actual security concern
                status_color = Fore.RED
                status_text = f"LISTED - THREAT (Response: {result['response']})"
                warning_count += 1
            elif severity == 'info':
                # PBL listing - informational (residential/dynamic IP)
                status_color = Fore.YELLOW
                status_text = f"LISTED - INFO (Response: {result['response']})"
                info_count += 1
            else:
                status_color = Fore.RED
                status_text = f"LISTED (Response: {result['response']})"
                warning_count += 1
        else:
            # IP is clean
            status_color = Fore.GREEN
            status_text = "CLEAN"
            clean_count += 1
        
        output.append(f"  {display_name}: {status_color}{status_text}{Style.RESET_ALL}")
    
    # Add summary based on severity
    if warning_count > 0:
        summary_color = Fore.RED
        summary_text = f"WARNING: IP listed on {warning_count} threat blacklists (SBL/CSS)"
    elif info_count > 0 and clean_count > 0:
        summary_color = Fore.BLUE
        summary_text = f"INFO: IP listed on PBL (normal for residential/dynamic IPs)"
    elif clean_count == total_count:
        summary_color = Fore.GREEN
        summary_text = "IP appears clean - not listed on any Spamhaus blacklists"
    else:
        summary_color = Fore.YELLOW
        summary_text = f"Mixed results: {info_count} informational, {warning_count} warnings"
    
    output.append(f"Summary: {summary_color}{summary_text}{Style.RESET_ALL}")
    
    return "\n".join(output)


def main(silent: bool = False, polite: bool = False) -> str:
    """
    Get external IP and check reputation with AbuseIPDB and Spamhaus.
    
    Args:
        silent (bool): If True, suppress detailed output  
        polite (bool): If True, use more polite language in output
        
    Returns:
        str: External IP with comprehensive reputation analysis
    """
    # Get the current external IP
    external_ip = get_public_ip()
    
    if external_ip == "Could not determine external IP (offline or no connectivity)":
        print(f"{Fore.RED}Failed to retrieve external IP.{Style.RESET_ALL}")
        return external_ip
    
    if not silent:
        print(f"{Fore.GREEN}External IP: {external_ip}{Style.RESET_ALL}")
    
    output_sections = [external_ip]
    
    # Try to get the AbuseIPDB API key from the environment
    api_key = os.environ.get("ABUSEIPDB_API_KEY")
    
    # Check AbuseIPDB reputation if API key is available
    if api_key:
        try:
            reputation_data = check_ip_reputation(external_ip, api_key)
            if reputation_data:
                ip_reputation_output = analyze_ip_reputation(reputation_data)
                if not silent:
                    print(ip_reputation_output)
                output_sections.append(ip_reputation_output)
        except Exception as e:
            error_msg = f"Failed to analyze AbuseIPDB reputation data: {e}"
            if not silent:
                print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
    
    # Always check Spamhaus blacklists (no API key required)
    try:
        spamhaus_data = check_spamhaus_blacklists(external_ip)
        spamhaus_output = analyze_spamhaus_reputation(spamhaus_data)
        if not silent:
            print(spamhaus_output)
        output_sections.append(spamhaus_output)
    except Exception as e:
        error_msg = f"Failed to check Spamhaus blacklists: {e}"
        if not silent:
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
    
    return "\n".join(output_sections)


def get_module_tools():
    """
    Get tool metadata for external IP checking and reputation analysis registration.
    
    Returns:
        Dictionary of tool metadata for tools registry integration
    """
    from core.tools_registry import ToolMetadata, ParameterInfo, ParameterType, ToolCategory
    
    return {
        "check_ip_reputation": ToolMetadata(
            name="check_ip_reputation",
            function_name="main",
            module_path="network_tools.check_external_ip",
            description="Get external IP address and check reputation using AbuseIPDB and Spamhaus blacklists (ABUSEIPDB_API_KEY env var optional)",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "silent": ParameterInfo(
                    ParameterType.BOOLEAN,
                    default=False,
                    description="Suppress verbose console output"
                ),
                "polite": ParameterInfo(
                    ParameterType.BOOLEAN,
                    default=False,
                    description="Use more polite language in output"
                )
            },
            aliases=["external_ip_reputation", "ip_reputation", "get_external_ip"],
            examples=[
                "check_ip_reputation",
                "check_ip_reputation --silent"
            ]
        )
    }


if __name__ == "__main__":
    main()