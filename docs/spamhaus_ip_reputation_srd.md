# Spamhaus IP Reputation Check - Software Requirements Document

## 1. Overview

### Purpose
This document specifies requirements for adding Spamhaus DNS-based blacklist checking functionality to the existing IP reputation system in the Instability v3 pentesting framework. This enhancement will supplement the current AbuseIPDB integration with additional threat intelligence from Spamhaus blacklists.

### Scope
The Spamhaus reputation check will be implemented as an additional function within the existing `network_tools/check_external_ip.py` module, maintaining full compatibility with the current AbuseIPDB functionality while providing expanded IP reputation coverage.

## 2. Functional Requirements

### 2.1 Core Functionality
The tool shall provide the following new capabilities:

**DNS-Based Blacklist Queries**: Query Spamhaus blacklists using DNS resolution to determine if an IP address is listed on known spam/threat databases.

**Multiple Spamhaus Lists**: Check against the following Spamhaus blacklists:
- **SBL** (Spamhaus Block List): Known spam sources
- **CSS** (Composite Spamhaus Source): Composite spam sources  
- **PBL** (Policy Block List): IP ranges that should not send email

**Integration with Existing Flow**: Seamlessly integrate with the current `main()` function to provide consolidated reputation reporting alongside AbuseIPDB results.

**Consistent Output Formatting**: Follow existing colorama-based output formatting patterns for consistency with current reputation display.

### 2.2 Technical Implementation

#### 2.2.1 New Functions
The implementation shall add the following functions to `network_tools/check_external_ip.py`:

**`check_spamhaus_blacklists(ip: str) -> Dict[str, Dict[str, Any]]`**
- Perform DNS-based queries against Spamhaus blacklists
- Return structured results for each blacklist checked
- Handle DNS resolution errors gracefully
- Use standard library `socket` module for DNS queries

**`analyze_spamhaus_reputation(spamhaus_data: Dict[str, Dict[str, Any]]) -> str`**
- Format Spamhaus results for human-readable display
- Apply appropriate colorama formatting (red for blacklisted, green for clean)
- Return formatted string consistent with existing `analyze_ip_reputation()` output

#### 2.2.2 DNS Query Implementation
The DNS-based blacklist checking shall:

1. **Reverse IP Address**: Convert `1.2.3.4` to `4.3.2.1` format
2. **Construct DNS Queries**: Append reversed IP to Spamhaus domains:
   - `4.3.2.1.sbl.spamhaus.org`
   - `4.3.2.1.css.spamhaus.org` 
   - `4.3.2.1.pbl.spamhaus.org`
3. **Perform DNS Resolution**: Use `socket.gethostbyname()` to test resolution
4. **Interpret Results**: 
   - Successful resolution = IP is blacklisted
   - DNS resolution failure = IP is clean (not listed)

### 2.3 Integration Requirements

#### 2.3.1 Existing Function Modifications
**Minimal Changes to `main()` Function**:
- Add call to `check_spamhaus_blacklists()` after AbuseIPDB check
- Integrate Spamhaus results into output display
- Maintain backward compatibility - function signature unchanged
- Preserve existing behavior when AbuseIPDB API key is not available

#### 2.3.2 Output Format Integration
The consolidated output shall display:
1. External IP address
2. AbuseIPDB reputation (if API key available)
3. Spamhaus blacklist status (always performed)
4. Combined risk assessment summary

#### 2.3.3 Error Handling
Follow established error handling patterns:
- Use try/except blocks with specific exception types
- Graceful degradation if DNS queries fail
- Informative error messages using colorama formatting
- Continue execution if Spamhaus check fails

## 3. Technical Specifications

### 3.1 Dependencies
**No New Dependencies Required**:
- Use standard library `socket` module for DNS queries
- Maintain existing `requests`, `colorama` dependencies
- Follow "prefer standard library" coding guideline

### 3.2 Data Structures

#### 3.2.1 Spamhaus Results Format
```python
{
    "sbl": {
        "listed": bool,
        "query": str,
        "response": str or None,
        "error": str or None
    },
    "css": {
        "listed": bool, 
        "query": str,
        "response": str or None,
        "error": str or None
    },
    "pbl": {
        "listed": bool,
        "query": str, 
        "response": str or None,
        "error": str or None
    }
}
```

### 3.3 Function Signatures

#### 3.3.1 New Functions
```python
def check_spamhaus_blacklists(ip: str) -> Dict[str, Dict[str, Any]]:
    """
    Check IP address against Spamhaus DNS-based blacklists.
    
    Args:
        ip (str): IP address to check (e.g., "192.168.1.1")
        
    Returns:
        Dict[str, Dict[str, Any]]: Results for each blacklist with status and details
        
    Raises:
        ValueError: If IP address format is invalid
    """
    pass

def analyze_spamhaus_reputation(spamhaus_data: Dict[str, Dict[str, Any]]) -> str:
    """
    Format Spamhaus blacklist results for display.
    
    Args:
        spamhaus_data (Dict[str, Dict[str, Any]]): Results from check_spamhaus_blacklists()
        
    Returns:
        str: Formatted analysis of Spamhaus blacklist status
    """
    pass
```

#### 3.3.2 Modified Functions
```python
def main(silent: bool = False, polite: bool = False) -> str:
    """
    Get external IP and check reputation with AbuseIPDB and Spamhaus.
    
    Args:
        silent (bool): If True, suppress detailed output  
        polite (bool): If True, use more polite language in output
        
    Returns:
        str: External IP with comprehensive reputation analysis
    """
    # Existing functionality preserved
    # Add Spamhaus checking integration
    pass
```

