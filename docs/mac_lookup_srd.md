# MAC Address Manufacturer Lookup - Software Requirements Document

## Overview

This document specifies the requirements for implementing offline MAC address manufacturer lookup functionality in the Instability MCP server and chatbot. The implementation will provide two primary tools that enable users to identify network device manufacturers from MAC addresses without requiring internet connectivity for lookups.

## Core Requirements

### Primary Tools

#### 1. `fetch_latest_wireshark_manuf_file`
- Downloads the latest Wireshark manufacturer database for offline use
- Must be manually initiated by the user (never automatic)
- Stores data locally for subsequent offline lookups
- Provides fallback mechanisms when internet access is unavailable

#### 2. `mac_address_manufacturer_lookup`
- Performs offline MAC address manufacturer identification
- Supports multiple MAC address input formats
- Returns comprehensive manufacturer information when available
- Integrates with existing MCP server, command-line chatbot, and manual CLI modes

### Data Sources and Storage

#### Primary Data Source
- **Primary URL**: `https://www.wireshark.org/download/automated/data/manuf.gz` (gzipped)
- **Fallback URL**: `https://www.wireshark.org/download/automated/data/manuf` (uncompressed)
- **Local Storage**: `~/.config/instability/manuf`
- **File Format**: Plain text, Wireshark manufacturer database format

#### Fallback Data Source
- **Command**: `tshark -G manuf` (when Wireshark is locally installed)
- **Purpose**: Generate local manufacturer data when internet access is unavailable
- **Requirement**: User consent required before execution

