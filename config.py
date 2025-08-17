"""
Configuration constants and tool paths for Instability v3.

This file centralizes all configuration settings including tool paths,
timeout values, default target ranges, and memory file locations.
"""

import os
import platform
from typing import Dict, List

# Version information
VERSION = "3.0.0"
APP_NAME = "Instability"

# Ollama configuration
OLLAMA_DEFAULT_MODEL = "dolphin3"
OLLAMA_API_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 30

# Memory and cache settings
MEMORY_DIR = "memory"
NETWORK_STATE_FILE = os.path.join(MEMORY_DIR, "network_state.md")
TARGET_SCOPE_FILE = os.path.join(MEMORY_DIR, "target_scope.md")
SESSION_CACHE_FILE = os.path.join(MEMORY_DIR, "session_cache.json")

# Default target scope
DEFAULT_TARGET_SCOPE = "local network only"

# Network diagnostic timeouts (seconds)
PING_TIMEOUT = 5
DNS_TIMEOUT = 10
WEB_REQUEST_TIMEOUT = 15
TRACEROUTE_TIMEOUT = 30

# Tool detection settings
TOOL_DETECTION_TIMEOUT = 5

# MCP server authentication settings
MCP_AUTH_ENABLED = os.getenv("MCP_AUTH_ENABLED", "true").lower() == "true"
MCP_API_KEY = os.getenv("MCP_API_KEY", "")
MCP_AUTH_HEADER = "X-API-Key"

# Cross-platform tool paths for detection
# The system will check these paths in order and use the first found
TOOL_PATHS: Dict[str, List[str]] = {
    "nmap": [
        # Unix/Linux/macOS common paths
        "/usr/bin/nmap",
        "/usr/local/bin/nmap",
        "/opt/local/bin/nmap",
        "/snap/bin/nmap",
        # macOS Homebrew
        "/opt/homebrew/bin/nmap",
        "/usr/local/Cellar/nmap/*/bin/nmap",
        # Windows common paths
        "C:\\Program Files\\Nmap\\nmap.exe",
        "C:\\Program Files (x86)\\Nmap\\nmap.exe",
        "C:\\Tools\\nmap\\nmap.exe",
    ],
    "nuclei": [
        "/usr/bin/nuclei",
        "/usr/local/bin/nuclei",
        "/opt/local/bin/nuclei",
        "/snap/bin/nuclei",
        "/opt/homebrew/bin/nuclei",
        "C:\\Tools\\nuclei\\nuclei.exe",
        "C:\\Program Files\\nuclei\\nuclei.exe",
    ],
    "httpx": [
        "/usr/bin/httpx",
        "/usr/local/bin/httpx",
        "/opt/local/bin/httpx",
        "/snap/bin/httpx",
        "/opt/homebrew/bin/httpx",
        "C:\\Tools\\httpx\\httpx.exe",
        "C:\\Program Files\\httpx\\httpx.exe",
    ],
    "feroxbuster": [
        "/usr/bin/feroxbuster",
        "/usr/local/bin/feroxbuster",
        "/opt/local/bin/feroxbuster",
        "/snap/bin/feroxbuster",
        "/opt/homebrew/bin/feroxbuster",
        "C:\\Tools\\feroxbuster\\feroxbuster.exe",
        "C:\\Program Files\\feroxbuster\\feroxbuster.exe",
    ],
    "gobuster": [
        "/usr/bin/gobuster",
        "/usr/local/bin/gobuster",
        "/opt/local/bin/gobuster",
        "/snap/bin/gobuster",
        "/opt/homebrew/bin/gobuster",
        "C:\\Tools\\gobuster\\gobuster.exe",
        "C:\\Program Files\\gobuster\\gobuster.exe",
    ],
    "hydra": [
        "/usr/bin/hydra",
        "/usr/local/bin/hydra",
        "/opt/local/bin/hydra",
        "/snap/bin/hydra",
        "/opt/homebrew/bin/hydra",
        "C:\\Tools\\hydra\\hydra.exe",
        "C:\\Program Files\\hydra\\hydra.exe",
    ],
    "sqlmap": [
        "/usr/bin/sqlmap",
        "/usr/local/bin/sqlmap",
        "/opt/local/bin/sqlmap",
        "/snap/bin/sqlmap",
        "/opt/homebrew/bin/sqlmap",
        "C:\\Tools\\sqlmap\\sqlmap.py",
        "C:\\Program Files\\sqlmap\\sqlmap.py",
    ],
    "traceroute": [
        "/usr/bin/traceroute",
        "/usr/local/bin/traceroute",
        "/opt/local/bin/traceroute",
        "/bin/traceroute",
        "/sbin/traceroute",
    ] if platform.system() != "Windows" else [
        "C:\\Windows\\System32\\tracert.exe",
        "tracert.exe",
    ],
}

