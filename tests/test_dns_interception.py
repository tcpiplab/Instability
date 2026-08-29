#!/usr/bin/env python3
"""
Test script for DNS interception detection and the checks that depend on it

A macOS DNS proxy network extension captures DNS flows system-wide, so a query
addressed to any IP on port 53 is answered locally. Three tools reported success
unconditionally as a result. These tests cover the properties that keep the
fixed versions honest.

Offline: every network call is stubbed. See docs/dns_interception_srd.md.
"""

import os
import struct
import sys

import dns.exception
from colorama import Fore, Style, init

init(autoreset=True)

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from network_tools import dns_check, dns_interception, resolver_check

FAILURES = []


def check(condition, label):
    if condition:
        print(f"{Fore.GREEN}  [PASS] {label}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}  [FAIL] {label}{Style.RESET_ALL}")
        FAILURES.append(label)


def _echo_reply(magic=dns_interception._ICMP_MAGIC, icmp_type=0):
    return struct.pack("!BBHHH", icmp_type, 0, 0, 1234, 1) + magic


def test_interception_detection():
    """A response from a reserved, unroutable address can only be a proxy."""
    print("Detection:")
    saved = dns_interception.dns.query.udp

    dns_interception._interception_cache = None
    dns_interception.dns.query.udp = lambda *a, **k: "a response"
    check(dns_interception.dns_interception_detected(force=True) is True,
          "a response from the unroutable probe address means intercepted")

    dns_interception._interception_cache = None
    def timeout(*args, **kwargs):
        raise dns.exception.Timeout("no answer")
    dns_interception.dns.query.udp = timeout
    check(dns_interception.dns_interception_detected(force=True) is False,
          "a timeout from the probe address means clean")

    dns_interception._interception_cache = None
    def unreachable(*args, **kwargs):
        raise OSError("network is down")
    dns_interception.dns.query.udp = unreachable
    check(dns_interception.dns_interception_detected(force=True) is None,
          "a probe that could not run returns None, not False")

    dns_interception.dns.query.udp = saved
    dns_interception._interception_cache = None


def test_unknown_is_never_an_all_clear():
    """The single property this whole change exists to guarantee."""
    print("No false all-clear:")
    unknown = ["- A (198.41.0.4) - DNS not testable here; answers a ping in 12 ms"]
    report = dns_check.generate_dns_report([], [], unknown)
    check("All DNS Root Servers are reachable" not in report,
          "a report with unknowns never claims all root servers reachable")
    check("could not be determined" in report,
          "it says the reachability could not be determined")
    check("intercepted" in report,
          "and it says why")

    mixed = dns_check.generate_dns_report(["- B (199.9.14.201)"], [], unknown)
    check("All DNS Root Servers are reachable" not in mixed,
          "a partly-unknown report does not claim an all-clear either")


def test_icmp_reply_validation():
    """A router's destination-unreachable is not an echo reply.

    The first version of this probe counted any received ICMP packet, so an
    unreachable message for the unroutable test address read as a 2310 ms
    success. The negative control caught it; this test keeps it caught.
    """
    print("ICMP reply validation:")
    check(dns_interception._is_echo_reply(_echo_reply()) is True,
          "an echo reply carrying our payload counts")
    check(dns_interception._is_echo_reply(_echo_reply(icmp_type=3)) is False,
          "a destination-unreachable (type 3) does not count")
    check(dns_interception._is_echo_reply(_echo_reply(icmp_type=11)) is False,
          "a time-exceeded (type 11) does not count")
    check(dns_interception._is_echo_reply(_echo_reply(magic=b"someone-else")) is False,
          "an echo reply that is not ours does not count")
    check(dns_interception._is_echo_reply(b"\x00\x00") is False,
          "a truncated packet does not count")
    check(dns_interception._is_echo_reply(b"") is False,
          "an empty packet does not count")
    check(dns_interception._is_echo_reply(b"\x00" * 20 + _echo_reply()) is True,
          "an echo reply behind an IP header still counts")


def test_root_servers_report_unknown_when_intercepted():
    """The roots serve port 53 only and have no encrypted alternative, so on an
    intercepted host the honest answer is that the check could not run."""
    print("Root servers under interception:")
    saved = dns_interception.dns_interception_detected
    dns_check.dns_interception_detected = lambda *a, **k: True
    dns_check.icmp_reachable = lambda ip, **k: (True, 5.0)
    try:
        reachable, unreachable, unknown = dns_check.check_dns_root_servers()
        check(reachable == [], "nothing is reported reachable")
        check(unreachable == [], "nothing is reported unreachable either")
        check(len(unknown) == len(dns_check.DNS_ROOT_SERVERS),
              "every root server is reported as not checkable")
    finally:
        dns_check.dns_interception_detected = saved
        dns_check.icmp_reachable = dns_interception.icmp_reachable


def test_a_root_that_drops_icmp_is_not_called_down():
    """G-root and L-root drop ICMP even when healthy."""
    print("ICMP non-response wording:")
    line = dns_interception.describe_icmp_result("'G' root server",
                                                 "192.112.36.4", False, None)
    check("not proof it is down" in line, "a non-reply is not reported as down")
    check("did not answer a ping" in line, "it is reported as what it is")


def test_resolvers_without_dot_are_unknown():
    """Comodo offers no DoT, so on an intercepted host it cannot be checked at
    all -- which is not the same as being unreachable."""
    print("Resolvers without DoT:")
    for ip in ("8.26.56.26", "8.20.247.20"):
        check(ip not in resolver_check.DOT_HOSTNAMES,
              f"{ip} is correctly recorded as having no DoT service")
    reachable, _, error = resolver_check.check_resolver_over_tls("8.26.56.26")
    check(reachable is False and "cannot be checked" in (error or ""),
          "a resolver with no DoT hostname reports why, not a failure to reach")

    for ip in ("8.8.8.8", "1.1.1.1", "9.9.9.9", "208.67.222.222"):
        check(ip in resolver_check.DOT_HOSTNAMES, f"{ip} has a DoT hostname")


def test_internet_check_does_not_use_port_53():
    """The port was incidental and it is what made the check unable to fail."""
    print("Internet check port:")
    import config
    check(config.INTERNET_CHECK_PORT != 53,
          "the internet check no longer uses port 53")
    check(config.INTERNET_CHECK_PORT == 443,
          "it uses 443, which is not intercepted")
    check(len(config.INTERNET_CHECK_HOSTS) > 1,
          "more than one host is tried before declaring the internet down")


def run_all():
    print(f"{Fore.CYAN}DNS interception tests{Style.RESET_ALL}\n")
    test_interception_detection()
    test_unknown_is_never_an_all_clear()
    test_icmp_reply_validation()
    test_root_servers_report_unknown_when_intercepted()
    test_a_root_that_drops_icmp_is_not_called_down()
    test_resolvers_without_dot_are_unknown()
    test_internet_check_does_not_use_port_53()

    print()
    if FAILURES:
        print(f"{Fore.RED}{len(FAILURES)} check(s) failed:{Style.RESET_ALL}")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print(f"{Fore.GREEN}All DNS interception checks passed{Style.RESET_ALL}")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
