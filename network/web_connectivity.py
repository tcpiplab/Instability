"""
Web Connectivity Module

HTTP/HTTPS connectivity testing, SSL certificate validation, and web service health checks.
Part of the instability.py v3 network diagnostics suite.
"""

import urllib.request
import urllib.parse
import urllib.error
import ssl
import socket
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from colorama import Fore

def test_http_connectivity(url: str, timeout: int = 10, follow_redirects: bool = True, silent: bool = False) -> Dict[str, Any]:
    """
    Test HTTP/HTTPS connectivity to a URL.
    
    Args:
        url: URL to test (with http:// or https://)
        timeout: Request timeout in seconds
        follow_redirects: Whether to follow HTTP redirects
        silent: Suppress console output if True
        
    Returns:
        Dict containing connectivity results and response details
    """
    if not silent:
        print(f"{Fore.CYAN}Testing HTTP connectivity to {url}...{Fore.RESET}")
    
    result = {
        "success": False,
        "url": url,
        "status_code": None,
        "response_time_ms": None,
        "content_length": None,
        "content_type": None,
        "server": None,
        "final_url": None,
        "redirect_count": 0,
        "ssl_info": None,
        "error": None
    }
    
    # Ensure URL has protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        result["url"] = url

    # Explicit scheme validation
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.scheme not in ('http', 'https'):
        raise ValueError(f"Unsupported URL scheme: {parsed_url.scheme}")

    try:
        start_time = time.time()
        
        # Create request with headers
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'instability.py/3.0 (Network Diagnostics)')
        
        # Configure redirect handling
        if not follow_redirects:
            opener = urllib.request.build_opener()
            opener.add_handler(urllib.request.HTTPRedirectHandler())
        
        # Make request with proper SSL context for HTTPS
        if url.startswith('https://'):
            context = ssl.create_default_context()
            # Load system certificate store on macOS
            import platform
            if platform.system() == 'Darwin':
                # On macOS, explicitly load system certificates
                context.load_default_certs()
                # Try loading from macOS keychain
                try:
                    context.load_verify_locations('/etc/ssl/cert.pem')
                except FileNotFoundError:
                    pass
                try:
                    context.load_verify_locations('/System/Library/OpenSSL/certs/cert.pem')
                except FileNotFoundError:
                    pass
            # Ensure only secure protocols (TLS 1.2 and above) are used
            if hasattr(ssl, 'TLSVersion'):  # Python 3.7+
                context.minimum_version = ssl.TLSVersion.TLSv1_2
            else:  # For older Python versions
                context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            
            https_handler = urllib.request.HTTPSHandler(context=context)
            opener = urllib.request.build_opener(https_handler)
            with opener.open(req, timeout=timeout) as response:
                end_time = time.time()
                result["response_time_ms"] = round((end_time - start_time) * 1000, 2)
                
                # Get response details
                result["status_code"] = response.getcode()
                result["final_url"] = response.geturl()
                result["content_length"] = response.headers.get('Content-Length')
                result["content_type"] = response.headers.get('Content-Type')
                result["server"] = response.headers.get('Server')
                
                # Count redirects
                if result["final_url"] != url:
                    result["redirect_count"] = 1  # Basic redirect detection
                
                # Get SSL info for HTTPS
                if url.startswith('https://'):
                    ssl_info = _get_ssl_info_from_response(response)
                    if ssl_info:
                        result["ssl_info"] = ssl_info
                
                result["success"] = True
                
                if not silent:
                    print(f"{Fore.GREEN}✓ HTTP {result['status_code']}: {result['response_time_ms']}ms{Fore.RESET}")
                    if result["redirect_count"] > 0:
                        print(f"{Fore.YELLOW}  → Redirected to: {result['final_url']}{Fore.RESET}")
        else:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                end_time = time.time()
                result["response_time_ms"] = round((end_time - start_time) * 1000, 2)
                
                # Get response details
                result["status_code"] = response.getcode()
                result["final_url"] = response.geturl()
                result["content_length"] = response.headers.get('Content-Length')
                result["content_type"] = response.headers.get('Content-Type')
                result["server"] = response.headers.get('Server')
                
                # Count redirects
                if result["final_url"] != url:
                    result["redirect_count"] = 1  # Basic redirect detection
                
                # Get SSL info for HTTPS
                if url.startswith('https://'):
                    ssl_info = _get_ssl_info_from_response(response)
                    if ssl_info:
                        result["ssl_info"] = ssl_info
                
                result["success"] = True
                
                if not silent:
                    print(f"{Fore.GREEN}✓ HTTP {result['status_code']}: {result['response_time_ms']}ms{Fore.RESET}")
                    if result["redirect_count"] > 0:
                        print(f"{Fore.YELLOW}  → Redirected to: {result['final_url']}{Fore.RESET}")
    
    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
        result["error"] = f"HTTP {e.code}: {e.reason}"
        if not silent:
            print(f"{Fore.RED}✗ HTTP {e.code}: {e.reason}{Fore.RESET}")
    
    except urllib.error.URLError as e:
        result["error"] = f"URL Error: {str(e.reason)}"
        if not silent:
            print(f"{Fore.RED}✗ URL Error: {e.reason}{Fore.RESET}")
    
    except socket.timeout:
        result["error"] = f"Timeout after {timeout}s"
        if not silent:
            print(f"{Fore.RED}✗ Timeout after {timeout}s{Fore.RESET}")
    
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        if not silent:
            print(f"{Fore.RED}✗ Error: {e}{Fore.RESET}")
    
    return result

