"""
Email Diagnostics Module

Comprehensive email server connectivity diagnostics for SMTP and IMAP services.
Tests connectivity to major email providers to identify network infrastructure issues.
Part of the instability.py v3 network diagnostics suite.
"""

import socket
from typing import Dict, Tuple, List, Any
from colorama import Fore, Style

# Import standardized tool result functions 
from utils import create_success_result, create_error_result

# SMTP server configurations for major email providers
SMTP_SERVERS: Dict[str, Tuple[str, int]] = {
    "Gmail": ("smtp.gmail.com", 587),
    "Outlook/O365": ("smtp.office365.com", 587),
    "Yahoo": ("smtp.mail.yahoo.com", 587),
    "iCloud Mail": ("smtp.mail.me.com", 587),
    "AOL Mail": ("smtp.aol.com", 587),
    "Zoho Mail": ("smtp.zoho.com", 587),
    "Mail.com": ("smtp.mail.com", 587),
    "GMX Mail": ("smtp.gmx.com", 587),
    "Fastmail": ("smtp.fastmail.com", 587)
}

# IMAP server configurations for major email providers
IMAP_SERVERS: Dict[str, Tuple[str, int]] = {
    "Gmail": ("imap.gmail.com", 993),
    "Outlook/O365": ("outlook.office365.com", 993),
    "Yahoo": ("imap.mail.yahoo.com", 993),
    "iCloud Mail": ("imap.mail.me.com", 993),
    "AOL Mail": ("imap.aol.com", 993),
    "Zoho Mail": ("imap.zoho.com", 993),
    "Mail.com": ("imap.mail.com", 993),
    "GMX Mail": ("imap.gmx.com", 993),
    "Fastmail": ("imap.fastmail.com", 993)
}


def _test_server_connectivity(hostname: str, port: int, timeout: int = 10) -> Tuple[bool, str]:
    """
    Test connectivity to a specific server and port using socket connection.
    
    Args:
        hostname: Server hostname to test
        port: Port number to test
        timeout: Connection timeout in seconds
        
    Returns:
        Tuple of (success, status_message)
    """
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return True, "Connected successfully"
    except socket.timeout:
        return False, "Connection timeout"
    except socket.gaierror as e:
        return False, f"DNS resolution failed: {e}"
    except ConnectionRefusedError:
        return False, "Connection refused"
    except Exception as e:
        return False, f"Connection failed: {e}"


def check_smtp_connectivity(silent: bool = False) -> str:
    """
    Test SMTP server connectivity for major email providers.
    
    Tests outbound email server connectivity by attempting socket connections
    to major SMTP providers on secure port 587 (SMTP submission port).
    
    Args:
        silent: Suppress console output if True
        
    Returns:
        Formatted summary of SMTP connectivity test results
    """
    if not silent:
        print(f"{Fore.CYAN}Testing SMTP connectivity to major email providers...{Fore.RESET}")
    
    reachable = []
    unreachable = []
    
    for provider, (hostname, port) in SMTP_SERVERS.items():
        if not silent:
            print(f"{Fore.YELLOW}Testing {provider} ({hostname}:{port})...{Fore.RESET}")
        
        success, message = _test_server_connectivity(hostname, port, timeout=10)
        
        if success:
            reachable.append(provider)
            if not silent:
                print(f"{Fore.GREEN}[OK] {provider}: {message}{Fore.RESET}")
        else:
            unreachable.append((provider, message))
            if not silent:
                status_color = Fore.RED if "timeout" not in message.lower() else Fore.YELLOW
                status_text = "[FAIL]" if "timeout" not in message.lower() else "[TIMEOUT]"
                print(f"{status_color}{status_text} {provider}: {message}{Fore.RESET}")
    
    # Generate summary
    total_servers = len(SMTP_SERVERS)
    reachable_count = len(reachable)
    
    summary = f"\nSMTP Connectivity Summary:\n"
    summary += f"Reachable servers: {reachable_count}/{total_servers}\n"
    
    if reachable:
        summary += f"\n{Fore.GREEN}Reachable SMTP servers:{Fore.RESET}\n"
        for provider in reachable:
            hostname, port = SMTP_SERVERS[provider]
            summary += f"  [OK] {provider} ({hostname}:{port})\n"
    
    if unreachable:
        summary += f"\n{Fore.RED}Unreachable SMTP servers:{Fore.RESET}\n"
        for provider, error in unreachable:
            hostname, port = SMTP_SERVERS[provider]
            status = "[TIMEOUT]" if "timeout" in error.lower() else "[FAIL]"
            summary += f"  {status} {provider} ({hostname}:{port}) - {error}\n"
    
    if not silent:
        print(summary)
    
    return summary


