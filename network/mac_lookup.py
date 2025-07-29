"""
MAC address manufacturer lookup tools for Instability v3.

Provides offline MAC address manufacturer identification using Wireshark's
manufacturer database with automatic updates and fallback mechanisms.
"""

import gzip
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

import requests
from colorama import Fore, Style

from core.error_handling import (
    create_error_response, ErrorType, ErrorCode,
    create_network_error, create_system_error, create_input_error
)


def fetch_latest_wireshark_manuf_file(silent: bool = False) -> Dict[str, Any]:
    """
    Download the latest Wireshark manufacturer database for offline MAC lookup.
    
    Downloads from official Wireshark sources and stores locally for subsequent
    offline lookups. Attempts gzipped download first, then uncompressed fallback.
    
    Args:
        silent: If True, suppress output except errors
        
    Returns:
        Standardized result dictionary
    """
    start_time = datetime.now()
    
    # URL configuration
    primary_url = "https://www.wireshark.org/download/automated/data/manuf.gz"
    fallback_url = "https://www.wireshark.org/download/automated/data/manuf" 
    
    # Local storage path - use user's home directory for MCP compatibility
    from pathlib import Path
    import os
    
    # Try project directory first, fallback to user config directory
    try:
        local_path = Path("data/manuf")
        local_path.parent.mkdir(parents=True, exist_ok=True)
        # Test write access
        test_file = local_path.parent / ".write_test"
        test_file.touch()
        test_file.unlink()
    except (PermissionError, OSError):
        # Fallback to user config directory for MCP server compatibility
        config_dir = Path.home() / ".config" / "instability"
        config_dir.mkdir(parents=True, exist_ok=True)
        local_path = config_dir / "manuf"
    
    try:
        # First, ask for user consent
        if not silent:
            print(f"{Fore.YELLOW}This will download the latest Wireshark manufacturer database from:{Style.RESET_ALL}")
            print(f"Primary: {primary_url}")
            print(f"Fallback: {fallback_url}")
            
            consent = input(f"{Fore.CYAN}Proceed with download? (y/N): {Style.RESET_ALL}").strip().lower()
            if consent not in ['y', 'yes']:
                return {
                    "success": False,
                    "exit_code": 1,
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "timestamp": start_time.isoformat(),
                    "tool_name": "fetch_latest_wireshark_manuf_file",
                    "command_executed": "fetch_latest_wireshark_manuf_file()",
                    "stdout": "",
                    "stderr": "User declined download",
                    "parsed_data": {},
                    "error_type": "user_cancelled",
                    "error_message": "User declined to download manufacturer database",
                    "target": None,
                    "options_used": {"silent": silent}
                }
        
        # Try downloading gzipped version first
        success = False
        for url in [primary_url, fallback_url]:
            try:
                if not silent:
                    print(f"Downloading from {url}...")
                
                headers = {'User-Agent': 'Instability-Network-Tool/3.0'}
                response = requests.get(url, headers=headers, timeout=30, stream=True)
                response.raise_for_status()
                
                # Download to temporary file first
                temp_path = local_path.with_suffix('.tmp')
                
                # Show progress if not silent
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if not silent and total_size > 0:
                                percent = (downloaded / total_size) * 100
                                print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
                
                if not silent and total_size > 0:
                    print()  # New line after progress
                
                # Handle gzipped content
                if url.endswith('.gz'):
                    if not silent:
                        print("Decompressing gzipped file...")
                    with gzip.open(temp_path, 'rb') as f_in:
                        with open(local_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    temp_path.unlink()  # Remove temporary gzipped file
                else:
                    # Move uncompressed file to final location
                    temp_path.rename(local_path)
                
                success = True
                break
                
            except requests.RequestException as e:
                if not silent:
                    print(f"{Fore.RED}Failed to download from {url}: {e}{Style.RESET_ALL}")
                continue
        
        if not success:
            # Try tshark fallback
            return _try_tshark_fallback(start_time, local_path, silent)
        
        # Verify file was downloaded successfully
        if not local_path.exists() or local_path.stat().st_size == 0:
            return create_system_error(
                ErrorCode.FILE_NOT_FOUND,
                tool_name="fetch_latest_wireshark_manuf_file",
                execution_time=(datetime.now() - start_time).total_seconds(),
                details={"local_path": str(local_path)}
            )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        file_size = local_path.stat().st_size
        
        if not silent:
            print(f"{Fore.GREEN}Successfully downloaded manufacturer database{Style.RESET_ALL}")
            print(f"File: {local_path}")
            print(f"Size: {file_size:,} bytes")
            print(f"Last modified: {datetime.fromtimestamp(local_path.stat().st_mtime)}")
        
        return {
            "success": True,
            "exit_code": 0,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "tool_name": "fetch_latest_wireshark_manuf_file",
            "command_executed": "fetch_latest_wireshark_manuf_file()",
            "stdout": f"Downloaded manufacturer database to {local_path}",
            "stderr": "",
            "parsed_data": {
                "file_path": str(local_path),
                "file_size": file_size,
                "download_source": "wireshark.org",
                "last_modified": datetime.fromtimestamp(local_path.stat().st_mtime).isoformat()
            },
            "error_type": None,
            "error_message": None,
            "target": None,
            "options_used": {"silent": silent}
        }
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"Download failed: {str(e)}"
        
        if not silent:
            print(f"{Fore.RED}Error: {error_msg}{Style.RESET_ALL}")
        
        return create_system_error(
            ErrorCode.COMMAND_FAILED,
            tool_name="fetch_latest_wireshark_manuf_file",
            execution_time=execution_time,
            details={"error": str(e), "options": {"silent": silent}}
        )


def mac_address_manufacturer_lookup(mac_address: str, silent: bool = False) -> Dict[str, Any]:
    """
    Perform offline MAC address manufacturer identification.
    
    Supports multiple MAC address input formats and returns comprehensive
    manufacturer information when available. Uses locally stored Wireshark
    manufacturer database.
    
    Args:
        mac_address: MAC address in various formats (AA:BB:CC, AA-BB-CC, etc.)
        silent: If True, suppress output except errors
        
    Returns:
        Standardized result dictionary
    """
    start_time = datetime.now()
    
    try:
        # Normalize MAC address
        normalized_mac = _normalize_mac_address(mac_address)
        if not normalized_mac:
            return create_input_error(
                ErrorCode.INVALID_TARGET,
                tool_name="mac_address_manufacturer_lookup",
                execution_time=(datetime.now() - start_time).total_seconds(),
                details={"mac_address": mac_address},
                target=mac_address
            )
        
        # Check if manufacturer database exists - try both locations
        local_path = Path("data/manuf")
        if not local_path.exists():
            # Try user config directory
            config_path = Path.home() / ".config" / "instability" / "manuf"
            if config_path.exists():
                local_path = config_path
            else:
                if not silent:
                    print(f"{Fore.YELLOW}Manufacturer database not found locally.{Style.RESET_ALL}")
                    print("You can fetch it using: fetch_latest_wireshark_manuf_file")
                
                return create_system_error(
                    ErrorCode.FILE_NOT_FOUND,
                    tool_name="mac_address_manufacturer_lookup",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    details={"expected_path": str(local_path), "mac_address": mac_address},
                    target=mac_address
                )
        
        # Check file age and warn if older than 7 days
        file_age = datetime.now() - datetime.fromtimestamp(local_path.stat().st_mtime)
        if file_age > timedelta(days=7):
            if not silent:
                print(f"{Fore.YELLOW}Warning: Manufacturer database is {file_age.days} days old{Style.RESET_ALL}")
                print("Consider updating with: fetch_latest_wireshark_manuf_file")
        
        # Extract OUI (first 24 bits / 6 hex characters)
        oui = normalized_mac[:6].upper()
        
        # Search manufacturer database
        manufacturer_info = _search_manufacturer_database(local_path, oui)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if manufacturer_info:
            if not silent:
                print(f"MAC: {mac_address}")
                print(f"OUI: {oui}")
                print(f"Manufacturer: {manufacturer_info['manufacturer']}")
                if manufacturer_info.get('comment'):
                    print(f"Comment: {manufacturer_info['comment']}")
            
            return {
                "success": True,
                "exit_code": 0,
                "execution_time": execution_time,
                "timestamp": start_time.isoformat(),
                "tool_name": "mac_address_manufacturer_lookup",
                "command_executed": f"mac_address_manufacturer_lookup({mac_address})",
                "stdout": f"Manufacturer: {manufacturer_info['manufacturer']}",
                "stderr": "",
                "parsed_data": {
                    "input_mac": mac_address,
                    "normalized_mac": normalized_mac,
                    "oui": oui,
                    "manufacturer": manufacturer_info['manufacturer'],
                    "comment": manufacturer_info.get('comment', ''),
                    "database_age_days": file_age.days
                },
                "error_type": None,
                "error_message": None,
                "target": mac_address,
                "options_used": {"silent": silent}
            }
        else:
            if not silent:
                print(f"MAC: {mac_address}")
                print(f"OUI: {oui}")
                print(f"{Fore.YELLOW}Manufacturer: Unknown{Style.RESET_ALL}")
            
            return {
                "success": True,
                "exit_code": 0,
                "execution_time": execution_time,
                "timestamp": start_time.isoformat(),
                "tool_name": "mac_address_manufacturer_lookup",
                "command_executed": f"mac_address_manufacturer_lookup({mac_address})",
                "stdout": "Manufacturer: Unknown",
                "stderr": "",
                "parsed_data": {
                    "input_mac": mac_address,
                    "normalized_mac": normalized_mac,
                    "oui": oui,
                    "manufacturer": "Unknown",
                    "comment": "",
                    "database_age_days": file_age.days
                },
                "error_type": None,
                "error_message": None,
                "target": mac_address,
                "options_used": {"silent": silent}
            }
            
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = f"MAC lookup failed: {str(e)}"
        
        if not silent:
            print(f"{Fore.RED}Error: {error_msg}{Style.RESET_ALL}")
        
        return create_system_error(
            ErrorCode.COMMAND_FAILED,
            tool_name="mac_address_manufacturer_lookup",
            execution_time=execution_time,
            details={"error": str(e), "mac_address": mac_address},
            target=mac_address
        )


def _normalize_mac_address(mac_address: str) -> Optional[str]:
    """
    Normalize MAC address to standard format (remove separators, uppercase).
    
    Supports formats:
    - AA:BB:CC:DD:EE:FF
    - AA-BB-CC-DD-EE-FF
    - AABB.CCDD.EEFF
    - AABBCCDDEEFF
    """
    if not mac_address:
        return None
    
    # Remove all separators and whitespace
    clean_mac = re.sub(r'[:\-\.\s]', '', mac_address.strip())
    
    # Validate length and hex characters
    if len(clean_mac) != 12:
        return None
    
    if not re.match(r'^[0-9A-Fa-f]{12}$', clean_mac):
        return None
    
    return clean_mac.upper()


def _search_manufacturer_database(db_path: Path, oui: str) -> Optional[Dict[str, str]]:
    """
    Search the Wireshark manufacturer database for OUI information.
    
    Args:
        db_path: Path to manufacturer database file
        oui: 6-character OUI string (uppercase hex)
        
    Returns:
        Dictionary with manufacturer info or None if not found
    """
    try:
        with open(db_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse line format: OUI\tManufacturer\t[Comment]
                parts = line.split('\t')
                if len(parts) < 2:
                    continue
                
                db_oui = parts[0].replace(':', '').replace('-', '').strip().upper()
                
                # Check for exact match or prefix match
                if oui.startswith(db_oui) or db_oui.startswith(oui[:len(db_oui)]):
                    manufacturer = parts[1].strip()
                    comment = parts[2].strip() if len(parts) > 2 else ''
                    
                    return {
                        'manufacturer': manufacturer,
                        'comment': comment,
                        'oui_match': db_oui
                    }
    
    except Exception:
        pass
    
    return None


def _try_tshark_fallback(start_time: datetime, local_path: Path, silent: bool) -> Dict[str, Any]:
    """
    Try to generate manufacturer database using tshark as fallback.
    
    Args:
        start_time: Tool start time for timing calculations
        local_path: Path where to save the database
        silent: Whether to suppress output
        
    Returns:
        Standardized result dictionary
    """
    try:
        # Check if tshark is available
        result = subprocess.run(['which', 'tshark'], capture_output=True, text=True)
        if result.returncode != 0:
            # Try alternative check
            result = subprocess.run(['tshark', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                return create_system_error(
                    ErrorCode.TOOL_MISSING,
                    tool_name="fetch_latest_wireshark_manuf_file",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    details={"fallback": "tshark not available"},
                    tool="tshark"
                )
        
        if not silent:
            print(f"{Fore.YELLOW}Internet download failed. Trying tshark fallback...{Style.RESET_ALL}")
            consent = input(f"{Fore.CYAN}Generate manufacturer database using local tshark? (y/N): {Style.RESET_ALL}").strip().lower()
            if consent not in ['y', 'yes']:
                return create_system_error(
                    ErrorCode.USER_CANCELLED,
                    tool_name="fetch_latest_wireshark_manuf_file",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    details={"fallback": "user declined tshark"}
                )
        
        # Run tshark to generate manufacturer data
        if not silent:
            print("Generating manufacturer database with tshark...")
        
        result = subprocess.run(['tshark', '-G', 'manuf'], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and result.stdout:
            # Save output to file
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            file_size = local_path.stat().st_size
            
            if not silent:
                print(f"{Fore.GREEN}Successfully generated manufacturer database using tshark{Style.RESET_ALL}")
                print(f"File: {local_path}")
                print(f"Size: {file_size:,} bytes")
            
            return {
                "success": True,
                "exit_code": 0,
                "execution_time": execution_time,
                "timestamp": start_time.isoformat(),
                "tool_name": "fetch_latest_wireshark_manuf_file",
                "command_executed": "tshark -G manuf",
                "stdout": f"Generated manufacturer database using tshark: {local_path}",
                "stderr": "",
                "parsed_data": {
                    "file_path": str(local_path),
                    "file_size": file_size,
                    "download_source": "tshark",
                    "last_modified": datetime.fromtimestamp(local_path.stat().st_mtime).isoformat()
                },
                "error_type": None,
                "error_message": None,
                "target": None,
                "options_used": {"silent": silent, "fallback": "tshark"}
            }
        else:
            return create_system_error(
                ErrorCode.COMMAND_FAILED,
                tool_name="fetch_latest_wireshark_manuf_file",
                execution_time=(datetime.now() - start_time).total_seconds(),
                details={"tshark_error": result.stderr, "fallback": "tshark failed"}
            )
            
    except subprocess.TimeoutExpired:
        return create_system_error(
            ErrorCode.TIMEOUT,
            tool_name="fetch_latest_wireshark_manuf_file", 
            execution_time=(datetime.now() - start_time).total_seconds(),
            details={"fallback": "tshark timeout"}
        )
    except Exception as e:
        return create_system_error(
            ErrorCode.COMMAND_FAILED,
            tool_name="fetch_latest_wireshark_manuf_file",
            execution_time=(datetime.now() - start_time).total_seconds(),
            details={"fallback_error": str(e)}
        )


def get_module_tools():
    """Get tool metadata for functions in this module."""
    from core.tools_registry import ToolMetadata, ParameterInfo, ParameterType, ToolCategory
    
    return {
        "fetch_latest_wireshark_manuf_file": ToolMetadata(
            name="fetch_latest_wireshark_manuf_file",
            function_name="fetch_latest_wireshark_manuf_file", 
            module_path="network.mac_lookup",
            description="Download the latest Wireshark manufacturer database for offline MAC lookup",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "silent": ParameterInfo(ParameterType.BOOLEAN, default=False, description="If True, suppress output except errors")
            },
            modes=["manual", "chatbot"],
            examples=["fetch_latest_wireshark_manuf_file", "fetch_latest_wireshark_manuf_file silent=true"],
            function_ref=fetch_latest_wireshark_manuf_file
        ),
        "mac_address_manufacturer_lookup": ToolMetadata(
            name="mac_address_manufacturer_lookup",
            function_name="mac_address_manufacturer_lookup",
            module_path="network.mac_lookup", 
            description="Perform offline MAC address manufacturer identification",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "mac_address": ParameterInfo(ParameterType.STRING, required=True, description="MAC address in various formats (AA:BB:CC, AA-BB-CC, etc.)"),
                "silent": ParameterInfo(ParameterType.BOOLEAN, default=False, description="If True, suppress output except errors")
            },
            modes=["manual", "chatbot"],
            aliases=["mac_lookup", "lookup_mac"],
            examples=["mac_address_manufacturer_lookup AA:BB:CC:DD:EE:FF", "mac_lookup aa-bb-cc-dd-ee-ff"],
            function_ref=mac_address_manufacturer_lookup
        )
    }


if __name__ == "__main__":
    # Test functions
    print("Testing MAC lookup tools...")
    
    # Test MAC normalization
    test_macs = [
        "AA:BB:CC:DD:EE:FF",
        "aa-bb-cc-dd-ee-ff", 
        "AABB.CCDD.EEFF",
        "aabbccddeeff",
        "invalid"
    ]
    
    for mac in test_macs:
        normalized = _normalize_mac_address(mac)
        print(f"{mac} -> {normalized}")