# Tool installation recommendations
TOOL_INSTALL_COMMANDS: Dict[str, Dict[str, str]] = {
    "nmap": {
        "linux": "sudo apt install nmap  # or: sudo yum install nmap",
        "darwin": "brew install nmap",
        "windows": "Download from https://nmap.org/download.html",
    },
    "nuclei": {
        "linux": "go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
        "darwin": "brew install nuclei",
        "windows": "go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest",
    },
    "httpx": {
        "linux": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
        "darwin": "brew install httpx",
        "windows": "go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest",
    },
    "feroxbuster": {
        "linux": "curl -sL https://raw.githubusercontent.com/epi052/feroxbuster/master/install-nix.sh | bash",
        "darwin": "brew install feroxbuster",
        "windows": "Download from https://github.com/epi052/feroxbuster/releases",
    },
    "gobuster": {
        "linux": "sudo apt install gobuster  # or: go install github.com/OJ/gobuster/v3@latest",
        "darwin": "brew install gobuster",
        "windows": "go install github.com/OJ/gobuster/v3@latest",
    },
    "hydra": {
        "linux": "sudo apt install hydra",
        "darwin": "brew install hydra",
        "windows": "Download from https://github.com/vanhauser-thc/thc-hydra",
    },
    "sqlmap": {
        "linux": "sudo apt install sqlmap  # or: git clone https://github.com/sqlmapproject/sqlmap.git",
        "darwin": "brew install sqlmap",
        "windows": "git clone https://github.com/sqlmapproject/sqlmap.git",
    },
}

# Terminal colors and formatting
COLORS = {
    "user_input": "\033[96m",      # Cyan
    "assistant": "\033[94m",       # Blue
    "tool_execution": "\033[92m",  # Green
    "error": "\033[91m",           # Red
    "thinking": "\033[90m",        # Grey
    "warning": "\033[93m",         # Yellow
    "reset": "\033[0m",            # Reset
}

# ASCII header file
ASCII_HEADER_FILE = "Instability_ASCII_Header_v3.txt"

# Startup check phases
STARTUP_PHASES = [
    "Core System Verification",
    "Internet Connectivity Assessment", 
    "Pentesting Tool Inventory",
    "Target Scope Configuration",
]

# Common DNS servers for testing
DNS_TEST_SERVERS = [
    "8.8.8.8",      # Google
    "1.1.1.1",      # Cloudflare
    "208.67.222.222",  # OpenDNS
]

# Common websites for connectivity testing
CONNECTIVITY_TEST_SITES = [
    "https://www.google.com",
    "https://www.cloudflare.com",
    "https://www.github.com",
]

# Extended Network Configuration
ADDITIONAL_DNS_SERVERS = [
    "9.9.9.9",      # Quad9
    "8.8.4.4",      # Google Secondary
    "1.0.0.1",      # Cloudflare Secondary
    "208.67.220.220", # OpenDNS Secondary
]

# Root DNS Servers (for comprehensive DNS testing)
ROOT_DNS_SERVERS = {
    "A": "198.41.0.4",      # VeriSign, Inc.
    "B": "199.9.14.201",    # University of Southern California
    "C": "192.33.4.12",     # Cogent Communications
    "D": "199.7.91.13",     # University of Maryland
    "E": "192.203.230.10",  # NASA Ames Research Center
    "F": "192.5.5.241",     # Internet Systems Consortium
    "G": "192.112.36.4",    # US Department of Defense NIC
    "H": "198.97.190.53",   # US Army Research Lab
    "I": "192.36.148.17",   # Netnod
    "J": "192.58.128.30",   # VeriSign, Inc.
    "K": "193.0.14.129",    # RIPE NCC
    "L": "199.7.83.42",     # ICANN
    "M": "202.12.27.33",    # WIDE Project
}

