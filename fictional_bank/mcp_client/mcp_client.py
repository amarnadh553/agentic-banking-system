
from contextlib import AsyncExitStack
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools


DEFAULT_SERVERS = {
    "accounts": {
        "transport": "stdio",
        "command": "uv",
        "args": [
            "run",
            "python",
            "-m",
            "fictional_bank.mcp_servers.accounts_server",
        ],
    },
    "transactions": {
        "transport": "stdio",
        "command": "uv",
        "args": [
            "run",
            "python",
            "-m",
            "fictional_bank.mcp_servers.transactions_server",
        ],
    },
    "service": {
            "transport": "stdio",
            "command": "uv",
            "args": [
                "run",
                "python",
                "-m",
                "fictional_bank.mcp_servers.service_server",
            ],
        },
}


class MCPToolClient:
    """Connect to MCP servers and retrieve their tools."""

    def __init__(self):
        self.client = MultiServerMCPClient(DEFAULT_SERVERS)
        self.stack = AsyncExitStack()
        self.tools = {}

    async def connect(self):
        for name in DEFAULT_SERVERS:
            session = await self.stack.enter_async_context(self.client.session(name))
            self.tools[name] = await load_mcp_tools(session, server_name=name,)
        return self

    def tools_for(self, server_name: str):
        return self.tools[server_name]

    async def close(self):
        await self.stack.aclose()
        self.tools.clear()

    async def __aenter__(self):
        return await self.connect()

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
