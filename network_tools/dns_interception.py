"""DNS interception detection and unprivileged ICMP reachability.

A macOS DNS proxy network extension -- Tailscale's, a corporate VPN client, a
captive portal -- captures DNS flows system-wide at the flow level, so a query
addressed to ANY IP on port 53 is answered locally. Every port-53 reachability
check on such a host therefore reports success unconditionally, including for
servers that are completely unreachable.

This module provides the two signals the DNS tools need in order to tell the
difference: a runtime negative control that detects the condition, and an ICMP
probe that is not intercepted and can stand in as a weaker claim.

Full design and the measurements behind it: docs/dns_interception_srd.md.
"""

import os
import socket
import struct
import time
from typing import Optional, Tuple

import dns.exception
import dns.message
import dns.query
from colorama import Fore, Style

from config import (
    DNS_INTERCEPTION_PROBE_ADDRESS,
    DNS_INTERCEPTION_PROBE_NAME,
    DNS_INTERCEPTION_PROBE_TIMEOUT,
    ICMP_PROBE_ATTEMPTS,
    ICMP_PROBE_TIMEOUT,
)

# Result states. UNKNOWN is the reason this module exists: it is what a check
# must report when no trustworthy signal was available, and it must never be
# folded into either of the other two.
REACHABLE = "REACHABLE"
UNREACHABLE = "UNREACHABLE"
UNKNOWN = "UNKNOWN"

# The probe is stable for the life of a process and costs a full timeout on a
# clean host, so it is answered once.
_interception_cache: Optional[bool] = None

# Carried in the ICMP payload so a reply can be told apart from an unrelated
# packet arriving on the same socket.
_ICMP_MAGIC = b"instability-reach"


def dns_interception_detected(force: bool = False) -> Optional[bool]:
    """Detect whether DNS on this host is being intercepted.

    Sends one A query to a reserved, unroutable address. Nothing can legitimately
    answer from there, so any response at all proves a local proxy is answering
    on behalf of every destination -- which means no port-53 reachability check
    on this host can be trusted.

    Args:
        force: Re-probe instead of using the per-process cached answer.

    Returns:
        True if DNS is intercepted, False if it appears clean, or None if the
        probe could not be carried out. None means "cannot verify" and callers
        must treat it the same way they treat True: as grounds to withhold a
        pass, never as an all-clear.
    """
    global _interception_cache
    if _interception_cache is not None and not force:
        return _interception_cache

    query = dns.message.make_query(DNS_INTERCEPTION_PROBE_NAME, "A")
    try:
        dns.query.udp(query, DNS_INTERCEPTION_PROBE_ADDRESS,
                      timeout=DNS_INTERCEPTION_PROBE_TIMEOUT)
    except dns.exception.Timeout:
        # The expected result on a healthy host: the packet went out and nothing
        # came back, because nothing is there.
        _interception_cache = False
        return False
    except OSError:
        # No route, or the network is down entirely. That is not evidence either
        # way about interception.
        return None
    except dns.exception.DNSException:
        # A malformed or unexpected response is still a response, and nothing
        # should be responding at all.
        _interception_cache = True
        return True
    else:
        _interception_cache = True
        return True


def interception_notice() -> str:
    """One line explaining why a DNS-based check could not be trusted."""
    return (f"DNS on this host is being intercepted: a query to "
            f"{DNS_INTERCEPTION_PROBE_ADDRESS} (reserved, unroutable) was "
            f"answered. A DNS proxy is replying for every destination, so "
            f"port 53 reachability cannot be tested from here.")


def _checksum(data: bytes) -> int:
    """The standard internet checksum over an ICMP message."""
    if len(data) % 2:
        data += b"\x00"
    total = 0
    for index in range(0, len(data), 2):
        total += (data[index] << 8) + data[index + 1]
    total = (total >> 16) + (total & 0xFFFF)
    return ~(total + (total >> 16)) & 0xFFFF