# Common Service Ports (prioritized by frequency of use)
COMMON_PORTS = "80,443,22,21,25,53,110,143,993,995"
TOP_TCP_PORTS = "22,23,25,53,80,110,111,135,139,143,443,993,995,1723,3306,3389,5432,5900,6001,8000,8080,8443,8888,10000"
TOP_UDP_PORTS = "53,67,68,69,123,161,162,500,514,520,631,1434,1900,4500,5353"

# Network Ranges and IP Configuration
DEFAULT_LOCAL_NETWORK = "192.168.1.0/24"
PRIVATE_NETWORK_RANGES = [
    "10.0.0.0/8",
    "172.16.0.0/12", 
    "192.168.0.0/16",
    "169.254.0.0/16",  # Link-local
    "127.0.0.0/8",     # Loopback
]

# External IP Detection Services (priority order - most reliable first)
IP_DETECTION_SERVICES = [
    "https://api.ipify.org?format=json",
    "https://ifconfig.me/ip", 
    "https://icanhazip.com",
    "https://ident.me",
    "https://checkip.amazonaws.com",
    "https://ipecho.net/plain",
    "https://myexternalip.com/raw"
]

# Tool-Specific Timeouts and Configuration
NMAP_TIMEOUTS = {
    "quick_scan": 60,
    "basic_scan": 300,
    "service_scan": 300,
    "os_detection": 180,
    "comprehensive": 600,
    "network_discovery": 120,
    "port_scan": 120,
    "stealth_scan": 900
}

NMAP_TIMING = {
    "paranoid": "T0",
    "sneaky": "T1", 
    "polite": "T2",
    "normal": "T3",
    "aggressive": "T4",
    "insane": "T5"
}

NMAP_DEFAULTS = {
    "timing_template": "T3",
    "max_hostgroup": 30,
    "max_parallelism": 10,
    "max_scan_delay": 10,
    "default_udp_ports": 100
}

# DNS Operation Configuration
DNS_CONFIG = {
    "resolver_timeout": 5,
    "resolver_lifetime": 5,
    "retry_delay": 5,
    "propagation_check": 10,
    "max_retries": 3,
    "record_types": ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "PTR", "SOA"]
}

# Web Request Configuration
WEB_REQUEST_CONFIG = {
    "user_agent": f"{APP_NAME}/{VERSION} (Network Diagnostics)",
    "content_preview_bytes": 500,
    "content_preview_display": 200,
    "ssl_verify": True,
    "allow_redirects": True,
    "max_redirects": 5,
    "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive"
    }
}

# Cache and Performance Configuration
CACHE_CONFIG = {
    "tool_result_ttl_minutes": 60,
    "session_cache_file": "session_cache.json",
    "temp_file_suffix": ".tmp",
    "max_cache_size_mb": 50,
    "cleanup_interval_hours": 24
}

PERFORMANCE_LIMITS = {
    "max_line_length": 2000,
    "max_interfaces_display": 5,
    "max_hops_display": 10,
    "max_processes": 4,
    "subprocess_timeout_default": 30,
    "max_output_lines": 1000
}

# Network Quality and Speed Test Configuration
NETWORK_QUALITY_CONFIG = {
    "timeout": 90,
    "test_duration": 10,
    "upload_test": True,
    "download_test": True,
    "latency_test": True
}

# Speed Test Thresholds (Mbps)
SPEED_THRESHOLDS = {
    "very_slow": 1,
    "slow": 10,
    "moderate": 25,
    "fast": 100,
    "very_fast": 500,
    "gigabit": 1000
}

# WHOIS Servers Configuration
WHOIS_SERVERS = {
    "default": [
        "whois.iana.org",
        "whois.verisign-grs.com",
        "whois.pir.org"
    ],
    "tld_specific": {
        ".com": "whois.verisign-grs.com",
        ".net": "whois.verisign-grs.com", 
        ".org": "whois.pir.org",
        ".uk": "whois.nic.uk",
        ".edu": "whois.educause.edu",
        ".gov": "whois.dotgov.gov"
    }
}

