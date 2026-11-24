"""
Internet Exchange Point Monitoring Module

Checks whether the public website of each major internet exchange point answers
an HTTPS request. A reply shows that the exchange's website is reachable from
this host. It says nothing about traffic crossing the exchange itself, and the
report words the result that way.
Part of the instability.py v3 network diagnostics suite.
"""

import concurrent.futures
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
import urllib3
from colorama import Fore

# Import standardized tool result functions
from utils import create_success_result

TOOL_NAME = "monitor_ixp_connectivity"

# Major internet exchange points to monitor
IXP_ENDPOINTS: Dict[str, str] = {
    "DE-CIX Frankfurt": "https://www.de-cix.net/",
    "LINX London": "https://www.linx.net/",
    "AMS-IX Amsterdam": "https://www.ams-ix.net/",
    "NYIIX New York": "https://www.nyiix.net/",
    "HKIX Hong Kong": "https://www.hkix.net/",
    "Equinix Global": "https://status.equinix.com/"
}

# The sites are tested concurrently, so the whole check takes about as long as
# the slowest site: at most (timeout + backoff) * (retries + 1). The defaults
# keep that near 21 seconds. They were 15 seconds and three retries, tested one
# site after another, which let a single dead site hold the check for over a
# minute.
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_RETRIES = 1

# An HTTP status below this means a web server received the request and
# answered it, which is the question this check asks. The Equinix status page
# answers 403 to non-browser clients on every request (measured 2026-11-23), and
# counting that as unreachable reported a standing failure that was not an
# outage. A 5xx status is still a failure, and is retried.
ANSWERED_BELOW_STATUS = 500


def _build_session(
    user_agent: Optional[str],
    insecure: bool,
    burp: bool
) -> requests.Session:
    """
    Build the HTTP session used to test one IXP website.

    Args:
        user_agent: Custom User-Agent header, or None for the tool's own
        insecure: Disable SSL certificate verification
        burp: Route through Burp Suite proxy

    Returns:
        A configured requests session
    """
    session = requests.Session()
    session.headers.update({"User-Agent": user_agent or "InstabilityIXP/1.0"})

    if insecure:
        session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if burp:
        session.proxies = {
            "http": "http://localhost:8080",
            "https": "http://localhost:8080"
        }
    return session


def _test_ixp_connectivity(
    name: str,
    url: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    retries: int = DEFAULT_RETRIES,
    user_agent: Optional[str] = None,
    insecure: bool = False,
    burp: bool = False
) -> Tuple[bool, Dict[str, Any]]:
    """
    Test HTTP connectivity to a specific IXP website with retry logic.

    Any HTTP status below 500 counts as an answer and is never retried. A
    connection failure, a timeout or a 5xx status is retried with exponential
    backoff. This function prints nothing, because it runs on a worker thread
    and concurrent prints would interleave.

    Args:
        name: IXP name for display
        url: IXP URL to test
        timeout: Connection timeout in seconds
        retries: Number of retry attempts
        user_agent: Custom User-Agent header
        insecure: Disable SSL certificate verification
        burp: Route through Burp Suite proxy

    Returns:
        Tuple of (answered, result_dict). The "error" field of result_dict is a
        short fixed category. The exception text, which can be long and names
        hosts, is kept apart in "error_detail".
    """
    result: Dict[str, Any] = {
        "name": name,
        "url": url,
        "response_time": None,
        "status_code": None,
        "error": None,
        "error_detail": None,
        "retry_attempts": 0
    }

    session = _build_session(user_agent, insecure, burp)

    for attempt in range(retries + 1):
        result["retry_attempts"] = attempt
        if attempt > 0:
            time.sleep(2 ** (attempt - 1))

        try:
            start_time = time.time()
            response = session.get(url, timeout=timeout)
            end_time = time.time()
        except requests.exceptions.Timeout as e:
            result["error"] = "Connection timeout"
            result["error_detail"] = str(e)
            continue
        except requests.exceptions.SSLError as e:
            # SSLError and ProxyError are subclasses of ConnectionError, so
            # they must be caught before it.
            result["error"] = "TLS certificate error"
            result["error_detail"] = str(e)
            continue
        except requests.exceptions.ProxyError as e:
            result["error"] = "Proxy connection failed"
            result["error_detail"] = str(e)
            continue
        except requests.exceptions.ConnectionError as e:
            result["error"] = "Connection failed"
            result["error_detail"] = str(e)
            continue
        except requests.exceptions.RequestException as e:
            result["error"] = "Request failed"
            result["error_detail"] = str(e)
            continue

        result["response_time"] = round((end_time - start_time) * 1000, 2)
        result["status_code"] = response.status_code
        if response.status_code < ANSWERED_BELOW_STATUS:
            result["error"] = None
            result["error_detail"] = None
            return True, result
        result["error"] = f"HTTP {response.status_code}"

    return False, result


