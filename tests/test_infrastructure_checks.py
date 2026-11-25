#!/usr/bin/env python3
"""
Test script for the internet exchange point and WHOIS server checks

Both checks reported failures that were not outages. The Equinix status page
answers 403 on every request, and six WHOIS servers had been retired. These
tests cover the properties that keep the fixed versions honest: a standing
failure is gone, and a real failure is still reported.

Offline: every network call is stubbed. See docs/infrastructure_checks_srd.md.
"""

import inspect
import os
import socket
import sys

import requests
from colorama import Fore, Style, init

init(autoreset=True)

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import network_diagnostics
from network import ixp_diagnostics

FAILURES = []

RETIRED_WHOIS_SERVERS = (
    "whois.nic.mobi", "whois.nic.google", "whois.nic.co", "whois.nic.info",
    "whois.nic.pro", "whois.registry.in",
)

# The five regional internet registries. Removing the retired servers must not
# take any of these with them.
REGIONAL_REGISTRY_WHOIS_SERVERS = (
    "whois.arin.net", "whois.ripe.net", "whois.apnic.net", "whois.lacnic.net",
    "whois.afrinic.net",
)


def check(condition, label):
    if condition:
        print(f"{Fore.GREEN}  [PASS] {label}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}  [FAIL] {label}{Style.RESET_ALL}")
        FAILURES.append(label)


class FakeResponse:
    """A stand-in for requests.Response carrying only a status code."""

    def __init__(self, status_code):
        self.status_code = status_code


class FakeSession:
    """A stand-in for requests.Session that replays a script of outcomes.

    Each entry of the script is a status code to return or an exception to
    raise. The last entry repeats once the script is used up.
    """

    def __init__(self, script):
        self.script = list(script)
        self.calls = 0
        self.headers = {}
        self.verify = True
        self.proxies = {}

    def get(self, url, timeout=None):
        outcome = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        return FakeResponse(outcome)


def run_ixp_test(script, retries=2):
    """Run one IXP website test against a scripted session, without sleeping."""
    session = FakeSession(script)
    saved_build = ixp_diagnostics._build_session
    saved_sleep = ixp_diagnostics.time.sleep
    ixp_diagnostics._build_session = lambda *args: session
    ixp_diagnostics.time.sleep = lambda seconds: None
    try:
        answered, result = ixp_diagnostics._test_ixp_connectivity(
            "Example IX", "https://ix.example/", retries=retries)
    finally:
        ixp_diagnostics._build_session = saved_build
        ixp_diagnostics.time.sleep = saved_sleep
    return answered, result, session.calls


def test_a_refusal_is_an_answer():
    """A 403 is a server that is up, and must not be retried."""
    print("IXP: a refused request:")
    answered, result, calls = run_ixp_test([403])
    check(answered is True, "HTTP 403 counts as an answer")
    check(calls == 1, "an answered request is not retried")
    check(result["error"] is None, "an answered site carries no error")

    answered, _, calls = run_ixp_test([401])
    check(answered is True and calls == 1, "HTTP 401 counts as an answer")


def test_a_real_failure_is_still_reported():
    """The negative control: the check can still say a site did not answer."""
    print("IXP: real failures:")
    answered, result, calls = run_ixp_test([503], retries=2)
    check(answered is False, "HTTP 503 does not count as an answer")
    check(calls == 3, "a 5xx status is retried the configured number of times")
    check(result["error"] == "HTTP 503", "the error names the status")

    answered, result, calls = run_ixp_test([requests.exceptions.Timeout("slow")], retries=1)
    check(answered is False and result["error"] == "Connection timeout",
          "a timeout is reported as a timeout")
    check(calls == 2, "a timeout is retried")

    answered, result, _ = run_ixp_test(
        [requests.exceptions.SSLError("bad certificate for ix.example")], retries=0)
    check(result["error"] == "TLS certificate error",
          "a TLS failure is not reported as a plain connection failure")
    check("ix.example" not in result["error"],
          "the short error carries no text from the exception")

    answered, _, calls = run_ixp_test([requests.exceptions.ConnectionError("x"), 200])
    check(answered is True and calls == 2, "a site that answers on the retry is counted")


def run_monitor(script):
    """Run the whole IXP check with every site following the same script."""
    saved_build = ixp_diagnostics._build_session
    saved_sleep = ixp_diagnostics.time.sleep
    ixp_diagnostics._build_session = lambda *args: FakeSession(script)
    ixp_diagnostics.time.sleep = lambda seconds: None
    try:
        return ixp_diagnostics.monitor_ixp_connectivity(silent=True)
    finally:
        ixp_diagnostics._build_session = saved_build
        ixp_diagnostics.time.sleep = saved_sleep


def test_the_ixp_result_is_a_standard_result():
    """Manual mode prints the report only for a standardized success result."""
    print("IXP: the returned result:")
    total = len(ixp_diagnostics.IXP_ENDPOINTS)

    result = run_monitor([200])
    check(result.get("success") is True, "the result carries success=True")
    check(f"IXP websites answering: {total}/{total}" in result["stdout"],
          "the report states the count")
    check("All IXP websites answered." in result["stdout"],
          "the report says so when every site answered")
    check(result["summary"]["successful"] == total,
          "the summary is still present at the top level")

    result = run_monitor([requests.exceptions.ConnectionError("down")])
    check(result.get("success") is True,
          "a check that ran is a success even when no site answered")
    check(f"IXP websites answering: 0/{total}" in result["stdout"],
          "the report states that none answered")
    check("All IXP websites answered." not in result["stdout"],
          "the all-answered line is absent when a site failed")
    check(result["stdout"].count("Connection failed") == total,
          "every failed site is listed")
    check("\x1b" not in result["stdout"], "the report carries no colour codes")
    names = list(ixp_diagnostics.IXP_ENDPOINTS)
    positions = [result["stdout"].index(name) for name in names]
    check(positions == sorted(positions), "sites are listed in a stable order")