# Error Handling and Retry Configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay": 2,
    "exponential_backoff": True,
    "backoff_factor": 2.0,
    "jitter": True
}

ERROR_THRESHOLDS = {
    "high_abuse_score": 80,
    "medium_abuse_score": 20,
    "max_failed_dns_servers": 2,
    "min_successful_connectivity": 1,
    "max_ping_loss_percent": 50,
    "min_successful_hops": 3
}

# Security and Abuse Detection Configuration
SECURITY_CONFIG = {
    "abuseipdb_url": "https://api.abuseipdb.com/api/v2/check",
    "max_age_days": 90,
    "confidence_threshold": 75,
    "rate_limit_delay": 1
}

# Output and Display Configuration
DISPLAY_CONFIG = {
    "max_table_rows": 20,
    "truncate_long_output": True,
    "show_timestamps": False,
    "color_output": True,
    "progress_indicators": True,
    "verbose_errors": True
}

def get_platform_install_command(tool_name: str) -> str:
    """Get the installation command for a tool on the current platform."""
    system = platform.system().lower()
    if tool_name in TOOL_INSTALL_COMMANDS:
        return TOOL_INSTALL_COMMANDS[tool_name].get(system, "Tool installation instructions not available for this platform")
    return f"Installation instructions not available for {tool_name}"

def get_memory_dir() -> str:
    """Get the memory directory path, creating it if it doesn't exist."""
    if not os.path.exists(MEMORY_DIR):
        os.makedirs(MEMORY_DIR)
    return MEMORY_DIR

def get_timeout(operation: str, scan_type: str = "basic") -> int:
    """
    Get timeout value for a specific operation and scan type.
    
    Args:
        operation: Operation type (nmap, dns, web, ping, traceroute)
        scan_type: Specific scan type for the operation (basic, quick, comprehensive, etc.)
        
    Returns:
        Timeout value in seconds
    """
    timeout_maps = {
        "nmap": NMAP_TIMEOUTS,
        "dns": {
            "query": DNS_CONFIG["resolver_timeout"],
            "propagation": DNS_CONFIG["propagation_check"], 
            "lookup": DNS_TIMEOUT
        },
        "web": {
            "request": WEB_REQUEST_TIMEOUT,
            "quality": NETWORK_QUALITY_CONFIG["timeout"]
        },
        "ping": {"basic": PING_TIMEOUT},
        "traceroute": {"basic": TRACEROUTE_TIMEOUT}
    }
    
    if operation in timeout_maps:
        timeout_map = timeout_maps[operation]
        if isinstance(timeout_map, dict):
            return timeout_map.get(scan_type, timeout_map.get("basic", 30))
        else:
            return timeout_map
    
    return PERFORMANCE_LIMITS["subprocess_timeout_default"]

def get_dns_servers(include_additional: bool = False) -> List[str]:
    """
    Get list of DNS servers for testing.
    
    Args:
        include_additional: Whether to include additional DNS servers beyond the main test servers
        
    Returns:
        List of DNS server IP addresses
    """
    servers = DNS_TEST_SERVERS.copy()
    if include_additional:
        servers.extend(ADDITIONAL_DNS_SERVERS)
    return servers

def get_common_ports(port_type: str = "common") -> str:
    """
    Get common port specifications for scanning.
    
    Args:
        port_type: Type of ports ("common", "tcp", "udp")
        
    Returns:
        Port specification string
    """
    port_maps = {
        "common": COMMON_PORTS,
        "tcp": TOP_TCP_PORTS,
        "udp": TOP_UDP_PORTS
    }
    return port_maps.get(port_type, COMMON_PORTS)

def get_nmap_timing(timing_preference: str = "normal") -> str:
    """
    Get nmap timing template.
    
    Args:
        timing_preference: Timing preference (paranoid, sneaky, polite, normal, aggressive, insane)
        
    Returns:
        Nmap timing template string (e.g., "T3")
    """
    return NMAP_TIMING.get(timing_preference, NMAP_TIMING["normal"])

