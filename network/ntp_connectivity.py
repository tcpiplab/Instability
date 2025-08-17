"""
Network Time Protocol Connectivity Testing Module

Comprehensive NTP server testing, time synchronization validation, and stratum analysis.
Tests connectivity to major NTP servers worldwide and provides detailed timing analysis.
Part of the instability.py v3 network diagnostics suite.
"""

import ntplib
import socket
import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Tuple
from colorama import Fore, Style

from config import (
    NTP_DEFAULT_PORT, NTP_DEFAULT_TIMEOUT, NTP_DEFAULT_VERSION, 
    NTP_SYNC_THRESHOLD_MS, NTP_MAX_PARALLEL_CHECKS, 
    get_ntp_servers, get_ntp_timeout
)
from core.error_handling import (
    create_error_response, create_network_error, ErrorType, ErrorCode
)
from utils import create_success_result, create_error_result


def test_ntp_server(
    server: str, 
    port: int = None, 
    timeout: int = None, 
    version: int = None, 
    silent: bool = False
) -> Dict[str, Any]:
    """
    Test connectivity and time synchronization with an NTP server.
    
    This function queries an NTP server using the specified protocol version
    and returns detailed timing information including offset calculations,
    stratum level, and server characteristics.
    
    Args:
        server: NTP server hostname or IP address
        port: UDP port for NTP service (default: 123)
        timeout: Query timeout in seconds (default: 5)
        version: NTP protocol version 2-4 (default: 3)
        silent: Suppress console output if True
        
    Returns:
        Dict containing success status, timing data, server info, and any errors
        
    Example:
        result = test_ntp_server("time.google.com")
        if result["success"]:
            print(f"Server time: {result['parsed_data']['server_time']}")
            print(f"Offset: {result['parsed_data']['offset_ms']}ms")
    """
    if port is None:
        port = NTP_DEFAULT_PORT
    if timeout is None:
        timeout = get_ntp_timeout("individual")
    if version is None:
        version = NTP_DEFAULT_VERSION
    
    start_time = time.time()
    command = f"NTP query to {server}:{port} (version {version})"
    
    if not silent:
        print(f"{Fore.YELLOW}Testing NTP server {server}:{port}...{Style.RESET_ALL}")
    
    try:
        # Validate NTP version
        if version not in [2, 3, 4]:
            return create_error_result(
                tool_name="test_ntp_server",
                execution_time=time.time() - start_time,
                error_message=f"Invalid NTP version {version}. Must be 2, 3, or 4",
                error_type="invalid_target",
                command_executed=command,
                target=server
            )
        
        # Validate port
        if not (1 <= port <= 65535):
            return create_error_result(
                tool_name="test_ntp_server", 
                execution_time=time.time() - start_time,
                error_message=f"Invalid port {port}. Must be between 1-65535",
                error_type="invalid_target",
                command_executed=command,
                target=server
            )
        
        # Create NTP client
        client = ntplib.NTPClient()
        
        # Record local time before request
        local_time_before = time.time()
        
        # Query the NTP server
        response = client.request(server, port=port, version=version, timeout=timeout)
        
        # Record local time after request  
        local_time_after = time.time()
        execution_time = local_time_after - start_time
        
        # Calculate times and offsets
        server_time = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)
        local_time = datetime.fromtimestamp(local_time_after, tz=timezone.utc)
        
        # Calculate offset in milliseconds
        # Positive offset means server is ahead of local time
        offset_seconds = response.tx_time - local_time_after
        offset_ms = offset_seconds * 1000
        
        # Calculate response time
        response_time_ms = (local_time_after - local_time_before) * 1000
        
        # Extract server information
        stratum = response.stratum if hasattr(response, 'stratum') else None
        reference_id = response.ref_id if hasattr(response, 'ref_id') else None
        precision = response.precision if hasattr(response, 'precision') else None
        root_delay = response.root_delay if hasattr(response, 'root_delay') else None
        root_dispersion = response.root_dispersion if hasattr(response, 'root_dispersion') else None
        
        # Convert reference_id to readable format if it's an IP
        ref_id_str = reference_id
        if reference_id and isinstance(reference_id, int):
            try:
                ref_id_str = socket.inet_ntoa(reference_id.to_bytes(4, 'big'))
            except (ValueError, OverflowError):
                ref_id_str = str(reference_id)
        
        parsed_data = {
            "success": True,
            "server": server,
            "port": port,
            "server_time": server_time.isoformat(),
            "local_time": local_time.isoformat(), 
            "offset_ms": round(offset_ms, 3),
            "stratum": stratum,
            "reference_id": ref_id_str,
            "precision": precision,
            "root_delay": root_delay,
            "root_dispersion": root_dispersion,
            "response_time_ms": round(response_time_ms, 3),
            "version": version,
            "timestamp": datetime.now().isoformat()
        }
        
        # Console output
        if not silent:
            print(f"{Fore.GREEN}[OK] {server}: Server time {server_time.strftime('%Y-%m-%d %H:%M:%S UTC')}{Style.RESET_ALL}")
            print(f"  Offset: {offset_ms:+.1f}ms, Stratum: {stratum}, Response: {response_time_ms:.1f}ms")
            if abs(offset_ms) > NTP_SYNC_THRESHOLD_MS:
                print(f"{Fore.YELLOW}  Warning: Large time offset ({offset_ms:+.1f}ms){Style.RESET_ALL}")
        
        return create_success_result(
            tool_name="test_ntp_server",
            execution_time=execution_time,
            parsed_data=parsed_data,
            command_executed=command,
            target=server,
            stdout=f"NTP server {server} responded with stratum {stratum}, offset {offset_ms:+.1f}ms"
        )
        
    except ntplib.NTPException as e:
        execution_time = time.time() - start_time
        error_msg = f"NTP protocol error: {str(e)}"
        if not silent:
            print(f"{Fore.RED}[FAIL] {server}: {error_msg}{Style.RESET_ALL}")
        
        return create_error_result(
            tool_name="test_ntp_server",
            execution_time=execution_time,
            error_message=error_msg,
            error_type="network",
            command_executed=command,
            target=server,
            stderr=str(e)
        )
        
    except socket.timeout:
        execution_time = time.time() - start_time
        error_msg = f"Connection timeout after {timeout}s"
        if not silent:
            print(f"{Fore.YELLOW}[TIMEOUT] {server}: {error_msg}{Style.RESET_ALL}")
            
        return create_error_result(
            tool_name="test_ntp_server",
            execution_time=execution_time,
            error_message=error_msg,
            error_type="timeout", 
            command_executed=command,
            target=server
        )
        
    except socket.gaierror as e:
        execution_time = time.time() - start_time
        error_msg = f"DNS resolution failed: {str(e)}"
        if not silent:
            print(f"{Fore.RED}[FAIL] {server}: {error_msg}{Style.RESET_ALL}")
            
        return create_error_result(
            tool_name="test_ntp_server",
            execution_time=execution_time,
            error_message=error_msg,
            error_type="network",
            command_executed=command,
            target=server,
            stderr=str(e)
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"Unexpected error: {str(e)}"
        if not silent:
            print(f"{Fore.RED}[ERROR] {server}: {error_msg}{Style.RESET_ALL}")
            
        return create_error_result(
            tool_name="test_ntp_server",
            execution_time=execution_time,
            error_message=error_msg,
            error_type="execution",
            command_executed=command,
            target=server,
            stderr=str(e)
        )


def check_ntp_servers(
    servers: Optional[List[str]] = None, 
    timeout: int = None, 
    retry_failed: bool = True, 
    silent: bool = False
) -> Dict[str, Any]:
    """
    Test connectivity to multiple NTP servers with retry logic.
    
    Performs concurrent testing of NTP servers and categorizes results.
    Failed servers are optionally retried after a delay to handle
    temporary network issues.
    
    Args:
        servers: List of NTP servers to test (uses defaults if None)
        timeout: Query timeout per server in seconds
        retry_failed: Whether to retry failed servers once
        silent: Suppress console output if True
        
    Returns:
        Dict with reachable/unreachable servers, summary, and recommendations
        
    Example:
        result = check_ntp_servers()
        print(f"Reachable: {len(result['parsed_data']['reachable_servers'])}")
        for server_data in result['parsed_data']['reachable_servers']:
            print(f"  {server_data['server']}: {server_data['server_time']}")
    """
    if servers is None:
        servers = get_ntp_servers()
    if timeout is None:
        timeout = get_ntp_timeout("batch")
        
    start_time = time.time()
    command = f"NTP batch check of {len(servers)} servers"
    
    if not silent:
        print(f"{Fore.CYAN}NTP Server Connectivity Testing{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Testing {len(servers)} NTP servers with {timeout}s timeout...{Style.RESET_ALL}\n")
    
    reachable_servers = []
    unreachable_servers = []
    
    def test_single_server(server: str) -> Tuple[str, Dict[str, Any]]:
        """Helper function for concurrent testing"""
        result = test_ntp_server(server, timeout=timeout, silent=True)
        return server, result
    
    # First round of testing with concurrent execution
    with ThreadPoolExecutor(max_workers=min(NTP_MAX_PARALLEL_CHECKS, len(servers))) as executor:
        future_to_server = {
            executor.submit(test_single_server, server): server 
            for server in servers
        }
        
        for future in as_completed(future_to_server):
            server = future_to_server[future]
            try:
                _, result = future.result()
                if result["success"]:
                    reachable_servers.append(result["parsed_data"])
                    if not silent:
                        offset = result["parsed_data"]["offset_ms"]
                        stratum = result["parsed_data"]["stratum"]
                        response_time = result["parsed_data"]["response_time_ms"]
                        print(f"{Fore.GREEN}[OK] {server}: offset {offset:+.1f}ms, stratum {stratum}, {response_time:.1f}ms{Style.RESET_ALL}")
                else:
                    unreachable_servers.append({
                        "server": server,
                        "error": result["error_message"],
                        "error_type": result.get("error_type", "unknown")
                    })
                    if not silent:
                        error_type = result.get("error_type", "unknown")
                        status = "[TIMEOUT]" if "timeout" in error_type else "[FAIL]"
                        color = Fore.YELLOW if "timeout" in error_type else Fore.RED
                        print(f"{color}{status} {server}: {result['error_message']}{Style.RESET_ALL}")
                        
            except Exception as e:
                unreachable_servers.append({
                    "server": server,
                    "error": f"Future execution failed: {str(e)}",
                    "error_type": "execution"
                })
                if not silent:
                    print(f"{Fore.RED}[ERROR] {server}: Future execution failed: {str(e)}{Style.RESET_ALL}")
    
    # Retry failed servers if requested
    if retry_failed and unreachable_servers:
        if not silent:
            print(f"\n{Fore.YELLOW}Retrying {len(unreachable_servers)} failed servers...{Style.RESET_ALL}")
        
        time.sleep(2)  # Brief delay before retrying
        servers_to_retry = [srv["server"] for srv in unreachable_servers]
        retry_reachable = []
        retry_unreachable = []
        
        with ThreadPoolExecutor(max_workers=min(NTP_MAX_PARALLEL_CHECKS, len(servers_to_retry))) as executor:
            future_to_server = {
                executor.submit(test_single_server, server): server 
                for server in servers_to_retry
            }
            
            for future in as_completed(future_to_server):
                server = future_to_server[future]
                try:
                    _, result = future.result()
                    if result["success"]:
                        retry_reachable.append(result["parsed_data"])
                        if not silent:
                            offset = result["parsed_data"]["offset_ms"]
                            stratum = result["parsed_data"]["stratum"]
                            response_time = result["parsed_data"]["response_time_ms"]
                            print(f"{Fore.GREEN}[RETRY OK] {server}: offset {offset:+.1f}ms, stratum {stratum}, {response_time:.1f}ms{Style.RESET_ALL}")
                    else:
                        retry_unreachable.append({
                            "server": server,
                            "error": result["error_message"],
                            "error_type": result.get("error_type", "unknown")
                        })
                        if not silent:
                            error_type = result.get("error_type", "unknown")
                            status = "[RETRY TIMEOUT]" if "timeout" in error_type else "[RETRY FAIL]"
                            color = Fore.YELLOW if "timeout" in error_type else Fore.RED
                            print(f"{color}{status} {server}: {result['error_message']}{Style.RESET_ALL}")
                            
                except Exception as e:
                    retry_unreachable.append({
                        "server": server,
                        "error": f"Retry execution failed: {str(e)}",
                        "error_type": "execution"
                    })
                    if not silent:
                        print(f"{Fore.RED}[RETRY ERROR] {server}: Retry execution failed: {str(e)}{Style.RESET_ALL}")
        
        # Update results with retry outcomes
        reachable_servers.extend(retry_reachable)
        unreachable_servers = retry_unreachable
    
    execution_time = time.time() - start_time
    
    # Calculate summary statistics
    total_servers = len(servers)
    successful = len(reachable_servers)
    failed = len(unreachable_servers)
    success_rate = (successful / total_servers * 100) if total_servers > 0 else 0
    
    # Generate recommendations
    recommendations = []
    if successful == 0:
        recommendations.append("No NTP servers are reachable - check network connectivity and firewall settings")
        recommendations.append("Verify UDP port 123 outbound traffic is allowed")
    elif successful < total_servers * 0.5:
        recommendations.append("Many NTP servers unreachable - consider network diagnostics")
        recommendations.append("Check if corporate firewall blocks NTP traffic")
    elif successful >= total_servers * 0.8:
        recommendations.append("Good NTP connectivity - most servers reachable")
    
    # Check for time synchronization issues
    if reachable_servers:
        large_offsets = [s for s in reachable_servers if abs(s["offset_ms"]) > NTP_SYNC_THRESHOLD_MS]
        if large_offsets:
            recommendations.append(f"Warning: {len(large_offsets)} servers show large time offsets (>{NTP_SYNC_THRESHOLD_MS}ms)")
            recommendations.append("Consider checking system clock synchronization")
    
    # Generate overall status
    if successful == total_servers:
        status = "success"
        summary = f"All {total_servers} NTP servers are reachable"
    elif successful >= total_servers * 0.8:
        status = "success" 
        summary = f"{successful}/{total_servers} NTP servers reachable ({success_rate:.1f}%)"
    elif successful > 0:
        status = "partial"
        summary = f"Partial NTP connectivity: {successful}/{total_servers} servers reachable ({success_rate:.1f}%)"
    else:
        status = "error"
        summary = f"No NTP servers reachable (0/{total_servers})"
    
    parsed_data = {
        "status": status,
        "total_servers": total_servers,
        "successful": successful,
        "failed": failed,
        "success_rate": success_rate,
        "reachable_servers": reachable_servers,
        "unreachable_servers": unreachable_servers,
        "summary": summary,
        "recommendations": recommendations,
        "timestamp": datetime.now().isoformat()
    }
    
    # Display summary
    if not silent:
        print(f"\n{Fore.CYAN}NTP Server Test Summary:{Style.RESET_ALL}")
        print(f"Total servers tested: {total_servers}")
        print(f"Reachable servers: {successful}")
        print(f"Unreachable servers: {failed}")
        print(f"Success rate: {success_rate:.1f}%")
        
        if reachable_servers:
            print(f"\n{Fore.GREEN}Reachable NTP Servers:{Style.RESET_ALL}")
            for server_data in sorted(reachable_servers, key=lambda x: abs(x["offset_ms"])):
                offset = server_data["offset_ms"]
                stratum = server_data["stratum"]
                response_time = server_data["response_time_ms"]
                print(f"  [OK] {server_data['server']}: offset {offset:+.1f}ms, stratum {stratum}, response {response_time:.1f}ms")
        
        if unreachable_servers:
            print(f"\n{Fore.RED}Unreachable NTP Servers:{Style.RESET_ALL}")
            for server_data in unreachable_servers:
                error_type = server_data.get("error_type", "unknown")
                status = "[TIMEOUT]" if "timeout" in error_type else "[FAIL]"
                print(f"  {status} {server_data['server']}: {server_data['error']}")
        
        if recommendations:
            print(f"\n{Fore.YELLOW}Recommendations:{Style.RESET_ALL}")
            for rec in recommendations:
                print(f"  - {rec}")
    
    return create_success_result(
        tool_name="check_ntp_servers",
        execution_time=execution_time,
        parsed_data=parsed_data,
        command_executed=command,
        target=f"{len(servers)} NTP servers",
        stdout=summary
    )


def analyze_ntp_sync(
    servers: Optional[List[str]] = None, 
    threshold_ms: int = None, 
    silent: bool = False
) -> Dict[str, Any]:
    """
    Analyze NTP time synchronization across multiple servers.
    
    Compare time from multiple NTP servers to identify servers with
    significant time drift, calculate consensus time, and detect
    potential time manipulation or server issues.
    
    Args:
        servers: List of NTP servers to analyze (uses defaults if None)
        threshold_ms: Threshold for significant time drift in milliseconds
        silent: Suppress console output if True
        
    Returns:
        Dict containing synchronization analysis and recommendations
    """
    if servers is None:
        servers = get_ntp_servers()
    if threshold_ms is None:
        threshold_ms = NTP_SYNC_THRESHOLD_MS
        
    start_time = time.time()
    command = f"NTP synchronization analysis of {len(servers)} servers"
    
    if not silent:
        print(f"{Fore.CYAN}NTP Time Synchronization Analysis{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Analyzing time synchronization across {len(servers)} NTP servers...{Style.RESET_ALL}\n")
    
    # First get connectivity results
    batch_result = check_ntp_servers(servers=servers, silent=True)
    
    if not batch_result["success"] or not batch_result["parsed_data"]["reachable_servers"]:
        return create_error_result(
            tool_name="analyze_ntp_sync",
            execution_time=time.time() - start_time,
            error_message="No NTP servers reachable for synchronization analysis",
            error_type="network",
            command_executed=command,
            target=f"{len(servers)} NTP servers"
        )
    
    reachable_servers = batch_result["parsed_data"]["reachable_servers"]
    
    # Extract offset data
    offsets = [server["offset_ms"] for server in reachable_servers]
    server_times = [(server["server"], server["offset_ms"]) for server in reachable_servers]
    
    # Calculate statistics
    mean_offset = sum(offsets) / len(offsets) if offsets else 0
    min_offset = min(offsets) if offsets else 0
    max_offset = max(offsets) if offsets else 0
    offset_range = max_offset - min_offset if offsets else 0
    
    # Calculate standard deviation
    if len(offsets) > 1:
        variance = sum((x - mean_offset) ** 2 for x in offsets) / (len(offsets) - 1)
        std_deviation = variance ** 0.5
    else:
        std_deviation = 0
    
    # Identify servers with significant drift
    drifted_servers = []
    synchronized_servers = []
    
    for server_data in reachable_servers:
        offset = server_data["offset_ms"]
        if abs(offset) > threshold_ms:
            drifted_servers.append({
                "server": server_data["server"],
                "offset_ms": offset,
                "drift_severity": "high" if abs(offset) > threshold_ms * 2 else "moderate"
            })
        else:
            synchronized_servers.append({
                "server": server_data["server"],
                "offset_ms": offset
            })
    
    # Calculate consensus time (median of all offsets)
    sorted_offsets = sorted(offsets)
    if len(sorted_offsets) % 2 == 0:
        median_offset = (sorted_offsets[len(sorted_offsets)//2 - 1] + sorted_offsets[len(sorted_offsets)//2]) / 2
    else:
        median_offset = sorted_offsets[len(sorted_offsets)//2]
    
    # Quality assessment
    if offset_range <= threshold_ms:
        sync_quality = "excellent"
        quality_score = 95
    elif offset_range <= threshold_ms * 2:
        sync_quality = "good" 
        quality_score = 80
    elif offset_range <= threshold_ms * 5:
        sync_quality = "moderate"
        quality_score = 60
    else:
        sync_quality = "poor"
        quality_score = 30
    
    # Generate recommendations
    recommendations = []
    if len(drifted_servers) == 0:
        recommendations.append("All servers show good time synchronization")
    elif len(drifted_servers) == len(reachable_servers):
        recommendations.append("All servers show significant time drift - check local system clock")
        recommendations.append("Consider running 'ntpdate' or enabling NTP synchronization")
    else:
        recommendations.append(f"{len(drifted_servers)} servers show significant time drift")
        recommendations.append("Investigate servers with large offsets for reliability")
    
    if offset_range > threshold_ms * 3:
        recommendations.append("Large variation between servers detected - potential reliability issues")
    
    if std_deviation > threshold_ms:
        recommendations.append("High standard deviation indicates inconsistent server responses")
    
    execution_time = time.time() - start_time
    
    parsed_data = {
        "total_analyzed": len(reachable_servers),
        "threshold_ms": threshold_ms,
        "statistics": {
            "mean_offset_ms": round(mean_offset, 3),
            "median_offset_ms": round(median_offset, 3),
            "min_offset_ms": round(min_offset, 3),
            "max_offset_ms": round(max_offset, 3),
            "offset_range_ms": round(offset_range, 3),
            "std_deviation_ms": round(std_deviation, 3)
        },
        "synchronized_servers": synchronized_servers,
        "drifted_servers": drifted_servers,
        "sync_quality": sync_quality,
        "quality_score": quality_score,
        "recommendations": recommendations,
        "timestamp": datetime.now().isoformat()
    }
    
    # Display analysis results
    if not silent:
        print(f"Analyzed {len(reachable_servers)} reachable NTP servers")
        print(f"Time offset threshold: ±{threshold_ms}ms")
        
        print(f"\n{Fore.CYAN}Time Offset Statistics:{Style.RESET_ALL}")
        print(f"Mean offset: {mean_offset:+.1f}ms")
        print(f"Median offset: {median_offset:+.1f}ms")
        print(f"Offset range: {offset_range:.1f}ms (min: {min_offset:+.1f}ms, max: {max_offset:+.1f}ms)")
        print(f"Standard deviation: {std_deviation:.1f}ms")
        
        print(f"\n{Fore.CYAN}Synchronization Quality: {Style.RESET_ALL}", end="")
        quality_color = Fore.GREEN if quality_score >= 80 else Fore.YELLOW if quality_score >= 60 else Fore.RED
        print(f"{quality_color}{sync_quality.upper()} ({quality_score}%){Style.RESET_ALL}")
        
        if synchronized_servers:
            print(f"\n{Fore.GREEN}Well-Synchronized Servers ({len(synchronized_servers)}):{Style.RESET_ALL}")
            for server in sorted(synchronized_servers, key=lambda x: abs(x["offset_ms"])):
                print(f"  [SYNC] {server['server']}: {server['offset_ms']:+.1f}ms")
        
        if drifted_servers:
            print(f"\n{Fore.RED}Servers with Significant Drift ({len(drifted_servers)}):{Style.RESET_ALL}")
            for server in sorted(drifted_servers, key=lambda x: abs(x["offset_ms"]), reverse=True):
                severity_color = Fore.RED if server["drift_severity"] == "high" else Fore.YELLOW
                print(f"  {severity_color}[DRIFT] {server['server']}: {server['offset_ms']:+.1f}ms ({server['drift_severity']}){Style.RESET_ALL}")
        
        if recommendations:
            print(f"\n{Fore.YELLOW}Recommendations:{Style.RESET_ALL}")
            for rec in recommendations:
                print(f"  - {rec}")
    
    return create_success_result(
        tool_name="analyze_ntp_sync",
        execution_time=execution_time,
        parsed_data=parsed_data,
        command_executed=command,
        target=f"{len(reachable_servers)} NTP servers",
        stdout=f"Synchronization analysis complete: {sync_quality} quality ({quality_score}%)"
    )


def get_module_tools():
    """
    Register NTP tools with the unified tool registry.
    
    Returns:
        Dictionary of tool metadata for tools registry integration
    """
    from core.tools_registry import ToolMetadata, ParameterInfo, ParameterType, ToolCategory
    
    return {
        "test_ntp_server": ToolMetadata(
            name="test_ntp_server",
            function_name="test_ntp_server",
            module_path="network.ntp_connectivity",
            description="Test connectivity and synchronization with an NTP server",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "server": ParameterInfo(
                    ParameterType.STRING,
                    required=True,
                    description="NTP server hostname or IP address"
                ),
                "port": ParameterInfo(
                    ParameterType.INTEGER,
                    default=NTP_DEFAULT_PORT,
                    description=f"UDP port for NTP service (default: {NTP_DEFAULT_PORT})"
                ),
                "timeout": ParameterInfo(
                    ParameterType.INTEGER,
                    default=NTP_DEFAULT_TIMEOUT,
                    description=f"Query timeout in seconds (default: {NTP_DEFAULT_TIMEOUT})"
                ),
                "version": ParameterInfo(
                    ParameterType.INTEGER,
                    default=NTP_DEFAULT_VERSION,
                    description=f"NTP protocol version 2-4 (default: {NTP_DEFAULT_VERSION})"
                ),
                "silent": ParameterInfo(
                    ParameterType.BOOLEAN,
                    default=False,
                    description="Suppress console output"
                )
            },
            aliases=["ntp_test", "query_ntp"],
            examples=[
                "test_ntp_server time.google.com",
                "test_ntp_server 192.168.1.1 --timeout 10",
                "test_ntp_server time.nist.gov --version 4 --port 123"
            ]
        ),
        "check_ntp_servers": ToolMetadata(
            name="check_ntp_servers",
            function_name="check_ntp_servers",
            module_path="network.ntp_connectivity",
            description="Test multiple NTP servers with concurrent testing and retry logic",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "servers": ParameterInfo(
                    ParameterType.LIST,
                    default=None,
                    description="List of NTP servers to test (uses well-known servers if None)"
                ),
                "timeout": ParameterInfo(
                    ParameterType.INTEGER,
                    default=get_ntp_timeout("batch"),
                    description=f"Query timeout per server in seconds (default: {get_ntp_timeout('batch')})"
                ),
                "retry_failed": ParameterInfo(
                    ParameterType.BOOLEAN,
                    default=True,
                    description="Whether to retry failed servers once"
                ),
                "silent": ParameterInfo(
                    ParameterType.BOOLEAN,
                    default=False,
                    description="Suppress console output"
                )
            },
            aliases=["ntp_check", "check_ntp", "ntp_batch"],
            examples=[
                "check_ntp_servers",
                "check_ntp_servers --timeout 10 --no-retry",
                "check_ntp_servers --silent"
            ]
        ),
        "analyze_ntp_sync": ToolMetadata(
            name="analyze_ntp_sync",
            function_name="analyze_ntp_sync",
            module_path="network.ntp_connectivity",
            description="Analyze time synchronization quality across multiple NTP servers",
            category=ToolCategory.NETWORK_DIAGNOSTICS,
            parameters={
                "servers": ParameterInfo(
                    ParameterType.LIST,
                    default=None,
                    description="List of NTP servers to analyze (uses well-known servers if None)"
                ),
                "threshold_ms": ParameterInfo(
                    ParameterType.INTEGER,
                    default=NTP_SYNC_THRESHOLD_MS,
                    description=f"Threshold for significant time drift in milliseconds (default: {NTP_SYNC_THRESHOLD_MS})"
                ),
                "silent": ParameterInfo(
                    ParameterType.BOOLEAN,
                    default=False,
                    description="Suppress console output"
                )
            },
            aliases=["ntp_sync", "ntp_analysis", "sync_analysis"],
            examples=[
                "analyze_ntp_sync",
                "analyze_ntp_sync --threshold_ms 50",
                "analyze_ntp_sync --silent"
            ]
        )
    }