## 4. Implementation Approach

### 4.1 Development Steps

#### Phase 1: Core DNS Function Implementation
1. Implement `check_spamhaus_blacklists()` function
2. Add IP address validation and reversal logic
3. Implement DNS query loop for each Spamhaus list
4. Add comprehensive error handling

#### Phase 2: Output Formatting
1. Implement `analyze_spamhaus_reputation()` function
2. Apply colorama formatting consistent with existing style
3. Create summary logic for overall blacklist status

#### Phase 3: Integration
1. Modify `main()` function to call Spamhaus checking
2. Integrate results into consolidated output
3. Test compatibility with existing AbuseIPDB functionality

#### Phase 4: Testing and Validation
1. Test with known blacklisted IPs (if available)
2. Test with clean IPs 
3. Test error conditions (network failures, invalid IPs)
4. Verify output formatting consistency

### 4.2 Code Organization
Following the established coding style:

**Function Placement**: Add new functions before existing `main()` function
**Import Organization**: No new imports required (use standard library `socket`)
**Error Handling**: Use specific exception types and informative messages
**Type Hints**: Apply comprehensive type hints to all function parameters and returns
**Documentation**: Use Google-style docstrings for all new functions

## 5. Testing Requirements

### 5.1 Unit Testing
Create test cases for:
- IP address reversal logic
- DNS query construction 
- Error handling for network failures
- Invalid IP address handling
- Output formatting verification

### 5.2 Integration Testing  
Verify:
- Compatibility with existing AbuseIPDB functionality
- Proper output formatting and colorama integration
- Silent mode operation
- Error condition handling

### 5.3 Manual Testing
Test with:
- Current external IP address
- Known clean IP addresses
- Test IP addresses (if any known blacklisted ones available)
- Network disconnected scenarios

## 6. Configuration and Deployment

### 6.1 Environment Configuration
**No New Environment Variables Required**:
- Spamhaus DNS queries require no API keys
- No additional configuration needed
- Maintains existing ABUSEIPDB_API_KEY environment variable support

### 6.2 Backward Compatibility
**Full Backward Compatibility Required**:
- Existing function signatures unchanged
- Tool registration metadata unchanged  
- Command-line interface unchanged
- Output format enhanced but not breaking

## 7. Performance Considerations

### 7.1 DNS Query Optimization
- Implement reasonable timeout for DNS queries (5 seconds default)
- Perform queries sequentially to avoid overwhelming DNS servers
- Cache results within single execution (if multiple checks performed)

### 7.2 Network Failure Handling
- Graceful degradation when DNS servers unreachable
- Clear messaging about partial results if some queries fail
- Continue with available results rather than failing completely

## 8. Security Considerations

### 8.1 DNS Security
- Use system DNS resolver (no custom DNS server configuration)
- No sensitive data transmitted (only IP addresses)
- DNS queries are standard, non-intrusive network traffic

### 8.2 Information Disclosure
- Results displayed locally only
- No data transmitted to third-party APIs beyond standard DNS queries
- Maintains existing security posture of the tool

## 9. Success Criteria

### 9.1 Functional Success
- [x] IP addresses successfully checked against all three Spamhaus lists
- [x] DNS-based queries working reliably  
- [x] Results integrated into existing output format
- [x] Error conditions handled gracefully
- [x] Backward compatibility maintained

### 9.2 Code Quality Success
- [x] Follows all established coding style guidelines
- [x] Comprehensive type hints applied
- [x] Google-style docstrings for all functions
- [x] Proper error handling with specific exceptions
- [x] No new external dependencies introduced

## 10. Future Enhancements

### 10.1 Additional Blacklists
Future versions could add support for:
- Additional DNS-based blacklists (SURBL, URIBL)
- Other Spamhaus lists (XBL, DBL)
- Regional threat intelligence sources

### 10.2 Configuration Options
Potential future configuration:
- Custom DNS timeout settings
- Selective blacklist checking (skip certain lists)
- DNS server specification for queries

### 10.3 Output Enhancements  
Future output improvements:
- JSON output format option
- Severity scoring across all reputation sources
- Historical tracking of reputation changes

## 11. Appendix

### 11.1 Spamhaus Blacklist Details

**SBL (Spamhaus Block List)**:
- Lists IP addresses of known spam sources
- Includes compromised machines and spam operations
- Query format: `{reversed-ip}.sbl.spamhaus.org`

**CSS (Composite Spamhaus Source)**:  
- Composite list combining multiple Spamhaus sources
- More comprehensive than individual lists
- Query format: `{reversed-ip}.css.spamhaus.org`

**PBL (Policy Block List)**:
- Lists IP ranges that should not send email directly
- Includes residential and dynamic IP ranges
- Query format: `{reversed-ip}.pbl.spamhaus.org`

### 11.2 DNS Response Codes
Standard DNS blacklist response codes:
- `127.0.0.2` - SBL listings
- `127.0.0.3` - CSS listings  
- `127.0.0.4` - PBL listings
- No response - IP is not listed (clean)

### 11.3 Implementation Example
```python
# Example DNS query construction
ip = "192.168.1.1"
reversed_ip = ".".join(ip.split(".")[::-1])  # "1.1.168.192"
query_host = f"{reversed_ip}.sbl.spamhaus.org"

try:
    result = socket.gethostbyname(query_host)
    # IP is blacklisted - result contains response code
except socket.gaierror:
    # IP is clean - DNS query failed (expected for clean IPs)
```