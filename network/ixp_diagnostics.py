"""
Internet Exchange Point Monitoring Module

Comprehensive IXP connectivity monitoring for major global internet exchange points.
Tests HTTP/HTTPS connectivity to assess network infrastructure and routing characteristics.
Part of the instability.py v3 network diagnostics suite.
"""

import requests
import time
import urllib3
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from colorama import Fore

# Import standardized tool result functions
from utils import create_success_result, create_error_result

# Major internet exchange points to monitor
IXP_ENDPOINTS: Dict[str, str] = {
    "DE-CIX Frankfurt": "https://www.de-cix.net/",
    "LINX London": "https://www.linx.net/", 
    "AMS-IX Amsterdam": "https://www.ams-ix.net/",
    "NYIIX New York": "https://www.nyiix.net/",
    "HKIX Hong Kong": "https://www.hkix.net/",
    "Equinix Global": "https://status.equinix.com/"
}


def _test_ixp_connectivity(
    name: str, 
    url: str, 
    timeout: int = 15,
    retries: int = 3,
    user_agent: Optional[str] = None,
    insecure: bool = False,
    burp: bool = False,
    silent: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    Test HTTP connectivity to a specific IXP endpoint with retry logic.
    
    Args:
        name: IXP name for display
        url: IXP URL to test
        timeout: Connection timeout in seconds
        retries: Number of retry attempts
        user_agent: Custom User-Agent header
        insecure: Disable SSL certificate verification
        burp: Route through Burp Suite proxy
        silent: Suppress console output
        
    Returns:
        Tuple of (success, result_dict)
    """
    result = {
        "name": name,
        "url": url,
        "response_time": None,
        "status_code": None,
        "error": None,
        "retry_attempts": 0
    }
    
    # Configure session
    session = requests.Session()
    
    # Set User-Agent
    if user_agent:
        session.headers.update({"User-Agent": user_agent})
    else:
        session.headers.update({"User-Agent": "InstabilityIXP/1.0"})
    
    # Configure SSL verification
    if insecure:
        session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Configure Burp proxy
    if burp:
        session.proxies = {
            "http": "http://localhost:8080",
            "https": "http://localhost:8080"
        }
    
    # Retry logic with exponential backoff
    for attempt in range(retries + 1):
        result["retry_attempts"] = attempt
        
        if not silent and attempt > 0:
            backoff = 2 ** (attempt - 1)
            print(f"{Fore.YELLOW}  Retry {attempt}/{retries} for {name} (backoff: {backoff}s){Fore.RESET}")
            time.sleep(backoff)
        
        try:
            start_time = time.time()
            response = session.get(url, timeout=timeout)
            end_time = time.time()
            
            result["response_time"] = round((end_time - start_time) * 1000, 2)
            result["status_code"] = response.status_code
            
            if response.status_code == 200:
                return True, result
            else:
                result["error"] = f"HTTP {response.status_code}"
                if not silent:
                    print(f"{Fore.RED}  HTTP {response.status_code} for {name}{Fore.RESET}")
        
        except requests.exceptions.Timeout:
            result["error"] = "Connection timeout"
            if not silent:
                print(f"{Fore.YELLOW}  Timeout for {name} (attempt {attempt + 1}){Fore.RESET}")
        
        except requests.exceptions.ConnectionError as e:
            result["error"] = f"Connection failed: {str(e)}"
            if not silent:
                print(f"{Fore.RED}  Connection failed for {name}: {str(e)}{Fore.RESET}")
        
        except requests.exceptions.SSLError as e:
            result["error"] = f"SSL certificate error: {str(e)}"
            if not silent:
                print(f"{Fore.RED}  SSL error for {name}: {str(e)}{Fore.RESET}")
        
        except requests.exceptions.ProxyError as e:
            result["error"] = f"Proxy connection failed: {str(e)}"
            if not silent:
                print(f"{Fore.RED}  Proxy error for {name}: {str(e)}{Fore.RESET}")
        
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            if not silent:
                print(f"{Fore.RED}  Error for {name}: {str(e)}{Fore.RESET}")
    
    return False, result


def monitor_ixp_connectivity(
    silent: bool = False,
    timeout: int = 15,
    retries: int = 3,
    user_agent: Optional[str] = None,
    insecure: bool = False,
    burp: bool = False
) -> Dict[str, Any]:
    """
    Monitor connectivity to major internet exchange points worldwide.
    
    Tests HTTP/HTTPS connectivity to major global IXPs to assess network
    infrastructure health and routing characteristics for penetration testing
    and network reconnaissance activities.
    
    Args:
        silent: Suppress verbose console output
        timeout: Connection timeout in seconds
        retries: Number of retry attempts for failed connections  
        user_agent: Custom User-Agent header for HTTP requests
        insecure: Disable SSL certificate verification
        burp: Route traffic through Burp Suite proxy
        
    Returns:
        Dictionary containing connectivity results and summary statistics
    """
    if not silent:
        print(f"{Fore.CYAN}Internet Exchange Point Connectivity Assessment{Fore.RESET}")
        print(f"{Fore.CYAN}Testing connectivity to {len(IXP_ENDPOINTS)} major IXPs worldwide...{Fore.RESET}\n")
        
        if insecure:
            print(f"{Fore.YELLOW}Warning: SSL certificate verification disabled{Fore.RESET}")
        if burp:
            print(f"{Fore.YELLOW}Info: Routing traffic through Burp Suite proxy (localhost:8080){Fore.RESET}")
    
    reachable_ixps = []
    unreachable_ixps = []
    
    # Test each IXP
    for name, url in IXP_ENDPOINTS.items():
        if not silent:
            print(f"{Fore.YELLOW}Testing {name} ({url})...{Fore.RESET}")
        
        success, result = _test_ixp_connectivity(
            name=name,
            url=url,
            timeout=timeout,
            retries=retries,
            user_agent=user_agent,
            insecure=insecure,
            burp=burp,
            silent=silent
        )
        
        if success:
            reachable_ixps.append(result)
            if not silent:
                print(f"{Fore.GREEN}[OK] {name}: {result['response_time']}ms (HTTP {result['status_code']}){Fore.RESET}")
        else:
            unreachable_ixps.append(result)
            if not silent:
                status = "[TIMEOUT]" if "timeout" in result["error"].lower() else "[FAIL]"
                color = Fore.YELLOW if "timeout" in result["error"].lower() else Fore.RED
                print(f"{color}{status} {name}: {result['error']}{Fore.RESET}")
    
    # Calculate summary statistics
    total_tested = len(IXP_ENDPOINTS)
    successful = len(reachable_ixps)
    failed = len(unreachable_ixps)
    success_rate = round((successful / total_tested) * 100, 1) if total_tested > 0 else 0.0
    
    # Determine overall status
    if successful == total_tested:
        status = "success"
        status_msg = f"{Fore.GREEN}[EXCELLENT] All IXPs are reachable{Fore.RESET}"
    elif successful >= total_tested * 0.8:
        status = "success"
        status_msg = f"{Fore.GREEN}[GOOD] Most IXPs are reachable{Fore.RESET}"
    elif successful >= total_tested * 0.5:
        status = "partial"
        status_msg = f"{Fore.YELLOW}[PARTIAL] Some IXP connectivity issues detected{Fore.RESET}"
    else:
        status = "error"
        status_msg = f"{Fore.RED}[POOR] Significant IXP connectivity problems{Fore.RESET}"
    
    # Build result dictionary
    result = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "reachable_ixps": reachable_ixps,
        "unreachable_ixps": unreachable_ixps,
        "summary": {
            "total_tested": total_tested,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate
        }
    }
    
    # Display summary
    if not silent:
        print(f"\n{Fore.CYAN}IXP Connectivity Summary:{Fore.RESET}")
        print(f"Total IXPs tested: {total_tested}")
        print(f"Successful connections: {successful}/{total_tested}")
        print(f"Failed connections: {failed}/{total_tested}")
        print(f"Success rate: {success_rate}%")
        print(f"\nOverall status: {status_msg}")
        
        if reachable_ixps:
            print(f"\n{Fore.GREEN}Reachable IXPs:{Fore.RESET}")
            for ixp in reachable_ixps:
                print(f"  [OK] {ixp['name']} - {ixp['response_time']}ms")
        
        if unreachable_ixps:
            print(f"\n{Fore.RED}Unreachable IXPs:{Fore.RESET}")
            for ixp in unreachable_ixps:
                status_text = "[TIMEOUT]" if "timeout" in ixp["error"].lower() else "[FAIL]"
                print(f"  {status_text} {ixp['name']} - {ixp['error']} (after {ixp['retry_attempts']} retries)")
    
    return result


def get_module_tools():
    """
    Get tool metadata for IXP diagnostics module registration.
    
    Returns:
        Dictionary of tool metadata for tools registry integration
    """
    from core.tools_registry import ToolMetadata, ParameterInfo, ParameterType, ToolCategory
    
    return {
        "monitor_ixp_connectivity": ToolMetadata(
            name="monitor_ixp_connectivity",
            function_name="monitor_ixp_connectivity",
            module_path="network.ixp_diagnostics",
            description="Monitor connectivity to major internet exchange points worldwide",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "silent": ParameterInfo(
                    ParameterType.BOOLEAN,
                    default=False,
                    description="Suppress verbose console output"
                ),
                "timeout": ParameterInfo(
                    ParameterType.INTEGER,
                    default=15,
                    description="Connection timeout in seconds"
                ),
                "retries": ParameterInfo(
                    ParameterType.INTEGER,
                    default=3,
                    description="Number of retry attempts for failed connections"
                ),
                "user_agent": ParameterInfo(
                    ParameterType.STRING,
                    default=None,
                    description="Custom User-Agent header for HTTP requests"
                ),
                "insecure": ParameterInfo(
                    ParameterType.BOOLEAN,
                    default=False,
                    description="Disable SSL certificate verification"
                ),
                "burp": ParameterInfo(
                    ParameterType.BOOLEAN,
                    default=False,
                    description="Route traffic through Burp Suite proxy"
                )
            },
            aliases=["ixp_connectivity", "ixp_check", "exchange_points"],
            examples=[
                "monitor_ixp_connectivity",
                "monitor_ixp_connectivity --timeout 10 --retries 2",
                "monitor_ixp_connectivity --silent --insecure",
                "monitor_ixp_connectivity --burp --user_agent \"CustomTool/1.0\""
            ]
        )
    }