def check_ssl_certificate(hostname: str, port: int = 443, timeout: int = 10, silent: bool = False) -> Dict[str, Any]:
    """
    Check SSL certificate details and validity.
    
    Args:
        hostname: Hostname to check SSL certificate for
        port: SSL port (default 443)
        timeout: Connection timeout in seconds
        silent: Suppress console output if True
        
    Returns:
        Dict containing SSL certificate information
    """
    if not silent:
        print(f"{Fore.CYAN}Checking SSL certificate for {hostname}:{port}...{Fore.RESET}")
    
    result = {
        "success": False,
        "hostname": hostname,
        "port": port,
        "valid": False,
        "expired": False,
        "self_signed": False,
        "issuer": None,
        "subject": None,
        "serial_number": None,
        "not_before": None,
        "not_after": None,
        "days_until_expiry": None,
        "signature_algorithm": None,
        "key_size": None,
        "sans": [],
        "error": None
    }
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        # Ensure only secure protocols (TLS 1.2 and above) are used
        if hasattr(ssl, 'TLSVersion'):  # Python 3.7+
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        else:  # For older Python versions
            context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        
        # Connect and get certificate
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                cert_der = ssock.getpeercert(binary_form=True)
                
                if cert:
                    # Parse certificate details
                    result["issuer"] = dict(x[0] for x in cert.get('issuer', []))
                    result["subject"] = dict(x[0] for x in cert.get('subject', []))
                    result["serial_number"] = cert.get('serialNumber')
                    
                    # Parse dates
                    not_before = cert.get('notBefore')
                    not_after = cert.get('notAfter')
                    
                    if not_before:
                        result["not_before"] = not_before
                    if not_after:
                        result["not_after"] = not_after
                        
                        # Calculate days until expiry
                        try:
                            expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
                            now = datetime.now(timezone.utc)
                            days_left = (expiry_date - now).days
                            result["days_until_expiry"] = days_left
                            result["expired"] = days_left < 0
                        except ValueError:
                            pass
                    
                    # Get Subject Alternative Names
                    san_list = cert.get('subjectAltName', [])
                    result["sans"] = [name[1] for name in san_list if name[0] == 'DNS']
                    
                    # Check if self-signed
                    issuer_cn = result["issuer"].get('commonName', '')
                    subject_cn = result["subject"].get('commonName', '')
                    result["self_signed"] = issuer_cn == subject_cn
                    
                    # Additional details from DER certificate
                    if cert_der:
                        try:
                            import cryptography.x509
                            from cryptography.hazmat.backends import default_backend
                            
                            x509_cert = cryptography.x509.load_der_x509_certificate(cert_der, default_backend())
                            result["signature_algorithm"] = x509_cert.signature_algorithm_oid._name
                            
                            # Get key size if possible
                            public_key = x509_cert.public_key()
                            if hasattr(public_key, 'key_size'):
                                result["key_size"] = public_key.key_size
                                
                        except ImportError:
                            # cryptography library not available
                            pass
                    
                    result["valid"] = not result["expired"] and not result["self_signed"]
                    result["success"] = True
                    
                    if not silent:
                        status = "✓" if result["valid"] else "⚠"
                        expiry_info = f" (expires in {result['days_until_expiry']} days)" if result["days_until_expiry"] is not None else ""
                        print(f"{Fore.GREEN if result['valid'] else Fore.YELLOW}{status} SSL certificate valid{expiry_info}{Fore.RESET}")
                        
                        if result["expired"]:
                            print(f"{Fore.RED}  ⚠ Certificate expired{Fore.RESET}")
                        elif result["self_signed"]:
                            print(f"{Fore.YELLOW}  ⚠ Self-signed certificate{Fore.RESET}")
                else:
                    result["error"] = "No certificate received"
                    if not silent:
                        print(f"{Fore.RED}✗ No certificate received{Fore.RESET}")
    
    except ssl.SSLError as e:
        result["error"] = f"SSL Error: {str(e)}"
        if not silent:
            print(f"{Fore.RED}✗ SSL Error: {e}{Fore.RESET}")
    
    except socket.timeout:
        result["error"] = f"Timeout after {timeout}s"
        if not silent:
            print(f"{Fore.RED}✗ Timeout after {timeout}s{Fore.RESET}")
    
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        if not silent:
            print(f"{Fore.RED}✗ Error: {e}{Fore.RESET}")
    
    return result