def format_ixp_report(
    reachable_ixps: List[Dict[str, Any]],
    unreachable_ixps: List[Dict[str, Any]]
) -> str:
    """
    Build the plain-text report of an IXP website check.

    The report is the tool's returned value in manual mode. Other programs
    parse it, so its headings and line shapes are fixed, it carries no colour
    codes, and it is never shortened or truncated.

    Args:
        reachable_ixps: Result dictionaries of the sites that answered
        unreachable_ixps: Result dictionaries of the sites that did not

    Returns:
        The report text
    """
    total = len(reachable_ixps) + len(unreachable_ixps)
    lines = [
        "This check requests the public website of each internet exchange "
        "point. It does not test traffic crossing the exchange.",
        "",
        f"IXP websites answering: {len(reachable_ixps)}/{total}",
    ]

    if reachable_ixps:
        lines.append("")
        lines.append(f"IXP Websites That Answered ({len(reachable_ixps)}):")
        for ixp in reachable_ixps:
            lines.append(f"- {ixp['name']} (HTTP {ixp['status_code']}, "
                         f"{ixp['response_time']:.0f} ms)")

    if unreachable_ixps:
        lines.append("")
        lines.append(f"IXP Websites That Did Not Answer ({len(unreachable_ixps)}):")
        for ixp in unreachable_ixps:
            lines.append(f"- {ixp['name']}: {ixp['error']}")
    else:
        lines.append("")
        lines.append("All IXP websites answered.")

    return "\n".join(lines)


def _overall_status(successful: int, total_tested: int) -> str:
    """
    Grade the check from the share of sites that answered.

    Args:
        successful: Number of sites that answered
        total_tested: Number of sites tested

    Returns:
        "success", "partial" or "error"
    """
    if successful >= total_tested * 0.8:
        return "success"
    if successful >= total_tested * 0.5:
        return "partial"
    return "error"


def monitor_ixp_connectivity(
    silent: bool = False,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    retries: int = DEFAULT_RETRIES,
    user_agent: Optional[str] = None,
    insecure: bool = False,
    burp: bool = False
) -> Dict[str, Any]:
    """
    Check that the websites of major internet exchange points answer.

    Requests the public website of each exchange over HTTPS, all at the same
    time. A site answered if it returned any HTTP status below 500. The result
    is a weak signal of how well distant regions can be reached from this host.
    It is not a test of the exchanges themselves.

    Args:
        silent: Suppress verbose console output
        timeout: Connection timeout in seconds
        retries: Number of retry attempts for failed connections
        user_agent: Custom User-Agent header for HTTP requests
        insecure: Disable SSL certificate verification
        burp: Route traffic through Burp Suite proxy

    Returns:
        A standardized tool result. "success" is True whenever the check ran,
        including when no site answered, because the finding is in the data.
        "stdout" holds the plain-text report, and "parsed_data" holds
        "status", "reachable_ixps", "unreachable_ixps" and "summary". Those
        four are also present at the top level, where earlier versions of this
        tool returned them.
    """
    started = datetime.now()

    if not silent:
        print(f"{Fore.CYAN}Internet Exchange Point Website Check{Fore.RESET}")
        print(f"{Fore.CYAN}Requesting the websites of {len(IXP_ENDPOINTS)} major IXPs..."
              f"{Fore.RESET}\n")

        if insecure:
            print(f"{Fore.YELLOW}Warning: SSL certificate verification disabled{Fore.RESET}")
        if burp:
            print(f"{Fore.YELLOW}Info: Routing traffic through Burp Suite proxy "
                  f"(localhost:8080){Fore.RESET}")

    def test_one(item: Tuple[str, str]) -> Tuple[bool, Dict[str, Any]]:
        return _test_ixp_connectivity(
            name=item[0],
            url=item[1],
            timeout=timeout,
            retries=retries,
            user_agent=user_agent,
            insecure=insecure,
            burp=burp
        )

    # map() returns results in the order of IXP_ENDPOINTS, whichever site
    # finishes first, so the report lists the sites in a stable order.
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(IXP_ENDPOINTS)) as pool:
        outcomes = list(pool.map(test_one, IXP_ENDPOINTS.items()))

    reachable_ixps = [result for answered, result in outcomes if answered]
    unreachable_ixps = [result for answered, result in outcomes if not answered]

    if not silent:
        for answered, result in outcomes:
            if answered:
                print(f"{Fore.GREEN}[OK] {result['name']}: {result['response_time']}ms "
                      f"(HTTP {result['status_code']}){Fore.RESET}")
            else:
                print(f"{Fore.RED}[FAIL] {result['name']}: {result['error']} "
                      f"(after {result['retry_attempts']} retries){Fore.RESET}")

    total_tested = len(IXP_ENDPOINTS)
    successful = len(reachable_ixps)
    failed = len(unreachable_ixps)
    success_rate = round((successful / total_tested) * 100, 1) if total_tested > 0 else 0.0

    data = {
        "status": _overall_status(successful, total_tested),
        "reachable_ixps": reachable_ixps,
        "unreachable_ixps": unreachable_ixps,
        "summary": {
            "total_tested": total_tested,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate
        }
    }

    return create_success_result(
        tool_name=TOOL_NAME,
        execution_time=(datetime.now() - started).total_seconds(),
        parsed_data=data,
        command_executed="HTTPS GET of each IXP website",
        stdout=format_ixp_report(reachable_ixps, unreachable_ixps),
        options_used={"timeout": timeout, "retries": retries, "insecure": insecure,
                      "burp": burp},
        **data
    )


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
            description="Check that the websites of major internet exchange points answer",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "silent": ParameterInfo(
                    ParameterType.BOOLEAN,
                    default=False,
                    description="Suppress verbose console output"
                ),
                "timeout": ParameterInfo(
                    ParameterType.INTEGER,
                    default=DEFAULT_TIMEOUT_SECONDS,
                    description="Connection timeout in seconds"
                ),
                "retries": ParameterInfo(
                    ParameterType.INTEGER,
                    default=DEFAULT_RETRIES,
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