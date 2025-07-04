"""
Session management for MCP server.

Handles multiple concurrent chatbot sessions with proper isolation
and leverages existing chatbot functionality.
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from instability_mcp.chatbot_adapter import ChatbotAdapter


@dataclass
class ChatbotResponse:
    """Response from chatbot processing"""
    content: str
    thinking: Optional[str] = None
    tools_used: list = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.tools_used is None:
            self.tools_used = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class ChatbotSession:
    """Represents a single chatbot conversation session"""
    
    def __init__(self, session_id: str):
        self.id = session_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.conversation_history = []
        self.startup_complete = False
        self.chatbot_adapter = ChatbotAdapter()
        
    async def process_message(self, prompt: str, include_thinking: bool = True, timeout: float = 30.0) -> ChatbotResponse:
        """Process a message through the chatbot"""
        self.last_activity = datetime.now()
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        
        # Process through existing chatbot
        try:
            response_data = await self.chatbot_adapter.process_message_async(
                prompt, 
                self.conversation_history,
                timeout=timeout
            )
            
            # Create response object
            response = ChatbotResponse(
                content=response_data.get("message", ""),
                thinking=response_data.get("thinking") if include_thinking else None,
                tools_used=response_data.get("tools_executed", [])
            )
            
            # Add response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response.content,
                "timestamp": response.timestamp
            })
            
            # Trim conversation history if too long
            max_history = 20
            if len(self.conversation_history) > max_history:
                self.conversation_history = self.conversation_history[-max_history:]
            
            return response
            
        except asyncio.TimeoutError:
            return ChatbotResponse(
                content="Request timed out. Please try again with a simpler query.",
                thinking="Request exceeded timeout limit"
            )
        except Exception as e:
            return ChatbotResponse(
                content=f"Error processing message: {str(e)}",
                thinking=f"Internal error: {str(e)}"
            )


class SessionManager:
    """Manages multiple concurrent chatbot sessions"""
    
    def __init__(self, max_sessions: int = 10, session_timeout: int = 3600):
        self.sessions: Dict[str, ChatbotSession] = {}
        self.max_sessions = max_sessions
        self.session_timeout = session_timeout
        self._cleanup_task = None
        # Don't start cleanup task in __init__ - will be started when needed
        
    def _start_cleanup_task(self):
        """Start background task to clean up expired sessions"""
        async def cleanup_expired_sessions():
            while True:
                try:
                    await asyncio.sleep(300)  # Check every 5 minutes
                    current_time = datetime.now()
                    expired_sessions = []
                    
                    for session_id, session in self.sessions.items():
                        if (current_time - session.last_activity).seconds > self.session_timeout:
                            expired_sessions.append(session_id)
                    
                    for session_id in expired_sessions:
                        del self.sessions[session_id]
                        
                except Exception:
                    pass  # Continue cleanup on errors
        
        self._cleanup_task = asyncio.create_task(cleanup_expired_sessions())
        
    async def get_or_create_session(self, session_id: Optional[str] = None) -> ChatbotSession:
        """Get existing session or create new one"""
        # Start cleanup task if not already running
        if self._cleanup_task is None:
            self._start_cleanup_task()
            
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            session.last_activity = datetime.now()  # Update activity
            return session
            
        return await self.create_session()
        
    async def create_session(self) -> ChatbotSession:
        """Create a new chatbot session"""
        # Remove oldest session if at limit
        if len(self.sessions) >= self.max_sessions:
            oldest_session_id = min(
                self.sessions.keys(), 
                key=lambda sid: self.sessions[sid].last_activity
            )
            del self.sessions[oldest_session_id]
            
        session_id = str(uuid.uuid4())
        session = ChatbotSession(session_id)
        self.sessions[session_id] = session
        return session
    
    async def get_session(self, session_id: Optional[str]) -> Optional[ChatbotSession]:
        """Get existing session by ID"""
        if not session_id:
            return None
        
        session = self.sessions.get(session_id)
        if session:
            session.last_activity = datetime.now()
        return session
    
    def get_active_session_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)