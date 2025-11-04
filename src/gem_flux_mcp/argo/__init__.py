"""Argo LLM integration for Gem-Flux MCP.

This package provides integration with ANL's Argo Gateway to enable natural
language interaction with metabolic modeling tools via real LLMs.

Components:
- converter: Convert MCP tool schemas to OpenAI function calling format
- client: ArgoMCPClient for managing LLM conversations with tool calling
- tool_selector: Dynamic tool selection to work around Argo payload limits
"""

from .converter import MCPToOpenAIConverter
from .client import ArgoMCPClient
from .tool_selector import ToolSelector

__all__ = ["MCPToOpenAIConverter", "ArgoMCPClient", "ToolSelector"]
