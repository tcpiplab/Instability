# Software Requirements Document: Email Diagnostics Module

## Project Overview

### Purpose
Add comprehensive email server connectivity diagnostics to the Instability v3 project by implementing SMTP and IMAP connectivity testing for major email providers. This module will provide network administrators and pentesters with the ability to quickly assess email infrastructure availability and identify potential connectivity issues.

### Integration Target
This functionality will be implemented as a new module `network/email_diagnostics.py` within the existing Instability v3 project structure, following the established coding style guidelines and integrating with existing service check summarization and memory management systems.

## Functional Requirements

### Core Functionality

#### SMTP Connectivity Testing
Test outbound email server connectivity by attempting socket connections to major SMTP providers on secure port 587 (SMTP submission port). This testing verifies that the local network can reach email submission servers, which is critical for troubleshooting email sending issues.

#### IMAP Connectivity Testing  
Test inbound email server connectivity by attempting socket connections to major IMAP providers on secure port 993 (IMAPS). This testing verifies that the local network can reach email retrieval servers, which is essential for diagnosing email client connectivity problems.

#### Email Provider Coverage
Support connectivity testing for these nine major email providers:
- Gmail (smtp.gmail.com:587, imap.gmail.com:993)
- Outlook/O365 (smtp.office365.com:587, outlook.office365.com:993)
- Yahoo (smtp.mail.yahoo.com:587, imap.mail.yahoo.com:993)
- iCloud Mail (smtp.mail.me.com:587, imap.mail.me.com:993)
- AOL Mail (smtp.aol.com:587, imap.aol.com:993)
- Zoho Mail (smtp.zoho.com:587, imap.zoho.com:993)
- Mail.com (smtp.mail.com:587, imap.mail.com:993)
- GMX Mail (smtp.gmx.com:587, imap.gmx.com:993)
- Fastmail (smtp.fastmail.com:587, imap.fastmail.com:587)

### Tool Implementation Requirements

#### Function Specifications

**check_smtp_connectivity(silent: bool = False) -> str**
- Test connectivity to all SMTP servers using socket connections
- Use 10-second timeout per connection attempt
- Return formatted summary of reachable and unreachable servers
- Integrate with existing service check summarization system
- Support silent mode for automated testing

**check_imap_connectivity(silent: bool = False) -> str**
- Test connectivity to all IMAP servers using socket connections  
- Use 10-second timeout per connection attempt
- Return formatted summary of reachable and unreachable servers
- Integrate with existing service check summarization system
- Support silent mode for automated testing

**check_all_email_services(silent: bool = False) -> str**
- Combined function that tests both SMTP and IMAP connectivity
- Provide comprehensive email infrastructure assessment
- Return unified summary of all email service connectivity
- Primary function for general email diagnostics

#### Error Handling Requirements
- Use try/except blocks for all socket operations
- Capture and report specific connection errors (timeout, refused, unreachable)
- Continue testing remaining servers if individual servers fail
- Provide meaningful error messages without exposing sensitive system information
- Handle DNS resolution failures gracefully

#### Output Format Requirements
- Use consistent status indicators: [OK], [FAIL], [TIMEOUT], [REFUSED]
- Color coding using colorama: Green for success, Red for failures, Yellow for warnings
- Structured output showing reachable vs unreachable servers
- Include specific error descriptions for failed connections
- Summary statistics (X of Y servers reachable)

## Technical Implementation

### Module Structure

#### File Location
`network/email_diagnostics.py`

#### Required Imports
```python
import socket
from typing import Dict, Tuple, List
from colorama import Fore, Style
```

#### Server Configuration
Define server configurations as module-level dictionaries for easy maintenance:

```python
SMTP_SERVERS: Dict[str, Tuple[str, int]] = {
    "Gmail": ("smtp.gmail.com", 587),
    "Outlook/O365": ("smtp.office365.com", 587),
    # ... additional providers
}

IMAP_SERVERS: Dict[str, Tuple[str, int]] = {
    "Gmail": ("imap.gmail.com", 993),
    "Outlook/O365": ("outlook.office365.com", 993),
    # ... additional providers
}
```

#### Core Testing Logic
Implement socket-based connectivity testing with proper resource management:

