"""
External IP Check Module for Instability v2

This module provides functionality to:
1. Get the current external/public IP address
2. (Optionally) Check IP reputation with AbuseIPDB (when API key is available)
"""

import os
import requests
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


def main(silent: bool = False, polite: bool = False) -> str:
    """
    Get the external IP address and check its reputation if an API key is available.
    
    Args:
        silent (bool): If True, suppress detailed output
        polite (bool): If True, use more polite language in output
        
    Returns:
        str: The external IP address or detailed reputation if available
    """
    # Get the current external IP
    external_ip = get_public_ip()
    
    if external_ip == "Could not determine external IP (offline or no connectivity)":
        print(f"{Fore.RED}Failed to retrieve external IP.{Style.RESET_ALL}")
        return external_ip
    
    if not silent:
        print(f"{Fore.GREEN}External IP: {external_ip}{Style.RESET_ALL}")
    
    # Try to get the AbuseIPDB API key from the environment
    api_key = os.environ.get("ABUSEIPDB_API_KEY")
    
    # If no API key, just return the IP without reputation check
    if not api_key:
        return external_ip
    
    # Check reputation of the external IP
    reputation_data = check_ip_reputation(external_ip, api_key)
    
    # Analyze and display the results
    if reputation_data:
        try:
            ip_reputation_output = analyze_ip_reputation(reputation_data)
            if not silent:
                print(ip_reputation_output)
            return f"{external_ip}\n{ip_reputation_output}"
        except Exception as e:
            print(f"{Fore.RED}Failed to analyze IP reputation data.{Style.RESET_ALL}")
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
    
    return external_ip


if __name__ == "__main__":
    main()