def check_imap_connectivity(silent: bool = False) -> str:
    """
    Test IMAP server connectivity for major email providers.
    
    Tests inbound email server connectivity by attempting socket connections
    to major IMAP providers on secure port 993 (IMAPS).
    
    Args:
        silent: Suppress console output if True
        
    Returns:
        Formatted summary of IMAP connectivity test results
    """
    if not silent:
        print(f"{Fore.CYAN}Testing IMAP connectivity to major email providers...{Fore.RESET}")
    
    reachable = []
    unreachable = []
    
    for provider, (hostname, port) in IMAP_SERVERS.items():
        if not silent:
            print(f"{Fore.YELLOW}Testing {provider} ({hostname}:{port})...{Fore.RESET}")
        
        success, message = _test_server_connectivity(hostname, port, timeout=10)
        
        if success:
            reachable.append(provider)
            if not silent:
                print(f"{Fore.GREEN}[OK] {provider}: {message}{Fore.RESET}")
        else:
            unreachable.append((provider, message))
            if not silent:
                status_color = Fore.RED if "timeout" not in message.lower() else Fore.YELLOW
                status_text = "[FAIL]" if "timeout" not in message.lower() else "[TIMEOUT]"
                print(f"{status_color}{status_text} {provider}: {message}{Fore.RESET}")
    
    # Generate summary
    total_servers = len(IMAP_SERVERS)
    reachable_count = len(reachable)
    
    summary = f"\nIMAP Connectivity Summary:\n"
    summary += f"Reachable servers: {reachable_count}/{total_servers}\n"
    
    if reachable:
        summary += f"\n{Fore.GREEN}Reachable IMAP servers:{Fore.RESET}\n"
        for provider in reachable:
            hostname, port = IMAP_SERVERS[provider]
            summary += f"  [OK] {provider} ({hostname}:{port})\n"
    
    if unreachable:
        summary += f"\n{Fore.RED}Unreachable IMAP servers:{Fore.RESET}\n"
        for provider, error in unreachable:
            hostname, port = IMAP_SERVERS[provider]
            status = "[TIMEOUT]" if "timeout" in error.lower() else "[FAIL]"
            summary += f"  {status} {provider} ({hostname}:{port}) - {error}\n"
    
    if not silent:
        print(summary)
    
    return summary


