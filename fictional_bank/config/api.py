
"""API configuration for the Fictional Banking System."""

import os
from dotenv import load_dotenv

from fictional_bank.config.config import UPPERCASE_FALSE_STRINGS, DEPLOY

# Load environment variables from the project configuration.
load_dotenv(override=False)

# FastAPI application configuration.
API_CONFIG = {
    "title": "Fictional Banking Agent API",
    "description": "REST API powered by LangGraph and MCP.",
    "version": "1.0.0",
    "prefix": "/api/v1",
    "docs_url": "/api/v1/docs",
    "openapi_url": "/api/v1/openapi.json",
}
UPPERCASE_FALSE_STRINGS="false"
# Middleware configuration.
ALLOW_METHODS = os.getenv("ALLOW_METHODS", "*").split(",")
ALLOW_HEADERS = os.getenv("ALLOW_HEADERS", "*").split(",")
ALLOW_ORIGIN_REGEX = os.getenv("ALLOW_ORIGIN_REGEX", ".*")

ALLOW_CREDENTIALS = (os.getenv("ALLOW_CREDENTIALS", "true").upper().strip() not in UPPERCASE_FALSE_STRINGS)

# API server configuration.
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))

RELOAD = (os.getenv("RELOAD", "true").upper().strip() not in UPPERCASE_FALSE_STRINGS)

# # Disable API documentation in deployed environments.
# if DEPLOY:
#     API_CONFIG.update({"docs_url": None, "openapi_url": None})

__all__ = [
    "API_CONFIG",
    "ALLOW_METHODS",
    "ALLOW_HEADERS",
    "ALLOW_ORIGIN_REGEX",
    "ALLOW_CREDENTIALS",
    "API_HOST",
    "API_PORT",
    "RELOAD",
]
