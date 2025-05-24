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
OLLAMA_DEFAULT_MODEL = "phi3:14b"
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