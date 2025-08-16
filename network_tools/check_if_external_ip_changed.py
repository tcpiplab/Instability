"""
External IP Change Detection Module

Monitors changes in external/public IP address over time, tracking current and previous 
IP addresses with timestamps. Uses private user config directory for data storage.
Part of the instability.py network tools suite.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from colorama import Fore, Style

# Import existing external IP functionality
try:
    from network_tools.check_external_ip import get_public_ip
except ImportError:
    from check_external_ip import get_public_ip


def get_config_file_path() -> Path:
    """
    Get the path to the external IP history configuration file.
    
    Returns:
        Path to the JSON file storing IP change history
    """
    config_dir = Path.home() / ".config" / "instability"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "external_ip_history.json"


def load_ip_history() -> Dict[str, Any]:
    """
    Load IP change history from user config file.
    
    Returns:
        Dictionary containing current and previous IP data, or empty structure if file doesn't exist
    """
    config_file = get_config_file_path()
    
    default_structure = {
        "current_ip": None,
        "current_timestamp": None,
        "previous_ip": None,
        "previous_timestamp": None
    }
    
    if not config_file.exists():
        return default_structure
    
    try:
        with open(config_file, 'r') as f:
            data = json.load(f)
            # Ensure all required keys exist
            for key in default_structure:
                if key not in data:
                    data[key] = default_structure[key]
            return data
    except (json.JSONDecodeError, IOError):
        return default_structure


def save_ip_history(ip_data: Dict[str, Any]) -> None:
    """
    Save IP change history to user config file.
    
    Args:
        ip_data: Dictionary containing current and previous IP information
    """
    config_file = get_config_file_path()
    
    try:
        with open(config_file, 'w') as f:
            json.dump(ip_data, f, indent=2)
    except IOError as e:
        print(f"{Fore.RED}Failed to save IP history: {e}{Style.RESET_ALL}")


def update_ip_history(new_ip: str) -> Dict[str, Any]:
    """
    Update IP history with new IP address, shifting current to previous.
    
    Args:
        new_ip: The newly detected external IP address
        
    Returns:
        Updated IP history dictionary
    """
    current_timestamp = datetime.now().isoformat()
    ip_history = load_ip_history()
    
    # If this is a new IP (and not the first run), shift current to previous
    if ip_history["current_ip"] is not None and ip_history["current_ip"] != new_ip:
        ip_history["previous_ip"] = ip_history["current_ip"]
        ip_history["previous_timestamp"] = ip_history["current_timestamp"]
    
    # Always update current IP and timestamp
    ip_history["current_ip"] = new_ip
    ip_history["current_timestamp"] = current_timestamp
    
    save_ip_history(ip_history)
    return ip_history


def check_ip_change_status(current_ip: Optional[str] = None, silent: bool = False) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check if external IP address has changed since last check.
    
    Args:
        current_ip: Current external IP (will fetch if not provided)
        silent: Suppress console output if True
        
    Returns:
        Tuple of (changed, status_message, ip_history_data)
    """
    # Get current IP if not provided
    if current_ip is None:
        current_ip = get_public_ip()
        
        if current_ip == "Could not determine external IP (offline or no connectivity)":
            error_msg = "Cannot check IP change - unable to determine current external IP"
            if not silent:
                print(f"{Fore.RED}[FAIL] {error_msg}{Style.RESET_ALL}")
            return False, error_msg, {}
    
    # Load existing history
    ip_history = load_ip_history()
    
    # Check if this is the first run
    if ip_history["current_ip"] is None:
        updated_history = update_ip_history(current_ip)
        status_msg = f"Initial IP recorded: {current_ip}"
        if not silent:
            print(f"{Fore.GREEN}[INFO] {status_msg}{Style.RESET_ALL}")
        return False, status_msg, updated_history
    
    # Check if IP has changed
    if current_ip != ip_history["current_ip"]:
        updated_history = update_ip_history(current_ip)
        status_msg = f"IP changed from {ip_history['current_ip']} to {current_ip}"
        if not silent:
            print(f"{Fore.YELLOW}[CHANGED] {status_msg}{Style.RESET_ALL}")
            if ip_history["current_timestamp"]:
                prev_time = datetime.fromisoformat(ip_history["current_timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                print(f"{Fore.YELLOW}Previous IP was recorded at: {prev_time}{Style.RESET_ALL}")
        return True, status_msg, updated_history
    
    # IP has not changed - just update the timestamp
    updated_history = update_ip_history(current_ip)  # This will only update timestamp
    status_msg = f"IP unchanged: {current_ip}"
    if not silent:
        print(f"{Fore.GREEN}[OK] {status_msg}{Style.RESET_ALL}")
        if ip_history["current_timestamp"]:
            prev_time = datetime.fromisoformat(ip_history["current_timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            print(f"{Fore.GREEN}Last recorded at: {prev_time}{Style.RESET_ALL}")
    
    return False, status_msg, updated_history


def did_external_ip_change(current_external_ip: Optional[str] = None, silent: bool = False) -> str:
    """
    Legacy function name compatibility - check if external IP has changed.
    
    Args:
        current_external_ip: Current external IP (optional, will fetch if not provided)
        silent: Suppress console output if True
        
    Returns:
        String describing the IP change status
    """
    changed, message, _ = check_ip_change_status(current_external_ip, silent)
    return message


def monitor_external_ip_changes(silent: bool = False) -> Dict[str, Any]:
    """
    Monitor external IP address changes with comprehensive reporting.
    
    Args:
        silent: Suppress console output if True
        
    Returns:
        Dictionary containing IP change analysis and history
    """
    if not silent:
        print(f"{Fore.CYAN}External IP Change Monitoring{Style.RESET_ALL}")
    
    try:
        changed, message, history = check_ip_change_status(silent=silent)
        
        result = {
            "success": True,
            "changed": changed,
            "message": message,
            "current_ip": history.get("current_ip"),
            "current_timestamp": history.get("current_timestamp"),
            "previous_ip": history.get("previous_ip"),
            "previous_timestamp": history.get("previous_timestamp"),
            "config_file": str(get_config_file_path())
        }
        
        if not silent:
            print(f"\n{Fore.CYAN}IP History Summary:{Style.RESET_ALL}")
            print(f"Current IP: {result['current_ip']}")
            if result['current_timestamp']:
                current_time = datetime.fromisoformat(result['current_timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                print(f"Recorded at: {current_time}")
            
            if result['previous_ip']:
                print(f"Previous IP: {result['previous_ip']}")
                if result['previous_timestamp']:
                    prev_time = datetime.fromisoformat(result['previous_timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"Previous recorded at: {prev_time}")
        
        return result
        
    except Exception as e:
        error_msg = f"IP change monitoring failed: {str(e)}"
        if not silent:
            print(f"{Fore.RED}[ERROR] {error_msg}{Style.RESET_ALL}")
        
        return {
            "success": False,
            "error": error_msg,
            "changed": False,
            "message": error_msg
        }


def get_module_tools():
    """
    Get tool metadata for external IP change monitoring registration.
    
    Returns:
        Dictionary of tool metadata for tools registry integration
    """
    from core.tools_registry import ToolMetadata, ParameterInfo, ParameterType, ToolCategory
    
    return {
        "monitor_external_ip_changes": ToolMetadata(
            name="monitor_external_ip_changes",
            function_name="monitor_external_ip_changes",
            module_path="network_tools.check_if_external_ip_changed",
            description="Monitor external IP address changes with historical tracking",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "silent": ParameterInfo(
                    ParameterType.BOOLEAN,
                    default=False,
                    description="Suppress verbose console output"
                )
            },
            aliases=["ip_change_check", "external_ip_monitor", "check_ip_change"],
            examples=[
                "monitor_external_ip_changes",
                "monitor_external_ip_changes --silent"
            ]
        ),
        "did_external_ip_change": ToolMetadata(
            name="did_external_ip_change",
            function_name="did_external_ip_change",
            module_path="network_tools.check_if_external_ip_changed",
            description="Check if external IP has changed (legacy compatibility function)",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "current_external_ip": ParameterInfo(
                    ParameterType.STRING,
                    default=None,
                    description="Current external IP (optional, will fetch if not provided)"
                ),
                "silent": ParameterInfo(
                    ParameterType.BOOLEAN,
                    default=False,
                    description="Suppress console output"
                )
            },
            aliases=["check_external_ip_change"],
            examples=[
                "did_external_ip_change",
                "did_external_ip_change --current_external_ip 192.168.1.1"
            ]
        )
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Monitor external IP address changes",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "current_external_ip", 
        nargs='?',
        help="Current external IP address (optional, will fetch if not provided)"
    )
    parser.add_argument(
        "--silent", 
        action="store_true",
        help="Suppress verbose output"
    )
    
    args = parser.parse_args()
    
    # Use the modern function for comprehensive monitoring
    result = monitor_external_ip_changes(silent=args.silent)
    
    # Exit with appropriate code
    exit_code = 0 if result["success"] else 1
    exit(exit_code)