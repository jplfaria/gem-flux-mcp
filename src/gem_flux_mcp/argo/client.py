"""Argo MCP Client for natural language interaction with metabolic modeling tools.

This module provides the ArgoMCPClient class that orchestrates LLM conversations
with tool calling, connecting Argo Gateway (via argo-proxy) with the MCP server.

The client:
1. Connects to argo-proxy (OpenAI-compatible) for LLM access
2. Connects to MCP server for tool access
3. Converts MCP tools to OpenAI function calling format
4. Manages conversation history
5. Implements tool calling loop (LLM → tool → LLM)
6. Executes tools via MCP server
"""

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

# Import MCP tools for direct execution
from gem_flux_mcp import mcp_tools
from gem_flux_mcp.argo.converter import MCPToOpenAIConverter
from gem_flux_mcp.argo.tool_selector import ToolSelector
from gem_flux_mcp.logging import get_logger

logger = get_logger(__name__)


class ArgoMCPClient:
    """Client for natural language interaction with MCP metabolic modeling tools.

    This client connects Argo Gateway (via argo-proxy) with the Gem-Flux MCP server,
    enabling natural language interaction with metabolic modeling tools through
    real LLM capabilities.

    Architecture:
        User Question (natural language)
           ↓
        ArgoMCPClient
           ↓
        Argo Gateway (via argo-proxy) ← OpenAI API
           ↓
        LLM decides to call tools
           ↓
        ArgoMCPClient executes tools via MCP
           ↓
        Tool results sent back to LLM
           ↓
        LLM generates final natural language answer

    Example:
        >>> from gem_flux_mcp.server import initialize_server, create_server
        >>> from gem_flux_mcp.argo.client import ArgoMCPClient
        >>>
        >>> # Initialize MCP server
        >>> initialize_server()
        >>> mcp_server = create_server()
        >>>
        >>> # Create Argo client
        >>> client = ArgoMCPClient(
        ...     mcp_server=mcp_server,
        ...     argo_base_url="http://localhost:8000/v1",
        ...     model="argo:gpt-4o"
        ... )
        >>>
        >>> # Initialize tools
        >>> await client.initialize()
        >>>
        >>> # Ask a question
        >>> response = await client.chat("What is the formula for glucose?")
        >>> print(response)
    """

    def __init__(
        self,
        mcp_server: Any,
        argo_base_url: str = "http://localhost:8000/v1",
        argo_api_key: str = "not-needed",
        model: str = "argo:gpt-4o",
        max_tool_calls: int = 10,
        max_tools_per_call: int = 6,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """Initialize Argo MCP Client.

        Args:
            mcp_server: FastMCP server instance with registered tools
            argo_base_url: URL of argo-proxy (default: http://localhost:8000/v1)
            argo_api_key: API key for argo-proxy (default: "not-needed")
            model: Model to use (default: "argo:gpt-4o")
            max_tool_calls: Maximum number of tool calls per conversation (default: 10)
            max_tools_per_call: Maximum tools to send per LLM call (default: 6, ~15KB)
            temperature: Sampling temperature (0-2). If None, uses model-specific defaults.
            top_p: Nucleus sampling parameter (0-1). If None, uses model-specific defaults.
            max_tokens: Maximum tokens to generate. If None, uses default of 4096.

        Note:
            Per Argo documentation, you can only specify ONE of temperature or top_p, not both.
            If both are None, model-specific defaults will be applied based on the model name.
        """
        self.mcp_server = mcp_server
        self.model = model
        self.max_tool_calls = max_tool_calls

        # Model-specific configuration per Argo documentation
        # GPT models: use temperature
        # Claude models: use top_p (Anthropic preference)
        if temperature is None and top_p is None:
            # Apply model-specific defaults
            if "gpt" in model.lower():
                self.temperature = 0.7
                self.top_p = None
            elif "claude" in model.lower():
                self.temperature = None
                self.top_p = 0.9
            else:
                # Default to temperature for unknown models
                self.temperature = 0.7
                self.top_p = None
        else:
            # Use user-provided values
            self.temperature = temperature
            self.top_p = top_p

        # Set max_tokens (default 4096 for good response length)
        self.max_tokens = max_tokens if max_tokens is not None else 4096

        # OpenAI client for argo-proxy
        self.openai_client = OpenAI(
            base_url=argo_base_url,
            api_key=argo_api_key
        )

        # Tool converter and selector
        self.converter = MCPToOpenAIConverter()
        self.tool_selector = ToolSelector(max_tools=max_tools_per_call)

        # State
        self.messages: List[Dict[str, Any]] = []
        self.openai_tools: List[Dict[str, Any]] = []
        self.mcp_tools: Dict[str, Any] = {}

        logger.info(
            f"ArgoMCPClient initialized with model: {model}, "
            f"max_tools_per_call: {max_tools_per_call}, "
            f"temperature: {self.temperature}, top_p: {self.top_p}, "
            f"max_tokens: {self.max_tokens}"
        )

    async def initialize(self) -> None:
        """Initialize client by loading and converting MCP tools.

        This method must be called before using the client for chat.
        It loads tools from the MCP server and converts them to OpenAI format.

        Raises:
            RuntimeError: If tool loading or conversion fails
        """
        logger.info("Initializing ArgoMCPClient - loading tools from MCP server")

        try:
            # Get tools from MCP server (async call)
            self.mcp_tools = await self.mcp_server.get_tools()
            logger.info(f"Loaded {len(self.mcp_tools)} tools from MCP server")

            # Convert to OpenAI format
            self.openai_tools = self.converter.convert_tools(self.mcp_tools)
            logger.info(f"Converted {len(self.openai_tools)} tools to OpenAI format")

            # Validate conversion
            if not self.converter.validate_conversion(self.openai_tools):
                raise RuntimeError("Tool conversion validation failed")

            logger.info("ArgoMCPClient initialization complete")

        except Exception as e:
            logger.error(f"Failed to initialize ArgoMCPClient: {e}")
            raise RuntimeError(f"ArgoMCPClient initialization failed: {e}")

    async def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        reset_history: bool = False
    ) -> str:
        """Send a message and get a response with automatic tool calling.

        This method implements the tool calling loop:
        1. Send user message to LLM with available tools
        2. If LLM wants to call tools, execute them via MCP
        3. Send tool results back to LLM
        4. Repeat until LLM returns final answer (no more tool calls)

        Args:
            message: User message/question in natural language
            system_prompt: Optional system prompt to set context
            reset_history: Whether to reset conversation history (default: False)

        Returns:
            Final natural language response from LLM

        Raises:
            RuntimeError: If not initialized or if tool execution fails
        """
        if not self.openai_tools or not self.mcp_tools:
            raise RuntimeError(
                "ArgoMCPClient not initialized. Call initialize() first."
            )

        # Reset history if requested
        if reset_history:
            self.messages = []

        # Add system prompt if provided OR use default if conversation is empty
        if not self.messages:
            if system_prompt:
                prompt_to_use = system_prompt
            else:
                # Default system prompt to guide tool usage
                from pathlib import Path
                prompt_to_use = f"""You are a metabolic modeling expert assistant using Gem-Flux MCP tools.

Working directory: {Path.cwd()}

CRITICAL RULES:
1. You MUST use the available tools to answer questions - NEVER answer from memory
2. When asked about compounds/reactions: use get_compound_name, search_compounds, get_reaction_name, search_reactions
3. When asked about media: use build_media, list_media
4. When asked about models: use build_model, list_models, delete_model
5. For simulations: use gapfill_model, run_fba
6. Be concise and technical in your responses
7. Execute ALL requested operations - do not skip steps

Available tools: {', '.join(self.mcp_tools.keys()) if self.mcp_tools else 'loading...'}
"""

            self.messages.append({
                "role": "system",
                "content": prompt_to_use
            })
            logger.info("Added system prompt to guide tool usage")

        # Add user message
        self.messages.append({
            "role": "user",
            "content": message
        })

        logger.info(f"User message: {message}")

        # Tool calling loop
        tool_call_count = 0

        while tool_call_count < self.max_tool_calls:
            # Dynamic tool selection: select relevant tools based on query
            selected_tool_names = self.tool_selector.select_tools(
                message,
                set(self.mcp_tools.keys())
            )

            # Filter to only selected tools
            selected_tools = [
                tool for tool in self.openai_tools
                if tool['function']['name'] in selected_tool_names
            ]

            logger.info(f"Sending {len(selected_tools)} tools to LLM: {selected_tool_names}")

            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": self.messages,
                "tools": selected_tools,
                "tool_choice": "auto",
                "max_tokens": self.max_tokens,
            }

            # Add temperature or top_p (NOT both, per Argo docs)
            if self.temperature is not None:
                api_params["temperature"] = self.temperature
            elif self.top_p is not None:
                api_params["top_p"] = self.top_p

            # Get LLM response with dynamically selected tools
            response = self.openai_client.chat.completions.create(**api_params)

            response_message = response.choices[0].message

            # Add assistant's message to history
            self.messages.append(response_message)

            # Check if LLM wants to call tools
            if not response_message.tool_calls:
                # No more tool calls - return final answer
                final_answer = response_message.content
                logger.info(f"LLM final answer: {final_answer}")
                return final_answer

            # Execute tool calls
            logger.info(f"LLM requested {len(response_message.tool_calls)} tool calls")

            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                logger.info(f"Executing tool: {tool_name}({json.dumps(arguments)})")

                # Execute tool via MCP
                try:
                    result = await self._execute_tool(tool_name, arguments)
                    logger.info(f"Tool result: {json.dumps(result)[:200]}...")

                    # Add tool result to messages
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })

                except Exception as e:
                    logger.error(f"Tool execution failed: {e}")
                    # Add error result to messages
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps({"error": str(e)})
                    })

            tool_call_count += 1

        # Max tool calls reached
        logger.warning(f"Max tool calls ({self.max_tool_calls}) reached")
        return "I apologize, but I've reached the maximum number of tool calls for this conversation. Please try breaking your request into smaller steps."

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool via MCP server.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments from LLM

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
            RuntimeError: If tool execution fails

        Note:
            MCP tools are registered with @mcp.tool() decorator.
            Most are SYNC functions, but some (like build_model) are ASYNC.
            We detect this and await async functions.
        """
        if tool_name not in self.mcp_tools:
            raise ValueError(f"Tool not found: {tool_name}")

        # Get the actual tool function from mcp_tools module
        # Tools are registered as module-level functions with @mcp.tool() decorator
        # The decorator wraps them in FastMCP's FunctionTool objects
        try:
            import inspect

            tool_wrapper = getattr(mcp_tools, tool_name)

            # FastMCP wraps tools in FunctionTool objects with .fn attribute
            # Access the wrapped function via .fn
            if hasattr(tool_wrapper, 'fn') and callable(tool_wrapper.fn):
                tool_fn = tool_wrapper.fn
            elif callable(tool_wrapper):
                tool_fn = tool_wrapper
            else:
                raise RuntimeError(f"Tool {tool_name} is not callable")

            # Check if tool is async or sync
            # Most tools are sync, but some (like build_model) are async
            if inspect.iscoroutinefunction(tool_fn):
                # Async tool - await it
                logger.debug(f"Executing async tool: {tool_name}")
                result = await tool_fn(**arguments)
            else:
                # Sync tool - call directly
                logger.debug(f"Executing sync tool: {tool_name}")
                result = tool_fn(**arguments)

            return result

        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}", exc_info=True)
            raise RuntimeError(f"Tool execution failed: {e}")

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the full conversation history.

        Returns:
            List of message dictionaries (user, assistant, tool)
        """
        return self.messages.copy()

    def reset_conversation(self) -> None:
        """Reset conversation history."""
        self.messages = []
        logger.info("Conversation history reset")

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names.

        Returns:
            List of tool names
        """
        return list(self.mcp_tools.keys())
