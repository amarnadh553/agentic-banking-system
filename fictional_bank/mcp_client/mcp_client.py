
import logging
import sys
from contextlib import AsyncExitStack
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools


logger = logging.getLogger(__name__)

# Project root: fictional_bank_bot/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_EXE = sys.executable


DEFAULT_SERVERS = {
    "accounts": {
        "transport": "stdio",
        "command": PYTHON_EXE,
        "args": [
            "-m",
            "fictional_bank.mcp_servers.accounts_server",
        ],
        "cwd": str(PROJECT_ROOT),
    },
    "transactions": {
        "transport": "stdio",
        "command": PYTHON_EXE,
        "args": [
            "-m",
            "fictional_bank.mcp_servers.transactions_server",
        ],
        "cwd": str(PROJECT_ROOT),
    },
    "service": {
        "transport": "stdio",
        "command": PYTHON_EXE,
        "args": [
            "-m",
            "fictional_bank.mcp_servers.service_server",
        ],
        "cwd": str(PROJECT_ROOT),
    },
}


class MCPToolClient:
    
    """Connect to domain MCP servers and retrieve their tools."""

    def __init__(self):
        self.client = MultiServerMCPClient(DEFAULT_SERVERS)
        self.stack = AsyncExitStack()
        self.tools = {}

    async def connect(self):
        try:
            for name in DEFAULT_SERVERS:
                logger.info("Connecting to MCP server: %s", name)
                session = await self.stack.enter_async_context(self.client.session(name))
                logger.info("Loading tools from MCP server: %s", name)
                self.tools[name] = await load_mcp_tools(session, server_name=name)
                logger.info("Connected to %s; loaded %d tools", name, len(self.tools[name]))
            return self
        except Exception:
            logger.exception("Failed to connect to a domain MCP server")
            await self.stack.aclose()
            raise

    def tools_for(self, server_name: str):
        if server_name not in self.tools:
            raise ValueError(f"MCP server '{server_name}' is not connected. " f"Available servers: {list(self.tools)}")
        return self.tools[server_name]

    async def close(self):
        try:
            await self.stack.aclose()
        finally:
            self.tools.clear()

    async def __aenter__(self):
        return await self.connect()

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