def test_web_service_health(url: str, expected_status: int = 200, timeout: int = 10, silent: bool = False) -> Dict[str, Any]:
    """
    Test web service health and response characteristics.
    
    Args:
        url: URL to test for health check
        expected_status: Expected HTTP status code
        timeout: Request timeout in seconds
        silent: Suppress console output if True
        
    Returns:
        Dict containing health check results
    """
    if not silent:
        print(f"{Fore.CYAN}Health check for {url}...{Fore.RESET}")
    
    result = {
        "success": False,
        "url": url,
        "healthy": False,
        "status_code": None,
        "expected_status": expected_status,
        "response_time_ms": None,
        "headers": {},
        "content_preview": None,
        "error": None
    }
    
    try:
        start_time = time.time()
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'instability.py/3.0 (Health Check)')
        
        # Use custom SSL context for HTTPS URLs
        if url.startswith('https://'):
            context = ssl.create_default_context()
            # Ensure only secure protocols (TLS 1.2 and above) are used
            if hasattr(ssl, 'TLSVersion'):  # Python 3.7+
                context.minimum_version = ssl.TLSVersion.TLSv1_2
            else:  # For older Python versions
                context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            
            https_handler = urllib.request.HTTPSHandler(context=context)
            opener = urllib.request.build_opener(https_handler)
            with opener.open(req, timeout=timeout) as response:
                end_time = time.time()
                result["response_time_ms"] = round((end_time - start_time) * 1000, 2)
                result["status_code"] = response.getcode()
                
                # Store headers
                result["headers"] = dict(response.headers)
                
                # Read a small amount of content for preview
                try:
                    content = response.read(500)  # First 500 bytes
                    if content:
                        result["content_preview"] = content.decode('utf-8', errors='ignore')[:200]
                except Exception:
                    pass
                
                result["healthy"] = result["status_code"] == expected_status
                result["success"] = True
                
                if not silent:
                    status_color = Fore.GREEN if result["healthy"] else Fore.YELLOW
                    health_symbol = "✓" if result["healthy"] else "⚠"
                    print(f"{status_color}{health_symbol} HTTP {result['status_code']}: {result['response_time_ms']}ms{Fore.RESET}")
                    
                    if not result["healthy"]:
                        print(f"{Fore.YELLOW}  Expected {expected_status}, got {result['status_code']}{Fore.RESET}")
        else:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                end_time = time.time()
                result["response_time_ms"] = round((end_time - start_time) * 1000, 2)
                result["status_code"] = response.getcode()
                
                # Store headers
                result["headers"] = dict(response.headers)
                
                # Read a small amount of content for preview
                try:
                    content = response.read(500)  # First 500 bytes
                    if content:
                        result["content_preview"] = content.decode('utf-8', errors='ignore')[:200]
                except Exception:
                    pass
                
                result["healthy"] = result["status_code"] == expected_status
                result["success"] = True
                
                if not silent:
                    status_color = Fore.GREEN if result["healthy"] else Fore.YELLOW
                    health_symbol = "✓" if result["healthy"] else "⚠"
                    print(f"{status_color}{health_symbol} HTTP {result['status_code']}: {result['response_time_ms']}ms{Fore.RESET}")
                    
                    if not result["healthy"]:
                        print(f"{Fore.YELLOW}  Expected {expected_status}, got {result['status_code']}{Fore.RESET}")
    
    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
        result["error"] = f"HTTP {e.code}: {e.reason}"
        result["healthy"] = e.code == expected_status
        if not silent:
            health_symbol = "✓" if result["healthy"] else "✗"
            color = Fore.GREEN if result["healthy"] else Fore.RED
            print(f"{color}{health_symbol} HTTP {e.code}: {e.reason}{Fore.RESET}")
    
    except Exception as e:
        result["error"] = str(e)
        if not silent:
            print(f"{Fore.RED}✗ Error: {e}{Fore.RESET}")
    
    return result