def _is_echo_reply(packet: bytes) -> bool:
    """Whether a received packet is an echo reply to one of our own probes.

    Load-bearing, and not defensive tidiness. A first version of this probe
    counted any received ICMP packet as a reply, so a router's
    destination-unreachable for the unroutable test address read as a 2310 ms
    success. Only an echo reply (type 0) carrying our payload counts.

    macOS may or may not prepend the IP header on a SOCK_DGRAM ICMP socket, so
    both offsets are tried.

    Args:
        packet: The bytes returned by recvfrom.

    Returns:
        True only for a genuine echo reply to one of our probes.
    """
    for offset in (0, 20):
        if len(packet) < offset + 8:
            continue
        if packet[offset] == 0 and _ICMP_MAGIC in packet[offset:]:
            return True
    return False


def icmp_reachable(host: str, timeout: int = None,
                   attempts: int = None) -> Tuple[bool, Optional[float]]:
    """Whether a host answers an ICMP echo request, and how quickly.

    Unprivileged: macOS allows SOCK_DGRAM with IPPROTO_ICMP without root, which
    is what lets this run from the same process as everything else.

    This proves a host is reachable. It does NOT prove the host is serving DNS,
    and a caller must not present it as though it did. Note also that some hosts
    legitimately drop ICMP -- G-root and L-root both do -- so a False here means
    "did not answer a ping", never "down".

    Args:
        host: The IP address to probe.
        timeout: Seconds to wait per attempt.
        attempts: How many echo requests to send before giving up.

    Returns:
        (answered, round_trip_ms). round_trip_ms is None when answered is False.
    """
    timeout = ICMP_PROBE_TIMEOUT if timeout is None else timeout
    attempts = ICMP_PROBE_ATTEMPTS if attempts is None else attempts

    for sequence in range(1, attempts + 1):
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                  socket.IPPROTO_ICMP)
        except (PermissionError, OSError):
            # A platform that requires root for this. Skipping is correct: the
            # caller falls back to reporting UNKNOWN rather than guessing.
            return False, None

        identifier = os.getpid() & 0xFFFF
        body = struct.pack("!BBHHH", 8, 0, 0, identifier, sequence) + _ICMP_MAGIC
        packet = (struct.pack("!BBHHH", 8, 0, _checksum(body), identifier,
                              sequence) + _ICMP_MAGIC)
        deadline = time.monotonic() + timeout
        try:
            start = time.monotonic()
            probe.sendto(packet, (host, 0))
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                probe.settimeout(remaining)
                try:
                    data, address = probe.recvfrom(2048)
                except socket.timeout:
                    break
                # Keep waiting on anything that is not our reply from our host,
                # rather than accepting the first packet that arrives.
                if address[0] == host and _is_echo_reply(data):
                    return True, (time.monotonic() - start) * 1000
        except OSError:
            pass
        finally:
            probe.close()

    return False, None


def describe_icmp_result(name: str, host: str, answered: bool,
                         round_trip_ms: Optional[float]) -> str:
    """One console line for an ICMP probe, in the repository's output style."""
    if answered:
        return (f"{Fore.GREEN} - {name} ({host}) answered a ping in "
                f"{round_trip_ms:.1f} ms{Style.RESET_ALL}")
    return (f"{Fore.YELLOW} - {name} ({host}) did not answer a ping "
            f"(some servers drop ICMP; this is not proof it is down)"
            f"{Style.RESET_ALL}")


def get_module_tools():
    """Expose nothing from this module as a runnable tool.

    The registry uses this function when a module defines it and never falls
    back to scanning for public functions, so declaring an empty mapping here
    keeps these helpers out of the tool list without adding four more names to
    the central exclusion set in core/tools_registry.py.

    That matters beyond tidiness: these are the signals the DNS tools use to
    decide whether their own results can be trusted, not diagnostics in their
    own right. Exposing them would invite a caller to run the probe on its own
    and read an interception verdict as though it were a network check.

    Returns:
        An empty dict.
    """
    return {}