```python
def _test_server_connectivity(hostname: str, port: int, timeout: int = 10) -> Tuple[bool, str]:
    """Test connectivity to a specific server and port"""
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return True, "Connected successfully"
    except socket.timeout:
        return False, "Connection timeout"
    except socket.gaierror as e:
        return False, f"DNS resolution failed: {e}"
    except ConnectionRefusedError:
        return False, "Connection refused"
    except Exception as e:
        return False, f"Connection failed: {e}"
```

### Integration Requirements

#### Tools Registry Integration
Add email diagnostics as a new tool category in the tools registry system:

```python
def get_module_tools():
    from core.tools_registry import ToolMetadata, ParameterInfo, ParameterType, ToolCategory
    return {
        "check_smtp_connectivity": ToolMetadata(
            name="check_smtp_connectivity",
            function_name="check_smtp_connectivity",
            module_path="network.email_diagnostics",
            description="Test SMTP server connectivity for major email providers",
            category=ToolCategory.EMAIL_DIAGNOSTICS,
            parameters={
                "silent": ParameterInfo(ParameterType.BOOLEAN, default=False)
            }
        ),
        "check_imap_connectivity": ToolMetadata(
            name="check_imap_connectivity", 
            function_name="check_imap_connectivity",
            module_path="network.email_diagnostics",
            description="Test IMAP server connectivity for major email providers",
            category=ToolCategory.EMAIL_DIAGNOSTICS,
            parameters={
                "silent": ParameterInfo(ParameterType.BOOLEAN, default=False)
            }
        ),
        "check_all_email_services": ToolMetadata(
            name="check_all_email_services",
            function_name="check_all_email_services", 
            module_path="network.email_diagnostics",
            description="Comprehensive email infrastructure connectivity assessment",
            category=ToolCategory.EMAIL_DIAGNOSTICS,
            parameters={
                "silent": ParameterInfo(ParameterType.BOOLEAN, default=False)
            }
        )
    }
```

#### Service Check Integration
Integrate with the existing service check summarization system by importing and using the appropriate functions for generating summaries and updating memory.

#### Memory Integration
Update network state memory files with email connectivity status to maintain historical records of email infrastructure availability.

## Non-Functional Requirements

### Performance Requirements
- Complete testing of all 18 servers (9 SMTP + 9 IMAP) within 60 seconds
- Use concurrent connections where possible to reduce total testing time
- Implement reasonable timeouts to prevent hanging on unresponsive servers
- Minimize memory usage during testing operations

### Reliability Requirements
- Function correctly even during partial network outages
- Gracefully handle DNS resolution failures
- Continue testing remaining servers if some fail
- Provide consistent results across multiple test runs

### Usability Requirements
- Clear, scannable output format suitable for professional environments
- Meaningful error messages that aid in troubleshooting
- Silent mode support for automated testing and scripting
- Integration with existing Instability v3 command interface

### Security Requirements
- No authentication attempts or credential handling
- No logging of sensitive connection information
- Read-only network operations (no sending actual emails)
- Safe socket handling with proper resource cleanup

## Testing Requirements

### Unit Testing
Create comprehensive unit tests covering:
- Individual server connectivity testing
- Error handling for various failure modes
- Output formatting and summarization
- Integration with existing systems

### Integration Testing
- Verify proper integration with tools registry
- Test service check summarization integration
- Validate memory system updates
- Confirm compatibility with existing command interface

### Manual Testing Scenarios
- Test during complete internet outage (should fail gracefully)
- Test with partial connectivity (some servers reachable, others not)
- Test with DNS resolution issues
- Test with firewall blocking specific ports
- Validate output formatting across different terminal environments

## Future Enhancement Considerations

### Extensibility Design
- Modular design to support additional email providers
- Framework for adding other email protocols (POP3, Exchange Web Services)
- Capability to add email security testing (TLS certificate validation)
- Support for custom email server testing beyond major providers

### Configuration Options
- User-configurable server lists
- Adjustable timeout values
- Custom port testing capabilities
- Provider-specific testing configurations

This SRD provides comprehensive guidance for implementing email diagnostics functionality within the Instability v3 project while maintaining consistency with existing code patterns and architectural decisions.