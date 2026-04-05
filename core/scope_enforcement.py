"""
Scope enforcement for Instability v3.

Loads the target scope from memory/target_scope.md and validates that
tool targets fall within the authorized engagement scope before execution.

Scope types understood:
  - "local network only"  : only RFC-1918 / loopback / link-local addresses
  - CIDR list             : any ranges listed under "## In-Scope Targets"
"""

import ipaddress
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import TARGET_SCOPE_FILE, PRIVATE_NETWORK_RANGES


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def load_scope_config() -> Dict:
    """
    Parse target_scope.md and return a structured scope configuration.

    Returns:
        Dict with keys:
            scope_type  : str  - raw scope type string from the file header
            cidr_ranges : list - explicit CIDR ranges extracted from the doc
            local_only  : bool - True when scope_type is "local network only"
            loaded      : bool - False if the file could not be read
    """
    config = {
        "scope_type": "local network only",
        "cidr_ranges": [],
        "local_only": True,
        "loaded": False,
    }

    try:
        scope_text = Path(TARGET_SCOPE_FILE).read_text()
        config["loaded"] = True

        # Extract scope type from metadata line e.g. "*Scope type: local network only*"
        scope_type_match = re.search(r'\*Scope type:\s*(.+?)\*', scope_text)
        if scope_type_match:
            config["scope_type"] = scope_type_match.group(1).strip().lower()

        config["local_only"] = "local network only" in config["scope_type"]

        # Extract any explicit CIDR ranges (e.g. "192.168.1.0/24")
        cidr_pattern = re.compile(
            r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
            r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)'
            r'/(?:[0-9]|[12]\d|3[0-2])\b'
        )
        config["cidr_ranges"] = cidr_pattern.findall(scope_text)

    except (FileNotFoundError, PermissionError):
        # File missing or unreadable - default to local-only as safe fallback
        pass

    return config


def _is_private_address(target: str) -> Tuple[bool, Optional[str]]:
    """
    Check whether a target resolves to a private / loopback / link-local address.

    Args:
        target: IP address or CIDR string.

    Returns:
        Tuple of (is_private, canonical_form).  canonical_form is None on parse
        failure.
    """
    try:
        # Try as a plain IP first
        addr = ipaddress.ip_address(target)
        return addr.is_private or addr.is_loopback or addr.is_link_local, str(addr)
    except ValueError:
        pass

    try:
        # Try as a network (CIDR)
        net = ipaddress.ip_network(target, strict=False)
        private = net.is_private or net.is_loopback or net.is_link_local
        return private, str(net)
    except ValueError:
        return False, None


def _is_in_cidr_list(target: str, cidr_ranges: List[str]) -> bool:
    """
    Return True if *target* falls within any of *cidr_ranges*.

    Args:
        target     : IP address string.
        cidr_ranges: List of CIDR strings.
    """
    try:
        addr = ipaddress.ip_address(target)
        for cidr in cidr_ranges:
            try:
                if addr in ipaddress.ip_network(cidr, strict=False):
                    return True
            except ValueError:
                continue
    except ValueError:
        pass
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_target_in_scope(target: str, scope_config: Optional[Dict] = None) -> Tuple[bool, str]:
    """
    Determine whether *target* is within the authorized engagement scope.

    Hostnames that cannot be resolved to an IP are allowed through with a
    warning (conservative: we cannot check without a DNS lookup, and the
    tool itself will validate reachability).

    Args:
        target      : IP address, CIDR, or hostname to check.
        scope_config: Pre-loaded scope config dict (from load_scope_config()).
                      Loaded fresh if not supplied.

    Returns:
        Tuple of (in_scope: bool, reason: str).
    """
    if scope_config is None:
        scope_config = load_scope_config()

    # Hostnames: cannot determine scope without resolution - pass through
    ip_pattern = re.compile(
        r'^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
        r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)(?:/\d{1,2})?$'
    )
    if not ip_pattern.match(target):
        return True, f"Hostname '{target}' passed through scope check (resolve-time validation)"

    # --- Explicit CIDR allowlist takes priority over local-only mode ---
    if scope_config["cidr_ranges"]:
        if _is_in_cidr_list(target, scope_config["cidr_ranges"]):
            return True, f"Target '{target}' is within authorized CIDR range"
        return False, (
            f"Target '{target}' is outside the authorized scope. "
            f"Authorized ranges: {', '.join(scope_config['cidr_ranges'])}"
        )

    # --- Local-only mode ---
    if scope_config["local_only"]:
        is_private, canonical = _is_private_address(target)
        if is_private:
            return True, f"Target '{target}' is within private/local address space"
        return False, (
            f"Target '{target}' is a public/external address and the current "
            f"scope is 'local network only'. Update target_scope.md to authorize "
            f"external targets."
        )

    # Scope type not recognized - deny by default (fail secure)
    return False, (
        f"Scope type '{scope_config['scope_type']}' is not recognized. "
        f"Update target_scope.md with a supported scope type or explicit CIDR ranges."
    )


def get_scope_summary() -> str:
    """
    Return a human-readable one-line summary of the current scope configuration.

    Returns:
        String description of active scope.
    """
    config = load_scope_config()
    if not config["loaded"]:
        return "Scope: unknown (target_scope.md not found - defaulting to local network only)"
    if config["cidr_ranges"]:
        return f"Scope: explicit ranges {', '.join(config['cidr_ranges'])}"
    if config["local_only"]:
        return "Scope: local network only (RFC-1918 / loopback / link-local)"
    return f"Scope: {config['scope_type']}"
