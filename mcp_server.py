#!/usr/bin/env python3
"""
MCP server mode for Instability chatbot.

Entry point for running the Instability chatbot as an MCP server,
allowing any MCP-compatible client to interact with the pentesting assistant.
"""

import os
# Set MCP mode immediately to suppress stdout warnings
os.environ['MCP_MODE'] = '1'

import asyncio
import argparse
import logging
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from instability_mcp.mcp_server import InstabilityChatbotMCPServer


async def main():
    """Main entry point for MCP server"""
    parser = argparse.ArgumentParser(description="Instability MCP Server")
    parser.add_argument("--log-level", default="ERROR", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")
    parser.add_argument("--max-sessions", type=int, default=10,
                       help="Maximum concurrent sessions")
    args = parser.parse_args()
    
    # Configure logging to stderr only
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr)  # Log to stderr to avoid interfering with MCP stdout
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Suppress all stdout output during server initialization
        import contextlib
        import io
        
        # Capture stdout during server creation but allow stderr for debugging
        with contextlib.redirect_stdout(io.StringIO()):
            server = InstabilityChatbotMCPServer(max_sessions=args.max_sessions)
        
        # Run with stdio transport
        from mcp.server import stdio, InitializationOptions
        from mcp.types import ServerCapabilities
        try:
            async with (stdio.stdio_server() as (read_stream, write_stream)):
                init_options = InitializationOptions(
                    server_name="instability-chatbot",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities()
                )
                
                await server.run(
                    read_stream=read_stream,
                    write_stream=write_stream,
                    initialization_options=init_options
                )
        except Exception as e:
            print(f"Error in stdio server: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":

    # Suppress all stdout output during server initialization
    print('Starting the MCP server from __main__ inside `mcp_server.py`', file = sys.stderr)

    asyncio.run(main())

    print('MCP server has been started successfully', file = sys.stderr)