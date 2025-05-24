"""
Web Check Module for Instability v2

This module provides functionality to:
1. Check if major websites are reachable
2. Measure response times for reachable websites
3. Identify connectivity issues with specific websites
"""

import time
import warnings
import requests
from typing import List, Tuple, Dict, Any, Union, Optional
from urllib.parse import urljoin, urlparse
from colorama import Fore, Style, init

# Initialize colorama for cross-platform color support
init(autoreset=True)

# Suppress SSL warnings for unverified requests (since we're only testing reachability)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# List of significant websites to check
DEFAULT_WEBSITES: List[str] = [
    "https://www.google.com",
    "https://www.amazon.com",
    "https://www.facebook.com",
    "https://www.apple.com",
    "https://www.microsoft.com",
    "https://www.reddit.com",
    "https://www.wikipedia.org",
    "https://www.netflix.com",
    "https://www.bbc.com",
    "https://www.nytimes.com",
    # Government websites
    "https://www.usa.gov",           # US
    "https://www.canada.ca",         # Canada
    "https://www.gov.uk",            # UK
    "https://www.gouvernement.fr",   # France
    "https://www.bund.de",           # Germany
    "https://www.australia.gov.au",  # Australia
    "https://www.gov.sg"             # Singapore
]

# User agent to make requests appear like they come from a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
}


def check_website(url: str, verify_ssl: bool = False, timeout: int = 10) -> Tuple[str, Union[float, str]]:
    """
    Check if a website is reachable
    
    Args:
        url: The URL to check
        verify_ssl: Whether to verify SSL certificates (default: False)
        timeout: Timeout in seconds for the request (default: 10)
        
    Returns:
        tuple: (status, result) where status is 'reachable' or 'unreachable'
              and result is either response time or error message
    """
    try:
        # Parse the URL correctly
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # First try robots.txt as it's usually a small file
        robots_url = urljoin(base_url, "/robots.txt")
        
        response = requests.get(robots_url, headers=HEADERS, timeout=timeout, verify=verify_ssl)
        
        if response.status_code == 200:
            return "reachable", response.elapsed.total_seconds()
        elif response.status_code == 404:
            # Retry with root URL if robots.txt not found
            response = requests.get(url, headers=HEADERS, timeout=timeout, verify=verify_ssl)
            if response.status_code in [200, 301, 302, 303, 307, 308]:  # Accept redirects as reachable
                return "reachable", response.elapsed.total_seconds()
            else:
                return "unreachable", f"Status Code: {response.status_code}"
        else:
            return "unreachable", f"Status Code: {response.status_code}"
    except requests.exceptions.Timeout:
        return "unreachable", "Timeout reached"
    except requests.exceptions.ConnectionError as e:
        return "unreachable", str(e)
    except Exception as e:
        return "unreachable", str(e)


def check_websites_reachability(
    websites: List[str] = DEFAULT_WEBSITES,
    max_retries: int = 1,
    retry_delay: int = 3,
    timeout: int = 10,
    silent: bool = False
) -> Tuple[List[Tuple[str, float]], List[Tuple[str, str]]]:
    """
    Check the reachability of multiple websites with configurable retry behavior
    
    Args:
        websites: List of website URLs to check (default: DEFAULT_WEBSITES)
        max_retries: Maximum number of retry attempts (default: 1)
        retry_delay: Delay between retries in seconds (default: 3)
        timeout: Timeout in seconds for each request (default: 10)
        silent: Whether to suppress progress output (default: False)
        
    Returns:
        tuple: (reachable_websites, unreachable_websites) where each is a list of (url, result) tuples
    """
    # Initialize lists to store reachable and unreachable websites
    reachable_websites = []
    unreachable_websites = []
    
    # First round of checks
    for url in websites:
        if not silent:
            print(f"Checking {url}... ", end="", flush=True)
            
        status, result = check_website(url, timeout=timeout)
        
        if status == "reachable":
            reachable_websites.append((url, result))
            if not silent:
                print(f"{Fore.GREEN}Reachable{Style.RESET_ALL} ({result:.3f}s)")
        else:
            unreachable_websites.append((url, result))
            if not silent:
                print(f"{Fore.RED}Unreachable{Style.RESET_ALL} ({result})")
    
    # Retry logic with configurable attempts
    retry_count = 0
    while unreachable_websites and retry_count < max_retries:
        retry_count += 1
        if not silent:
            print(f"\n{Fore.YELLOW}Retry attempt {retry_count} of {max_retries}...{Style.RESET_ALL}\n")
            
        time.sleep(retry_delay)
        
        remaining_unreachable = []
        for url, error in unreachable_websites:
            if not silent:
                print(f"Retrying {url}... ", end="", flush=True)
                
            status, retry_result = check_website(url, timeout=timeout)
            
            if status == "reachable":
                reachable_websites.append((url, retry_result))
                if not silent:
                    print(f"{Fore.GREEN}Now Reachable{Style.RESET_ALL} ({retry_result:.3f}s)")
            else:
                remaining_unreachable.append((url, retry_result))
                if not silent:
                    print(f"{Fore.RED}Still Unreachable{Style.RESET_ALL} ({retry_result})")
        
        unreachable_websites = remaining_unreachable
    
    return reachable_websites, unreachable_websites