def check_all_email_services(silent: bool = False) -> str:
    """
    Comprehensive email infrastructure connectivity assessment.
    
    Tests both SMTP and IMAP server connectivity for major email providers
    to provide a complete view of email infrastructure availability.
    
    Args:
        silent: Suppress console output if True
        
    Returns:
        Unified summary of all email service connectivity
    """
    if not silent:
        print(f"{Fore.CYAN}Comprehensive Email Infrastructure Assessment{Fore.RESET}")
        print(f"{Fore.CYAN}Testing both SMTP and IMAP connectivity...{Fore.RESET}\n")
    
    # Run both tests with silent mode to control output
    smtp_summary = check_smtp_connectivity(silent=True)
    if not silent:
        print()  # Add spacing between tests
    imap_summary = check_imap_connectivity(silent=True)
    
    # Generate unified summary
    smtp_reachable = len([line for line in smtp_summary.split('\n') if '[OK]' in line and 'SMTP' not in line])
    imap_reachable = len([line for line in imap_summary.split('\n') if '[OK]' in line and 'IMAP' not in line])
    
    total_smtp = len(SMTP_SERVERS)
    total_imap = len(IMAP_SERVERS)
    total_servers = total_smtp + total_imap
    total_reachable = smtp_reachable + imap_reachable
    
    unified_summary = f"\n{Fore.CYAN}Email Infrastructure Assessment Summary:{Fore.RESET}\n"
    unified_summary += f"Total email servers tested: {total_servers} (SMTP: {total_smtp}, IMAP: {total_imap})\n"
    unified_summary += f"Total reachable servers: {total_reachable}/{total_servers}\n"
    unified_summary += f"SMTP servers reachable: {smtp_reachable}/{total_smtp}\n"
    unified_summary += f"IMAP servers reachable: {imap_reachable}/{total_imap}\n"
    
    # Add detailed results from individual tests
    unified_summary += f"\n{'-' * 50}\n"
    unified_summary += smtp_summary
    unified_summary += f"\n{'-' * 50}\n"
    unified_summary += imap_summary
    
    # Overall status assessment
    if total_reachable == total_servers:
        status_msg = f"{Fore.GREEN}[EXCELLENT] All email services are reachable{Fore.RESET}"
    elif total_reachable >= total_servers * 0.8:
        status_msg = f"{Fore.GREEN}[GOOD] Most email services are reachable{Fore.RESET}"
    elif total_reachable >= total_servers * 0.5:
        status_msg = f"{Fore.YELLOW}[PARTIAL] Some email connectivity issues detected{Fore.RESET}"
    else:
        status_msg = f"{Fore.RED}[POOR] Significant email connectivity problems{Fore.RESET}"
    
    unified_summary += f"\n{'-' * 50}\n"
    unified_summary += f"Overall Email Infrastructure Status: {status_msg}\n"
    
    if not silent:
        print(unified_summary)
    
    return unified_summary


def get_module_tools():
    """
    Get tool metadata for email diagnostics module registration.
    
    Returns:
        Dictionary of tool metadata for tools registry integration
    """
    from core.tools_registry import ToolMetadata, ParameterInfo, ParameterType, ToolCategory
    
    return {
        "check_smtp_connectivity": ToolMetadata(
            name="check_smtp_connectivity",
            function_name="check_smtp_connectivity",
            module_path="network.email_diagnostics",
            description="Test SMTP server connectivity for major email providers",
            category=ToolCategory.EMAIL_DIAGNOSTICS,
            parameters={
                "silent": ParameterInfo(
                    ParameterType.BOOLEAN, 
                    default=False,
                    description="Suppress console output if True"
                )
            },
            aliases=["smtp_test", "test_smtp"],
            examples=[
                "check_smtp_connectivity",
                "check_smtp_connectivity silent=True"
            ]
        ),
        "check_imap_connectivity": ToolMetadata(
            name="check_imap_connectivity", 
            function_name="check_imap_connectivity",
            module_path="network.email_diagnostics",
            description="Test IMAP server connectivity for major email providers",
            category=ToolCategory.EMAIL_DIAGNOSTICS,
            parameters={
                "silent": ParameterInfo(
                    ParameterType.BOOLEAN, 
                    default=False,
                    description="Suppress console output if True"
                )
            },
            aliases=["imap_test", "test_imap"],
            examples=[
                "check_imap_connectivity",
                "check_imap_connectivity silent=True"
            ]
        ),
        "check_all_email_services": ToolMetadata(
            name="check_all_email_services",
            function_name="check_all_email_services", 
            module_path="network.email_diagnostics",
            description="Comprehensive email infrastructure connectivity assessment",
            category=ToolCategory.EMAIL_DIAGNOSTICS,
            parameters={
                "silent": ParameterInfo(
                    ParameterType.BOOLEAN, 
                    default=False,
                    description="Suppress console output if True"
                )
            },
            aliases=["email_test", "test_email", "email_diagnostics"],
            examples=[
                "check_all_email_services",
                "check_all_email_services silent=True"
            ]
        )
    }