"""
Unified Tool Registration System for Instability v3

Provides a centralized registry for all tools with automatic discovery,
consistent metadata, and unified execution interface.
"""

import importlib
import inspect
import os
import re
from dataclasses import dataclass, field
from types import ModuleType
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum

class ParameterType(Enum):
    """Supported parameter types for tool functions"""
    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    LIST = "list"
    DICT = "dict"

class ToolCategory(Enum):
    """Tool categories for organization"""
    NETWORK_DIAGNOSTICS = "network_diagnostics"
    PENTESTING = "pentesting"
    SYSTEM_INFO = "system_info"
    DNS = "dns"
    WEB = "web"
    SECURITY = "security"
    EMAIL_DIAGNOSTICS = "email_diagnostics"

@dataclass
class ParameterInfo:
    """Information about a tool parameter"""
    param_type: ParameterType
    required: bool = False
    default: Any = None
    description: str = ""
    choices: Optional[List[str]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None

@dataclass
class ToolMetadata:
    """Complete metadata for a tool"""
    name: str
    function_name: str
    module_path: str
    description: str
    category: ToolCategory
    parameters: Dict[str, ParameterInfo] = field(default_factory=dict)
    modes: List[str] = field(default_factory=lambda: ["manual", "chatbot"])
    requires_external_tool: bool = False
    external_tool_name: Optional[str] = None
    privilege_required: bool = False
    aliases: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    function_ref: Optional[Callable] = None

class ToolRegistry:
    """
    Centralized registry for all tools with automatic discovery
    and unified execution interface.
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}
        self._categories: Dict[ToolCategory, List[str]] = {}
        self._external_tools: Dict[str, Any] = {}
        self._discovery_paths = [
            "network",
            "pentest", 
            "memory",
            "core"
        ]
        self._additional_modules = [
            "network_diagnostics"  # Legacy module not in standard paths
        ]
        
        # Initialize categories
        for category in ToolCategory:
            self._categories[category] = []

    @staticmethod
    def _is_safe_module_path(module_path: str) -> bool:
        """Validate if a module path is safe to import.
        :param module_path:
        :return:
        """
        # Whitelist of allowed module paths/prefixes
        safe_prefixes = {
                "network", "pentest", "memory", "core",
                "network_diagnostics", "pentest.tool_detector"
                }

        parts = module_path.split('.')
        return parts[0] in safe_prefixes


    def register_tool(self, metadata: ToolMetadata) -> None:
        """
        Register a tool with the registry.
        
        Args:
            metadata: Complete tool metadata
        """
        # Validate metadata
        if not metadata.name:
            raise ValueError("Tool name is required")
        
        if not metadata.function_name:
            raise ValueError("Function name is required")
        
        if not metadata.module_path:
            raise ValueError("Module path is required")

        # Validate module path to prevent unsafe imports such as absolute imports like "os" or "sys" from malicious user input or developer error
        if self._is_safe_module_path(metadata.module_path):
            module = importlib.import_module(metadata.module_path)
            metadata.function_ref = getattr(module, metadata.function_name)
        else:
            raise ValueError(f"Unsafe module path: {metadata.module_path}")

        # Load function reference if not provided
        if metadata.function_ref is None:
            try:
                module = importlib.import_module(metadata.module_path)
                metadata.function_ref = getattr(module, metadata.function_name)
            except (ImportError, AttributeError) as e:
                metadata.function_ref = None  # Silently set to None for failed imports
        
        # Register tool
        self._tools[metadata.name] = metadata
        
        # Add to category
        if metadata.category not in self._categories:
            self._categories[metadata.category] = []
        self._categories[metadata.category].append(metadata.name)
        
        # Register aliases
        for alias in metadata.aliases:
            if alias not in self._tools:
                self._tools[alias] = metadata
    
    def discover_module_tools(self, module_path: str) -> Dict[str, ToolMetadata]:
        """
        Discover tools from a module by looking for get_module_tools() function.
        
        Args:
            module_path: Python module path (e.g., "network.dns_diagnostics")
            
        Returns:
            Dictionary of discovered tools
        """

        try:

            # Validate module path to prevent unsafe imports such as absolute imports like "os" or "sys" from malicious user input or developer error
            if self._is_safe_module_path(module_path):
                module = importlib.import_module(module_path)
            else:
                raise ValueError(f"Unsafe module path: {module_path}")
            
            # Look for get_module_tools function
            if hasattr(module, 'get_module_tools'):
                tools = module.get_module_tools()
                for name, metadata in tools.items():
                    self.register_tool(metadata)
                return tools
            
            # Fallback: scan for functions with proper signatures
            discovered = {}
            excluded_functions = {
                'get_tool_registry',
                # Error handling utilities
                'create_error_response', 'create_input_error', 'create_network_error', 
                'create_system_error', 'create_execution_error',
                # Parsing utilities
                'parse_ping_output', 'parse_traceroute_output', 'parse_unix_interface_ip',
                'parse_unix_interfaces', 'parse_windows_interface_ip', 'parse_windows_interfaces',
                'parse_version_output', 'parse_network_state_markdown', 'parse_target_scope_markdown',
                # Validation utilities
                'is_valid_ip', 'get_timeout',
                # Cache/memory utilities
                'cache_tool_result', 'get_cached_result', 'load_session_cache', 'save_session_cache',
                'load_tool_inventory_cache', 'save_tool_inventory_cache',
                # Formatting utilities
                'format_tool_inventory_summary', 'format_targets_section', 'update_markdown_sections',
                # Test functions
                'test_layer2_diagnostics', 'test_layer3_diagnostics', 'test_tool_detector', 'test_memory_manager',
                # Standard library functions
                'dataclass', 'field',
                # Internal tool detector utilities
                'colorama_init', 'check_predefined_paths', 'check_tool_in_path', 'detect_tool_installation',
                'get_platform_install_command', 'get_tool_version', 'print_tool_recommendations',
                'get_available_tools', 'get_missing_tools', 'get_tools_by_category',
                # Memory management functions that are too low-level for direct use
                'create_default_network_state', 'create_default_target_scope', 'create_empty_session_cache',
                'get_memory_dir', 'initialize_memory_files', 'read_network_state', 'read_target_scope',
                'update_network_state', 'update_target_scope',
                # Low-level utilities that should be wrapped by higher-level tools
                'get_hostname_for_ip', 'detect_local_network'
            }
            for name, obj in inspect.getmembers(module, inspect.isfunction):
                if name.startswith('_') or name in excluded_functions:
                    continue
                
                # Create basic metadata from function
                sig = inspect.signature(obj)
                doc = inspect.getdoc(obj) or f"Function {name} from {module_path}"
                
                # Extract parameters
                parameters = {}
                for param_name, param in sig.parameters.items():
                    param_info = ParameterInfo(
                        param_type=ParameterType.STRING,  # Default type
                        required=param.default == inspect.Parameter.empty,
                        default=param.default if param.default != inspect.Parameter.empty else None,
                        description=f"Parameter {param_name}"
                    )
                    parameters[param_name] = param_info
                
                # Determine category from module path
                category = ToolCategory.NETWORK_DIAGNOSTICS
                if "pentest" in module_path:
                    category = ToolCategory.PENTESTING
                elif "dns" in module_path:
                    category = ToolCategory.DNS
                elif "web" in module_path:
                    category = ToolCategory.WEB
                
                metadata = ToolMetadata(
                    name=name,
                    function_name=name,
                    module_path=module_path,
                    description=doc.split('\n')[0],  # First line of docstring
                    category=category,
                    parameters=parameters,
                    function_ref=obj
                )
                
                discovered[name] = metadata
                self.register_tool(metadata)
            
            return discovered
            
        except ImportError as e:
            return {}  # Silently return empty dict for failed imports
    
    def auto_discover_tools(self) -> None:
        """
        Automatically discover tools from all known modules.
        """
        for base_path in self._discovery_paths:
            try:
                # Import base module
                base_module = importlib.import_module(base_path)
                base_dir = os.path.dirname(base_module.__file__)
                
                # Find all Python files in the module directory
                for filename in os.listdir(base_dir):
                    if filename.endswith('.py') and not filename.startswith('_'):
                        module_name = filename[:-3]  # Remove .py
                        module_path = f"{base_path}.{module_name}"

                        # Validate module path to prevent unsafe imports such as absolute imports like "os" or "sys" from malicious user input or developer error
                        if self._is_safe_module_path(module_path):
                            self.discover_module_tools(module_path)
                        
            except (ImportError, FileNotFoundError, AttributeError) as e:
                pass  # Silently skip missing modules during auto-discovery
        
        # Discover additional standalone modules
        for module_path in self._additional_modules:
            try:
                # Validate module path to prevent unsafe imports such as absolute imports like "os" or "sys" from malicious user input or developer error
                if self._is_safe_module_path(module_path):
                    self.discover_module_tools(module_path)
            except Exception as e:
                pass  # Silently skip modules that can't be imported


    def integrate_external_tools(self) -> None:
        """
        Integrate external tool detection with registry.
        """
        try:
            # Suppress stdout during tool detection to prevent MCP interference
            import contextlib
            import io
            
            with contextlib.redirect_stdout(io.StringIO()):
                from pentest.tool_detector import scan_for_tools
                external_tools_inventory = scan_for_tools()
            
            # Extract the tools dictionary from the inventory structure
            self._external_tools = external_tools_inventory.get("tools", {})
            
            # Register external tools as metadata entries
            for tool_name, tool_info in self._external_tools.items():
                if tool_info.get("found", False):
                    # Create metadata for external tool
                    metadata = ToolMetadata(
                        name=tool_name,
                        function_name=f"run_{tool_name}_scan",
                        module_path=f"pentest.{tool_name}_wrapper",
                        description=f"External {tool_name} tool",
                        category=ToolCategory.PENTESTING,
                        requires_external_tool=True,
                        external_tool_name=tool_name,
                        modes=["manual", "chatbot"]
                    )
                    
                    # Try to find wrapper function
                    try:

                        # Validate module path to prevent unsafe imports such as absolute imports like "os" or "sys" from malicious user input or developer error
                        if self._is_safe_module_path(f"pentest.{tool_name}_wrapper"):
                            wrapper_module: ModuleType = importlib.import_module(f"pentest.{tool_name}_wrapper")

                            if hasattr(wrapper_module, f"run_{tool_name}_scan"):
                                metadata.function_ref = getattr(wrapper_module, f"run_{tool_name}_scan")
                                self.register_tool(metadata)

                    except ImportError:
                        # Tool detected but no wrapper available
                        pass
                        
        except ImportError:
            pass  # Silently skip if tool detector not available
    
    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        """
        Get tool metadata by name or alias.
        
        Args:
            name: Tool name or alias
            
        Returns:
            Tool metadata if found, None otherwise
        """
        return self._tools.get(name)
    
    def get_available_tools(self, 
                          mode: str = "all", 
                          category: Optional[ToolCategory] = None,
                          external_only: bool = False) -> Dict[str, ToolMetadata]:
        """
        Get available tools with optional filtering.
        
        Args:
            mode: Mode filter ("manual", "chatbot", "all")
            category: Category filter
            external_only: Only return tools that require external tools
            
        Returns:
            Dictionary of available tools
        """
        result = {}
        
        for name, metadata in self._tools.items():
            # Skip aliases (they point to same metadata object)
            if name != metadata.name:
                continue
                
            # Mode filter
            if mode != "all" and mode not in metadata.modes:
                continue
            
            # Category filter
            if category and metadata.category != category:
                continue
            
            # External tool filter
            if external_only and not metadata.requires_external_tool:
                continue
            
            # Check if external tool is available if required
            if metadata.requires_external_tool:
                if metadata.external_tool_name not in self._external_tools:
                    continue
                if not self._external_tools[metadata.external_tool_name].get("found", False):
                    continue
            
            result[name] = metadata
        
        return result
    
    def get_tools_by_category(self, category: ToolCategory) -> List[ToolMetadata]:
        """
        Get all tools in a specific category.
        
        Args:
            category: Tool category
            
        Returns:
            List of tool metadata
        """
        return [self._tools[name] for name in self._categories.get(category, [])]
    
    def execute_tool(self, 
                    tool_name: str, 
                    parameters: Optional[Dict[str, Any]] = None,
                    mode: str = "manual") -> Dict[str, Any]:
        """
        Execute a tool with unified interface.
        
        Args:
            tool_name: Name of tool to execute
            parameters: Parameters to pass to tool
            mode: Execution mode ("manual" or "chatbot")
            
        Returns:
            Standardized tool result
        """
        from core.error_handling import create_error_response, ErrorType, ErrorCode
        
        # Get tool metadata
        metadata = self.get_tool(tool_name)
        if not metadata:
            return create_error_response(
                ErrorType.INPUT,
                ErrorCode.INVALID_TARGET,
                f"Tool '{tool_name}' not found",
                tool_name="tool_registry"
            )
        
        # Check if tool is available for this mode
        if mode not in metadata.modes:
            return create_error_response(
                ErrorType.INPUT,
                ErrorCode.INVALID_TARGET,
                f"Tool '{tool_name}' not available in {mode} mode",
                tool_name="tool_registry"
            )
        
        # Check external tool availability
        if metadata.requires_external_tool:
            if metadata.external_tool_name not in self._external_tools:
                return create_error_response(
                    ErrorType.SYSTEM,
                    ErrorCode.TOOL_MISSING,
                    f"External tool '{metadata.external_tool_name}' not found",
                    tool_name=tool_name
                )
        
        # Validate and prepare parameters
        if parameters is None:
            parameters = {}
        
        # Filter parameters to only include those defined in metadata
        filtered_parameters = {}
        for param_name, param_value in parameters.items():
            if param_name in metadata.parameters:
                filtered_parameters[param_name] = param_value
        
        # Validate required parameters
        for param_name, param_info in metadata.parameters.items():
            if param_info.required and param_name not in filtered_parameters:
                return create_error_response(
                    ErrorType.INPUT,
                    ErrorCode.MISSING_PARAMETER,
                    f"Required parameter '{param_name}' missing",
                    tool_name=tool_name
                )
        
        # Execute tool
        if metadata.function_ref:
            try:
                # Check if running in MCP mode - only force silent mode
                if os.environ.get('MCP_MODE') == '1':
                    # Force silent mode for MCP to prevent Claude Desktop crashes
                    if 'silent' in metadata.parameters:
                        filtered_parameters['silent'] = True
                
                # Execute tool normally - let MCP server handle stdout suppression
                result = metadata.function_ref(**filtered_parameters)
                
                # Sanitize output for MCP compatibility
                if os.environ.get('MCP_MODE') == '1':
                    result = self._sanitize_for_mcp(result)
                
                return result
            except Exception as e:
                return create_error_response(
                    ErrorType.EXECUTION,
                    ErrorCode.COMMAND_FAILED,
                    f"Tool execution failed: {str(e)}",
                    tool_name=tool_name
                )
        else:
            return create_error_response(
                ErrorType.SYSTEM,
                ErrorCode.TOOL_MISSING,
                f"Tool function not available",
                tool_name=tool_name
            )
    
    def _sanitize_for_mcp(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean tool output for MCP compatibility by removing terminal colors
        and ensuring JSON-serializable content.
        
        Args:
            result: Tool result dictionary
            
        Returns:
            Sanitized result dictionary
        """
        if not isinstance(result, dict):
            return result
        
        sanitized = {}
        for key, value in result.items():
            if isinstance(value, str):
                # Strip ANSI color codes and control characters
                clean_value = re.sub(r'\x1b\[[0-9;]*[mK]', '', value)
                # Remove any remaining control characters except newlines/tabs
                clean_value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', clean_value)
                sanitized[key] = clean_value
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = self._sanitize_for_mcp(value)
            elif isinstance(value, list):
                # Sanitize list elements
                sanitized_list = []
                for item in value:
                    if isinstance(item, dict):
                        sanitized_list.append(self._sanitize_for_mcp(item))
                    elif isinstance(item, str):
                        clean_item = re.sub(r'\x1b\[[0-9;]*[mK]', '', item)
                        clean_item = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', clean_item)
                        sanitized_list.append(clean_item)
                    else:
                        sanitized_list.append(item)
                sanitized[key] = sanitized_list
            else:
                # Keep other types as-is (numbers, booleans, None)
                sanitized[key] = value
        
        return sanitized
    
    def get_tool_help(self, tool_name: str) -> Optional[str]:
        """
        Get formatted help text for a tool.
        
        Args:
            tool_name: Name of tool
            
        Returns:
            Formatted help text or None if tool not found
        """
        metadata = self.get_tool(tool_name)
        if not metadata:
            return None
        
        help_text = f"Tool: {metadata.name}\n"
        help_text += f"Description: {metadata.description}\n"
        help_text += f"Category: {metadata.category.value}\n"
        help_text += f"Modes: {', '.join(metadata.modes)}\n"
        
        if metadata.requires_external_tool:
            help_text += f"Requires: {metadata.external_tool_name}\n"
        
        if metadata.parameters:
            help_text += "\nParameters:\n"
            for name, param in metadata.parameters.items():
                required = "[required]" if param.required else "[optional]"
                default = f" (default: {param.default})" if param.default is not None else ""
                help_text += f"  {name}: {param.param_type.value} {required}{default}\n"
                if param.description:
                    help_text += f"    {param.description}\n"
        
        if metadata.examples:
            help_text += "\nExamples:\n"
            for example in metadata.examples:
                help_text += f"  {example}\n"
        
        return help_text
    
    def list_tools(self, 
                  mode: str = "all", 
                  category: Optional[ToolCategory] = None) -> str:
        """
        Get formatted list of available tools.
        
        Args:
            mode: Mode filter
            category: Category filter
            
        Returns:
            Formatted tool list
        """
        tools = self.get_available_tools(mode=mode, category=category)
        
        if not tools:
            return "No tools available"
        
        # Group by category
        by_category = {}
        for metadata in tools.values():
            cat = metadata.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(metadata)
        
        result = f"Available Tools ({len(tools)} total):\n\n"
        
        for category, tool_list in by_category.items():
            result += f"{category.value.upper()}:\n"
            for metadata in sorted(tool_list, key=lambda x: x.name):
                status = ""
                if metadata.requires_external_tool:
                    tool_available = metadata.external_tool_name in self._external_tools
                    status = " [external]" if tool_available else " [missing]"
                
                result += f"  {metadata.name}{status} - {metadata.description}\n"
            result += "\n"
        
        return result

# Global registry instance
_global_registry = None

def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
        # Perform initial discovery
        _global_registry.auto_discover_tools()
        _global_registry.integrate_external_tools()
    return _global_registry