def get_web_headers() -> Dict[str, str]:
    """Get standard web request headers."""
    return WEB_REQUEST_CONFIG["headers"].copy()

def is_private_ip(ip: str) -> bool:
    """
    Check if an IP address is in private/reserved ranges.
    
    Args:
        ip: IP address to check
        
    Returns:
        True if IP is in private/reserved ranges
    """
    import ipaddress
    try:
        ip_obj = ipaddress.ip_address(ip)
        for range_str in PRIVATE_NETWORK_RANGES:
            if ip_obj in ipaddress.ip_network(range_str):
                return True
        return False
    except ValueError:
        return False

def get_speed_category(speed_mbps: float) -> str:
    """
    Categorize network speed.
    
    Args:
        speed_mbps: Speed in Mbps
        
    Returns:
        Speed category string
    """
    thresholds = SPEED_THRESHOLDS
    if speed_mbps >= thresholds["gigabit"]:
        return "gigabit"
    elif speed_mbps >= thresholds["very_fast"]:
        return "very_fast"
    elif speed_mbps >= thresholds["fast"]:
        return "fast"
    elif speed_mbps >= thresholds["moderate"]:
        return "moderate"
    elif speed_mbps >= thresholds["slow"]:
        return "slow"
    else:
        return "very_slow"

# NTP Configuration
NTP_DEFAULT_PORT = 123
NTP_DEFAULT_TIMEOUT = 5
NTP_DEFAULT_VERSION = 3
NTP_SYNC_THRESHOLD_MS = 100
NTP_MAX_PARALLEL_CHECKS = 10

# Well-known NTP servers organized by category
NTP_SERVERS = {
    "global_pool": [
        "pool.ntp.org",
        "0.pool.ntp.org",
        "1.pool.ntp.org", 
        "2.pool.ntp.org",
        "3.pool.ntp.org"
    ],
    "google": [
        "time.google.com",
        "time1.google.com",
        "time2.google.com",
        "time3.google.com",
        "time4.google.com"
    ],
    "microsoft": ["time.windows.com"],
    "apple": ["time.apple.com"],
    "cloudflare": ["time.cloudflare.com"],
    "nist": ["time.nist.gov"],
    "usno": [
        "tick.usno.navy.mil",
        "tock.usno.navy.mil", 
        "ntp2.usno.navy.mil"
    ],
    "regional": [
        "ca.pool.ntp.org",
        "us.pool.ntp.org", 
        "europe.pool.ntp.org",
        "time.euro.apple.com"
    ]
}

# Flatten all servers for default testing
NTP_DEFAULT_SERVERS = []
for category in NTP_SERVERS.values():
    NTP_DEFAULT_SERVERS.extend(category)

def get_ntp_servers(category: str = None) -> List[str]:
    """
    Get list of NTP servers by category or all servers.
    
    Args:
        category: Specific category of NTP servers (google, nist, usno, etc.) or None for all
        
    Returns:
        List of NTP server hostnames
    """
    if category and category in NTP_SERVERS:
        return NTP_SERVERS[category].copy()
    return NTP_DEFAULT_SERVERS.copy()

def get_ntp_timeout(operation: str = "basic") -> int:
    """
    Get timeout value for NTP operations.
    
    Args:
        operation: Operation type (basic, batch, sync_analysis)
        
    Returns:
        Timeout value in seconds
    """
    ntp_timeouts = {
        "basic": NTP_DEFAULT_TIMEOUT,
        "batch": NTP_DEFAULT_TIMEOUT * 2,
        "sync_analysis": NTP_DEFAULT_TIMEOUT * 3,
        "individual": NTP_DEFAULT_TIMEOUT
    }
    return ntp_timeouts.get(operation, NTP_DEFAULT_TIMEOUT)

def get_whois_server(domain: str) -> str:
    """
    Get appropriate WHOIS server for a domain.
    
    Args:
        domain: Domain name to look up
        
    Returns:
        WHOIS server address
    """
    # Extract TLD
    if '.' in domain:
        tld = '.' + domain.split('.')[-1].lower()
        return WHOIS_SERVERS["tld_specific"].get(tld, WHOIS_SERVERS["default"][0])
    
    return WHOIS_SERVERS["default"][0]