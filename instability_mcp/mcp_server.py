"""
Main MCP server implementation for Instability chatbot.

Provides MCP tools that expose chatbot functionality while leveraging
the existing v3 architecture and tool registry.
"""

import asyncio
import logging
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    from mcp import server, types
    from mcp.server import Server, stdio
except ImportError:
    raise ImportError("MCP package not installed. Install with: pip install mcp")

from instability_mcp.session_manager import SessionManager
from core.tools_registry import get_tool_registry
from core.startup_checks import run_startup_sequence


class InstabilityChatbotMCPServer(Server):
    """MCP server exposing Instability chatbot functionality"""
    
    def __init__(self, max_sessions: int = 10):
        super().__init__("instability-chatbot", version="1.0.0")
        self.session_manager = SessionManager(max_sessions=max_sessions)
        self.tool_registry = get_tool_registry()
        self.startup_context = None
        self._logger = logging.getLogger(__name__)
        
        # Register request handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP request handlers"""
        
        # Register tools/list handler
        async def handle_list_tools(request: types.ListToolsRequest) -> types.ListToolsResult:
            return await self.list_tools()
        
        # Register tools/call handler  
        async def handle_call_tool(request: types.CallToolRequest) -> types.CallToolResult:
            content = await self.call_tool(request.params.name, request.params.arguments or {})
            return types.CallToolResult(content=content)
        
        # Add handlers to the registry
        self.request_handlers[types.ListToolsRequest] = handle_list_tools
        self.request_handlers[types.CallToolRequest] = handle_call_tool
    
        
    async def list_tools(self) -> types.ListToolsResult:
        """List available tools"""
        try:
            tools = self.tool_registry.get_available_tools(mode="chatbot")
            
            # Convert to MCP tool format
            mcp_tools = []
            for name, metadata in tools.items():
                # Convert parameters to MCP format
                parameters = {}
                for param_name, param_info in metadata.parameters.items():
                    parameters[param_name] = {
                        "type": param_info.param_type.value,
                        "description": param_info.description,
                        "required": param_info.required
                    }
                
                mcp_tool = types.Tool(
                    name=name,
                    description=metadata.description,
                    inputSchema={
                        "type": "object",
                        "properties": parameters,
                        "required": [p for p, info in metadata.parameters.items() if info.required]
                    }
                )
                mcp_tools.append(mcp_tool)
            
            # Add chat tool
            chat_tool = types.Tool(
                name="chat",
                description="Send a message to the Instability pentesting assistant",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "User message to process"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Optional session ID for conversation continuity"
                        },
                        "include_thinking": {
                            "type": "boolean",
                            "description": "Include LLM reasoning in response",
                            "default": True
                        }
                    },
                    "required": ["prompt"]
                }
            )
            mcp_tools.append(chat_tool)
            
            # Add session management tools
            start_session_tool = types.Tool(
                name="start_session",
                description="Initialize a new chatbot session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "run_startup": {
                            "type": "boolean",
                            "description": "Run startup sequence",
                            "default": True
                        }
                    }
                }
            )
            mcp_tools.append(start_session_tool)
            
            return types.ListToolsResult(tools=mcp_tools)
            
        except Exception as e:
            self._logger.error(f"Error listing tools: {e}")
            return types.ListToolsResult(tools=[])
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Execute a tool call"""
        try:
            self._logger.info(f"Calling tool: {name} with args: {arguments}")
            
            if name == "chat":
                return await self._handle_chat(arguments)
            elif name == "start_session":
                return await self._handle_start_session(arguments)
            else:
                # Handle direct tool execution
                return await self._handle_tool_execution(name, arguments)
                
        except Exception as e:
            self._logger.error(f"Error calling tool {name}: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error executing tool {name} - {str(e)}"
            )]
    
    async def _handle_chat(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle chat tool calls"""
        prompt = arguments.get("prompt", "")
        session_id = arguments.get("session_id")
        include_thinking = arguments.get("include_thinking", True)
        
        if not prompt:
            return [types.TextContent(type="text", text="Error - prompt is required")]
        
        try:
            session = await self.session_manager.get_or_create_session(session_id)
            response = await session.process_message(prompt, include_thinking, timeout=30.0)
            
            result_text = f"**Response-** {response.content}\n"
            if response.thinking and include_thinking:
                result_text += f"\n**Thinking-** {response.thinking}\n"
            if response.tools_used:
                result_text += f"\n**Tools Used-** {', '.join([t.get('tool', 'unknown') for t in response.tools_used])}\n"
            result_text += f"\n**Session ID-** {session.id}"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Chat error - {str(e)}")]
    
    async def _handle_start_session(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle start session tool calls"""
        run_startup = arguments.get("run_startup", True)
        
        try:
            session = await self.session_manager.create_session()
            
            if run_startup and not self.startup_context:
                # Run startup sequence once for the server
                self.startup_context = run_startup_sequence(silent=True)
            
            result_text = f"**Session Created-** {session.id}\n"
            if run_startup and self.startup_context:
                status = "SUCCESS" if self.startup_context.get("success") else "DEGRADED"
                result_text += f"**Startup Status-** {status}\n"
                
                phases = self.startup_context.get("phases", {})
                if phases:
                    result_text += "**System Status-**\n"
                    for phase_name, phase_data in phases.items():
                        phase_status = "OK" if phase_data.get("success") else "WARN"
                        result_text += f"- {phase_name.replace('_', ' ').title()} - {phase_status}\n"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Session creation error - {str(e)}")]
    
    async def _handle_tool_execution(self, tool_name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle direct tool execution"""
        try:
            # Suppress stdout during tool execution to prevent MCP JSON protocol interference
            import contextlib
            import io
            
            with contextlib.redirect_stdout(io.StringIO()):
                # Force silent=True for MCP executions to prevent stdout interference
                arguments = arguments.copy()
                arguments["silent"] = True
                
                # Execute tool using registry
                result = self.tool_registry.execute_tool(tool_name, arguments, mode="chatbot")
            
            if isinstance(result, dict):
                if result.get("success"):
                    result_text = f"**Tool-** {tool_name}\n**Result-** Success\n"
                    if "stdout" in result:
                        # Sanitize stdout content to prevent colon-related UI crashes
                        sanitized_stdout = self._sanitize_text_content(result['stdout'])
                        result_text += f"**Output-**\n```\n{sanitized_stdout}\n```"
                    elif "parsed_data" in result:
                        import json
                        try:
                            # Sanitize parsed_data to prevent Claude desktop UI crashes
                            sanitized_data = self._sanitize_response_data(result['parsed_data'])
                            data_str = json.dumps(sanitized_data, ensure_ascii=True, indent=2)
                            result_text += f"**Data-**\n```json\n{data_str}\n```"
                        except (TypeError, ValueError):
                            # Fallback to string representation if JSON serialization fails
                            sanitized_fallback = self._sanitize_text_content(str(result['parsed_data']))
                            result_text += f"**Data-** {sanitized_fallback}"
                else:
                    sanitized_error = self._sanitize_text_content(result.get('error_message', 'Unknown error'))
                    result_text = f"**Tool-** {tool_name}\n**Error-** {sanitized_error}"
            else:
                sanitized_result = self._sanitize_text_content(str(result))
                result_text = f"**Tool-** {tool_name}\n**Result-** {sanitized_result}"
            
            return [types.TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [types.TextContent(type="text", text=f"Tool execution error - {str(e)}")]
    
    def _sanitize_response_data(self, data: Any) -> Any:
        """Sanitize response data to prevent Claude desktop UI crashes"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                sanitized[key] = self._sanitize_response_data(value)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_response_data(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_text_content(data)
        else:
            return data
    
    def _sanitize_text_content(self, text: str) -> str:
        """Sanitize text content to prevent Claude desktop UI crashes"""
        if not isinstance(text, str):
            text = str(text)
        
        # Replace colons that seem to trigger Claude desktop bugs
        # Be aggressive about colon replacement to prevent UI crashes
        
        # First handle MAC addresses specifically
        if ":" in text and len(text.split(":")) >= 6:
            # Likely contains MAC addresses - replace colons with hyphens
            text = text.replace(":", "-")
        elif ":" in text:
            # Replace other colons with safe alternatives
            # Keep IPv6 addresses readable but use different separator
            if "::" in text:  # IPv6
                text = text.replace("::", "--").replace(":", "-")
            else:
                # General colon replacement with safe alternative
                text = text.replace(":", " -")
        
        return text