def check_multiple_endpoints(urls: List[str], timeout: int = 10, silent: bool = False) -> Dict[str, Any]:
    """
    Check connectivity to multiple web endpoints.
    
    Args:
        urls: List of URLs to test
        timeout: Request timeout in seconds
        silent: Suppress console output if True
        
    Returns:
        Dict containing results for all endpoints
    """
    if not silent:
        print(f"{Fore.CYAN}Testing connectivity to {len(urls)} endpoints...{Fore.RESET}")
    
    result = {
        "success": False,
        "total_endpoints": len(urls),
        "successful_endpoints": 0,
        "failed_endpoints": 0,
        "average_response_time": None,
        "results": {}
    }
    
    response_times = []
    
    for url in urls:
        endpoint_result = test_http_connectivity(url, timeout=timeout, silent=True)
        result["results"][url] = endpoint_result
        
        if endpoint_result["success"]:
            result["successful_endpoints"] += 1
            if endpoint_result["response_time_ms"]:
                response_times.append(endpoint_result["response_time_ms"])
        else:
            result["failed_endpoints"] += 1
        
        if not silent:
            status = "✓" if endpoint_result["success"] else "✗"
            color = Fore.GREEN if endpoint_result["success"] else Fore.RED
            time_info = f" ({endpoint_result['response_time_ms']}ms)" if endpoint_result["response_time_ms"] else ""
            print(f"  {color}{status} {url}{time_info}{Fore.RESET}")
    
    # Calculate average response time
    if response_times:
        result["average_response_time"] = round(sum(response_times) / len(response_times), 2)
    
    result["success"] = result["successful_endpoints"] > 0
    
    # Add error message when all endpoints fail
    if result["successful_endpoints"] == 0:
        # Collect error types from failed endpoints
        error_types = []
        for url, endpoint_result in result["results"].items():
            if "error" in endpoint_result:
                error_types.append(endpoint_result["error"])
        
        if error_types:
            # Get unique error types
            unique_errors = list(set(error_types))
            if len(unique_errors) == 1:
                result["error_message"] = f"All endpoints failed: {unique_errors[0]}"
            else:
                result["error_message"] = f"All {result['total_endpoints']} endpoints failed with various errors"
        else:
            result["error_message"] = f"All {result['total_endpoints']} endpoints failed to respond"
    
    if not silent:
        success_rate = (result["successful_endpoints"] / result["total_endpoints"]) * 100
        print(f"{Fore.CYAN}Results: {result['successful_endpoints']}/{result['total_endpoints']} successful ({success_rate:.1f}%){Fore.RESET}")
        if result["average_response_time"]:
            print(f"{Fore.CYAN}Average response time: {result['average_response_time']}ms{Fore.RESET}")
        elif result["successful_endpoints"] == 0:
            print(f"{Fore.RED}Error: {result.get('error_message', 'All endpoints failed')}{Fore.RESET}")
    
    return result

def test_common_web_services(silent: bool = False) -> Dict[str, Any]:
    """
    Test connectivity to common web services for internet validation.
    
    Args:
        silent: Suppress console output if True
        
    Returns:
        Dict containing results for common web services
    """
    common_services = [
        "https://www.google.com",
        "https://www.cloudflare.com",
        "https://www.github.com",
        "https://httpbin.org/get"
    ]
    
    if not silent:
        print(f"{Fore.CYAN}Testing common web services...{Fore.RESET}")
    
    return check_multiple_endpoints(common_services, timeout=5, silent=silent)

