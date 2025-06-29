"""
Adapter to integrate existing synchronous chatbot with async MCP interface.

This adapter wraps the existing chatbot functionality to work with
the async MCP server while preserving all existing behavior.
"""

import asyncio
import sys
import os
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import ollama
    from core.tools_registry import get_tool_registry
    from utils import extract_thinking
    from chatbot import parse_tool_call
except ImportError as e:
    raise ImportError(f"Required modules not available: {e}")


class ChatbotAdapter:
    """Adapts synchronous chatbot to async MCP interface"""
    
    def __init__(self, model_name: str = "dolphin3"):
        self.model_name = model_name
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.tool_registry = get_tool_registry()
        
    async def process_message_async(
        self, 
        message: str, 
        conversation_history: List[Dict[str, Any]],
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Convert synchronous chatbot processing to async"""
        loop = asyncio.get_event_loop()
        
        try:
            # Run synchronous processing in thread pool with timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self.executor,
                    self._process_sync,
                    message,
                    conversation_history
                ),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            return {
                "message": "Request timed out",
                "thinking": "Processing took too long",
                "tools_executed": [],
                "error": "timeout"
            }
        except Exception as e:
            return {
                "message": f"Error processing message: {str(e)}",
                "thinking": f"Internal error: {str(e)}",
                "tools_executed": [],
                "error": str(e)
            }
        
    def _process_sync(self, message: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchronous processing adapted from existing chatbot"""
        try:
            # Build conversation context similar to existing chatbot
            conversation = self._build_conversation_context(message, conversation_history)
            
            # Generate response using Ollama
            response = ollama.chat(
                model=self.model_name,
                messages=conversation,
                options={"temperature": 0.1}
            )
            
            content = response["message"]["content"]
            
            # Extract thinking patterns
            thinking, content = extract_thinking(content)
            
            # Check for tool calls
            tool_name, args = parse_tool_call(content)
            tools_executed = []
            
            if tool_name:
                try:
                    # Suppress stdout during tool execution to prevent MCP JSON protocol interference
                    import contextlib
                    import io
                    
                    with contextlib.redirect_stdout(io.StringIO()):
                        # Execute tool using registry
                        tool_result = self.tool_registry.execute_tool(tool_name, args or {}, mode="chatbot")
                    
                    tools_executed.append({
                        "tool": tool_name,
                        "args": args,
                        "result": tool_result
                    })
                    
                    # Generate follow-up response with tool result
                    conversation.append({"role": "assistant", "content": content})
                    conversation.append({"role": "system", "content": f"Tool result: {tool_result}"})
                    
                    follow_up = ollama.chat(
                        model=self.model_name,
                        messages=conversation,
                        options={"temperature": 0.7}
                    )
                    
                    content = follow_up["message"]["content"]
                    
                except Exception as e:
                    content = f"Error executing tool {tool_name}: {str(e)}"
            
            return {
                "message": content,
                "thinking": thinking,
                "tools_executed": tools_executed
            }
            
        except Exception as e:
            return {
                "message": f"Error in chatbot processing: {str(e)}",
                "thinking": f"Processing error: {str(e)}",
                "tools_executed": []
            }
    
    def _build_conversation_context(self, current_message: str, history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Build conversation context for Ollama API"""
        
        # System message adapted from existing chatbot
        system_message = {
            "role": "system",
            "content": """You are a network diagnostics and cybersecurity specialist working with an experienced security admin/pentester. 
You can call tools for network diagnosis, security scanning, and pentest reconnaissance.
You have access to various networking tools that can be called to diagnose problems or do pentest reconnaissance and security scanning.

IMPORTANT: For any network-related questions about connectivity, DNS, ping, latency, IP addresses, routing, or network performance, you MUST use the appropriate tools to get real data.

When you need specific information, you can call a tool using this format:

TOOL: tool_name
ARGS: {"arg_name": "value"} (or {} if no arguments needed)

STOP after the tool call. Do NOT include any text like "Tool result:", example output, or sample data.

Be direct, concise, and technical. You are an expert conversing with another expert.
Keep responses extremely brief. One to two sentences maximum."""
        }
        
        # Build conversation from history
        conversation = [system_message]
        
        # Add recent history (last 10 messages to avoid context overflow)
        recent_history = history[-10:] if len(history) > 10 else history
        for msg in recent_history:
            if msg.get("role") in ["user", "assistant"]:
                conversation.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current message
        conversation.append({"role": "user", "content": current_message})
        
        return conversation