def format_check_results(reachable: List[Tuple[str, float]], unreachable: List[Tuple[str, str]]) -> str:
    """
    Format website check results into a readable string
    
    Args:
        reachable: List of tuples (url, response_time) for reachable websites
        unreachable: List of tuples (url, error) for unreachable websites
        
    Returns:
        str: Formatted results
    """
    result = []
    
    # Sort reachable websites by response time
    reachable_sorted = sorted(reachable, key=lambda x: x[1])
    
    result.append(f"{Fore.CYAN}Reachable Websites ({len(reachable)}):{Style.RESET_ALL}")
    for url, response_time in reachable_sorted:
        # Color code response times (green < 0.5s, yellow < 2s, red > 2s)
        if response_time < 0.5:
            time_color = Fore.GREEN
        elif response_time < 2.0:
            time_color = Fore.YELLOW
        else:
            time_color = Fore.RED
            
        result.append(f"  {url}: {time_color}{response_time:.3f}s{Style.RESET_ALL}")
    
    if unreachable:
        result.append(f"\n{Fore.RED}Unreachable Websites ({len(unreachable)}):{Style.RESET_ALL}")
        for url, error in unreachable:
            result.append(f"  {url}: {error}")
    
    # Add a summary
    total = len(reachable) + len(unreachable)
    if unreachable:
        status = f"{Fore.YELLOW}Partial Connectivity{Style.RESET_ALL}"
        details = f"{len(reachable)}/{total} websites reachable"
    else:
        status = f"{Fore.GREEN}Full Connectivity{Style.RESET_ALL}"
        details = "All websites reachable"
    
    result.append(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL} {status} - {details}")
    
    if unreachable and len(unreachable) <= 3 and len(reachable) > 0:
        result.append(f"{Fore.YELLOW}Diagnosis:{Style.RESET_ALL} You appear to have internet connectivity, but some specific websites are unreachable.")
        result.append("This could indicate regional blocking, DNS issues specific to those domains, or temporary service outages.")
    elif len(unreachable) > len(reachable) and len(reachable) > 0:
        result.append(f"{Fore.RED}Diagnosis:{Style.RESET_ALL} Significant connectivity issues detected. Most websites are unreachable.")
        result.append("This suggests serious network problems, possibly with your ISP or internet connection.")
    elif len(unreachable) == total:
        result.append(f"{Fore.RED}Diagnosis:{Style.RESET_ALL} Complete connectivity failure. No websites are reachable.")
        result.append("You appear to be offline or experiencing a severe network outage.")
    
    return "\n".join(result)


def main(silent: bool = False, polite: bool = False) -> str:
    """
    Check the reachability of significant websites
    
    Args:
        silent: Whether to suppress progress output (default: False)
        polite: Whether to use more polite phrasing in output (default: False)
        
    Returns:
        str: Summary of website checks
    """
    # Inform about the check
    if not silent:
        print(f"{Fore.CYAN}Checking connectivity to major websites...{Style.RESET_ALL}")
    
    # Run the checks
    reachable, unreachable = check_websites_reachability(
        websites=DEFAULT_WEBSITES,
        max_retries=1,
        retry_delay=3,
        timeout=8,
        silent=silent
    )
    
    # Format and return results
    result = format_check_results(reachable, unreachable)
    
    if not silent:
        print("\n" + result)
    
    return result


if __name__ == "__main__":
    main(silent=False)