def _get_ssl_info_from_response(response) -> Optional[Dict[str, Any]]:
    """Extract SSL information from urllib response object."""
    try:
        # Try to get SSL socket from response
        if hasattr(response, 'fp') and hasattr(response.fp, 'raw'):
            # sock = response.fp.raw._sock
            # pylint: disable=protected-access
            sock = getattr(response.fp.raw, '_sock', None)
            if hasattr(sock, 'getpeercert'):
                cert = sock.getpeercert()
                if cert:
                    return {
                        "issuer": dict(x[0] for x in cert.get('issuer', [])),
                        "subject": dict(x[0] for x in cert.get('subject', [])),
                        "version": cert.get('version'),
                        "serial_number": cert.get('serialNumber'),
                        "not_before": cert.get('notBefore'),
                        "not_after": cert.get('notAfter')
                    }
    except Exception:
        pass
    
    return None

def check_website_accessibility(domain: str, check_subdomains: bool = True, silent: bool = False) -> Dict[str, Any]:
    """
    Comprehensive website accessibility check.
    
    Args:
        domain: Domain to check (without protocol)
        check_subdomains: Whether to check common subdomains
        silent: Suppress console output if True
        
    Returns:
        Dict containing comprehensive accessibility results
    """
    if not silent:
        print(f"{Fore.CYAN}Comprehensive accessibility check for {domain}...{Fore.RESET}")
    
    result = {
        "success": False,
        "domain": domain,
        "http_accessible": False,
        "https_accessible": False,
        "redirects_to_https": False,
        "ssl_valid": False,
        "subdomains_checked": 0,
        "accessible_subdomains": [],
        "results": {}
    }
    
    # Test main domain
    http_url = f"http://{domain}"
    https_url = f"https://{domain}"
    
    # Test HTTP
    http_result = test_http_connectivity(http_url, timeout=10, silent=True)
    result["results"]["http"] = http_result
    result["http_accessible"] = http_result["success"]
    
    # Check if HTTP redirects to HTTPS
    if http_result["success"] and http_result["final_url"]:
        result["redirects_to_https"] = http_result["final_url"].startswith("https://")
    
    # Test HTTPS
    https_result = test_http_connectivity(https_url, timeout=10, silent=True)
    result["results"]["https"] = https_result
    result["https_accessible"] = https_result["success"]
    
    # Test SSL certificate if HTTPS works
    if result["https_accessible"]:
        ssl_result = check_ssl_certificate(domain, silent=True)
        result["results"]["ssl"] = ssl_result
        result["ssl_valid"] = ssl_result["valid"]
    
    # Test common subdomains if requested
    if check_subdomains:
        subdomains = ["www", "mail", "ftp", "api", "blog", "shop"]
        for subdomain in subdomains:
            subdomain_url = f"https://{subdomain}.{domain}"
            subdomain_result = test_http_connectivity(subdomain_url, timeout=5, silent=True)
            result["results"][f"subdomain_{subdomain}"] = subdomain_result
            result["subdomains_checked"] += 1
            
            if subdomain_result["success"]:
                result["accessible_subdomains"].append(f"{subdomain}.{domain}")
    
    result["success"] = result["http_accessible"] or result["https_accessible"]
    
    if not silent:
        # Print summary
        http_status = "✓" if result["http_accessible"] else "✗"
        https_status = "✓" if result["https_accessible"] else "✗"
        ssl_status = "✓" if result["ssl_valid"] else "✗" if result["https_accessible"] else "N/A"
        
        print(f"  {Fore.GREEN if result['http_accessible'] else Fore.RED}{http_status} HTTP accessible{Fore.RESET}")
        print(f"  {Fore.GREEN if result['https_accessible'] else Fore.RED}{https_status} HTTPS accessible{Fore.RESET}")
        print(f"  {Fore.GREEN if result['ssl_valid'] else Fore.RED}{ssl_status} SSL certificate valid{Fore.RESET}")
        
        if result["redirects_to_https"]:
            print(f"  {Fore.GREEN}✓ HTTP redirects to HTTPS{Fore.RESET}")
        
        if result["accessible_subdomains"]:
            print(f"  {Fore.GREEN}✓ Accessible subdomains: {', '.join(result['accessible_subdomains'])}{Fore.RESET}")
    
    return result