def run_whois_check(connect):
    """Run the whole WHOIS check with a stubbed socket connection."""
    saved_connect = network_diagnostics.socket.create_connection
    saved_sleep = network_diagnostics.time.sleep
    network_diagnostics.socket.create_connection = connect
    network_diagnostics.time.sleep = lambda seconds: None
    try:
        result = network_diagnostics.check_whois_servers()
    finally:
        network_diagnostics.socket.create_connection = saved_connect
        network_diagnostics.time.sleep = saved_sleep
    return result["stdout"] if isinstance(result, dict) else result


class FakeConnection:
    """A stand-in for a connected socket, usable as a context manager."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_retired_whois_servers_are_gone():
    print("WHOIS: the server list:")
    for name in RETIRED_WHOIS_SERVERS:
        check(name not in network_diagnostics.WHOIS_SERVERS_DICT,
              f"{name} is no longer checked")
    # A lookup by exact key. Written with get() and not "in", because CodeQL
    # reads a hostname literal on the left of "in" as a substring test of a URL.
    for name in REGIONAL_REGISTRY_WHOIS_SERVERS:
        check(network_diagnostics.WHOIS_SERVERS_DICT.get(name) is not None,
              f"{name} is still checked")
    check(network_diagnostics.WHOIS_MAX_WORKERS
          >= len(network_diagnostics.WHOIS_SERVERS_DICT),
          "every server has its own worker, so one timeout bounds the round")


def test_whois_failures_are_classified_without_remote_text():
    print("WHOIS: one server:")
    saved = network_diagnostics.socket.create_connection

    def run(outcome):
        def connect(address, timeout=None):
            if isinstance(outcome, Exception):
                raise outcome
            return FakeConnection()
        network_diagnostics.socket.create_connection = connect
        try:
            return network_diagnostics.check_whois_server("whois.example")
        finally:
            network_diagnostics.socket.create_connection = saved

    check(run(None) is None, "an opened connection is reachable")
    check(run(socket.gaierror(8, "nodename nor servname provided")) == "name did not resolve",
          "a name that does not resolve is reported as such")
    check(run(socket.timeout("timed out")) == "timed out", "a timeout is reported as such")
    check(run(ConnectionRefusedError(61, "refused")) == "connection refused",
          "a refusal is reported as such")
    check(run(OSError(65, "No route to host")) == "connection failed",
          "any other socket error is a connection failure")


def test_the_whois_report_is_whole():
    """The negative control, and the rule that the report is never cut short."""
    print("WHOIS: the report:")
    total = len(network_diagnostics.WHOIS_SERVERS_DICT)

    report = run_whois_check(lambda address, timeout=None: FakeConnection())
    check(f"Reachable WHOIS Servers ({total}):" in report, "every server is counted reachable")
    check("All WHOIS servers were reachable." in report, "the all-reachable line is present")

    def refuse(address, timeout=None):
        raise socket.timeout("timed out")

    report = run_whois_check(refuse)
    check(f"Unreachable WHOIS Servers ({total}):" in report,
          "the check can report every server unreachable")
    check("All WHOIS servers were reachable." not in report,
          "the all-reachable line is absent when a server failed")
    check(report.count(": timed out") == total,
          "every failure is listed, so the report was not truncated")
    check("truncated" not in report.lower(), "the report carries no truncation marker")

    attempts = {}

    def flaky(address, timeout=None):
        attempts[address[0]] = attempts.get(address[0], 0) + 1
        if address[0] == "whois.arin.net" and attempts[address[0]] == 1:
            raise socket.timeout("timed out")
        return FakeConnection()

    report = run_whois_check(flaky)
    check(attempts["whois.arin.net"] == 2, "a failed server is tried a second time")
    check(attempts["whois.ripe.net"] == 1, "a reachable server is not tried again")
    check(f"Reachable WHOIS Servers ({total}):" in report,
          "a server that answers on the retry is counted reachable")


def test_no_language_model_rewrites_the_whois_report():
    print("WHOIS: no model in the path:")
    source = inspect.getsource(network_diagnostics.check_whois_servers.__wrapped__
                               if hasattr(network_diagnostics.check_whois_servers, "__wrapped__")
                               else network_diagnostics.check_whois_servers)
    check("ollama_shorten_output(" not in source,
          "check_whois_servers does not call the language-model shortener")
    check("ollama_shorten_output(" not in inspect.getsource(
        network_diagnostics.format_whois_report),
        "format_whois_report does not call the language-model shortener")


def run_all():
    print(f"{Fore.CYAN}Infrastructure check tests{Style.RESET_ALL}\n")
    test_a_refusal_is_an_answer()
    test_a_real_failure_is_still_reported()
    test_the_ixp_result_is_a_standard_result()
    test_retired_whois_servers_are_gone()
    test_whois_failures_are_classified_without_remote_text()
    test_the_whois_report_is_whole()
    test_no_language_model_rewrites_the_whois_report()

    print()
    if FAILURES:
        print(f"{Fore.RED}{len(FAILURES)} check(s) failed:{Style.RESET_ALL}")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print(f"{Fore.GREEN}All infrastructure checks passed{Style.RESET_ALL}")
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