#### Python Library Integration
- **Library**: `manuf` from PyPI (https://pypi.org/project/manuf/)
- **Purpose**: Leverage existing Wireshark integration capabilities
- **Installation**: Should be included as a dependency
- **Fallback**: Manual parsing if library is unavailable

## Technical Specifications

### MAC Address Input Format Support
The `mac_address_manufacturer_lookup` tool must accept MAC addresses in the following formats:
- Colon-delimited: `AA:BB:CC:DD:EE:FF`, `aa:bb:cc:dd:ee:ff`
- Hyphen-delimited: `AA-BB-CC-DD-EE-FF`, `aa-bb-cc-dd-ee-ff`
- Dot-delimited: `AABB.CCDD.EEFF`, `aabb.ccdd.eeff`
- No delimiters: `AABBCCDDEEFF`, `aabbccddeeff`
- Case-insensitive processing for all formats

### Output Information
When manufacturer information is found, return:
- Full manufacturer name (if available)
- Company name (if different from manufacturer name)
- City (if available)
- Country (if available)
- OUI prefix information

### File Age Management
- Check local `manuf` file age before performing lookups
- If file is older than 7 days (hardcoded), prompt user to update
- Display file age and last update information to user
- Allow user to proceed with outdated data or update file

### Internet Access Policy
- **Critical Requirement**: Never automatically access the internet
- All internet-based operations require explicit user consent
- Clearly communicate when internet access is needed
- Provide offline alternatives when possible
- Maintain tool functionality even when completely offline

## Implementation Details

### Tool Integration Requirements
- Integrate with existing MCP server tool registration system
- Support command-line chatbot mode
- Provide standalone manual CLI execution
- Follow existing tool output formatting standards
- Implement consistent error handling patterns

### Directory and File Management
- Create `~/.config/instability/` directory if it doesn't exist
- Handle file permissions appropriately
- Implement atomic file operations for downloads
- Provide clear feedback during file operations

### Error Handling Strategy
- Use try/except blocks for all external operations
- Provide informative error messages to users
- Handle network connectivity issues gracefully
- Manage file system errors (permissions, disk space, etc.)
- Continue operation when non-critical dependencies are missing

### HTTP Request Configuration
- Follow existing HTTP request patterns in codebase
- Include appropriate User-Agent headers
- Implement request timeouts
- Handle HTTP errors with user-friendly messages

## Functional Requirements

### `fetch_latest_wireshark_manuf_file` Tool

#### Core Functionality
- Download manufacturer database from official Wireshark sources
- Attempt gzipped download first, fallback to uncompressed
- Decompress gzipped files automatically
- Save to local configuration directory
- Verify file integrity after download

#### User Interaction
- Display download progress for large files
- Show file size and estimated download time
- Confirm successful download and storage location
- Provide clear error messages for failed downloads

#### Fallback Behavior
- If internet download fails, offer tshark fallback option
- Request user permission before executing tshark command
- Parse tshark output and save in compatible format
- Inform user about the source of fallback data

### `mac_address_manufacturer_lookup` Tool

#### Core Functionality
- Parse and normalize MAC address input
- Extract OUI (first 24 bits) for manufacturer lookup
- Search local manufacturer database
- Return formatted manufacturer information
- Handle cases where manufacturer is not found

#### File Availability Checks
- Verify local manufacturer file exists before lookup
- Check file age and warn if older than 7 days
- Offer to fetch latest file if none exists locally
- Provide options to proceed with outdated data

#### Lookup Process
- Normalize MAC address format for comparison
- Search manufacturer database efficiently
- Return comprehensive information when available
- Provide "Unknown manufacturer" response when not found
- Include OUI prefix in response for reference

## Integration Specifications

### MCP Server Integration
- Register tools with existing MCP server framework
- Follow established tool calling conventions
- Implement consistent response formatting
- Support silent mode for automated operations

### Command-Line Interface
- Provide standalone script execution capability
- Include proper shebang line for direct execution
- Implement argument parsing with argparse
- Support help text and usage information
- Exit with appropriate status codes

### Output Formatting
- Follow established color coding standards:
  - Green: Success messages
  - Yellow: Warnings (old file, missing data)
  - Red: Error conditions
  - Blue: Informational output
- Use consistent message formatting across tools
- Provide structured output for programmatic use
- Include timestamps for file operations

## Dependencies and Requirements

### Required Python Libraries
- `requests`: HTTP operations for file downloads
- `gzip`: Decompression of downloaded files
- `argparse`: Command-line argument parsing
- `pathlib`: File system path operations
- `manuf`: MAC address manufacturer lookups (PyPI package)

### Optional Dependencies
- `colorama` or ANSI codes: Terminal color output

### System Requirements
- Python 3.6+ compatibility
- Write access to user configuration directory
- Optional: Wireshark/tshark installation for fallback functionality

## Security Considerations

### Network Security
- Validate downloaded file integrity when possible

### File System Security
- Create files with appropriate permissions
- Prevent directory traversal attacks
- Handle symlink attacks in configuration directory
- Validate file paths before operations

### Privacy Considerations
- No automatic transmission of user data
- Local-only MAC address processing
- Clear communication about internet access needs
- Respect user consent for all network operations

## Testing Requirements

### Unit Testing
- Test MAC address format parsing and normalization
- Verify manufacturer database loading and searching
- Test file age calculation and comparison
- Validate error handling for various failure scenarios

### Integration Testing
- Test tool registration with MCP server
- Verify command-line interface functionality
- Test file download and decompression operations
- Validate fallback mechanisms

### Edge Case Testing
- Handle malformed MAC addresses gracefully
- Test behavior with empty or corrupted manufacturer files
- Verify operation without internet connectivity
- Test with various file system permission scenarios

## Performance Requirements

### Response Time
- MAC address lookups should complete within 100ms
- File downloads should show progress for operations >5 seconds
- Database loading should be optimized for repeated lookups

### Resource Usage
- Minimize memory footprint for manufacturer database
- Implement efficient search algorithms for large datasets
- Cache parsed data structures when appropriate

## Documentation Requirements

### User Documentation
- Clear usage examples for both tools
- Explanation of supported MAC address formats
- Troubleshooting guide for common issues
- Description of fallback mechanisms

### Developer Documentation
- Code comments following Google docstring style
- Function parameter and return value documentation
- Integration points with existing codebase
- Error handling and exception documentation

## Success Criteria

### Functional Success
- Both tools integrate seamlessly with existing Instability framework
- MAC address lookups work reliably with local manufacturer database
- File download and update mechanisms function correctly
- Fallback options provide alternative data sources when needed

### Usability Success
- Tools are discoverable through existing help systems
- Error messages are clear and actionable
- User consent mechanisms are intuitive and non-intrusive
- Output formatting is consistent with existing tools

### Reliability Success
- Tools function correctly without internet connectivity
- Graceful degradation when dependencies are missing
- Robust error handling for all failure scenarios
- Consistent behavior across different operating systems