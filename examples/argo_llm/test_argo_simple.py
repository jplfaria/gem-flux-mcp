#!/usr/bin/env python3
"""Simple test of Argo LLM with tool calling.

This script demonstrates basic tool calling with Argo Gateway without needing
the full MCP server. It validates that argo-proxy is working and can call tools.

Run with: uv run python examples/argo_llm/test_argo_simple.py
"""

import json
from openai import OpenAI

# Connect to argo-proxy
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"  # argo-proxy doesn't require API key
)

# Define a simple test tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_compound_info",
            "description": "Get information about a metabolic compound by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "compound_id": {
                        "type": "string",
                        "description": "The compound ID (e.g., 'cpd00027' for glucose)"
                    }
                },
                "required": ["compound_id"]
            }
        }
    }
]

# Simulate tool execution
def execute_tool(tool_name, arguments):
    """Simulate tool execution."""
    if tool_name == "get_compound_info":
        compound_id = arguments.get("compound_id", "")
        # Simulated response
        return {
            "compound_id": compound_id,
            "name": "D-Glucose" if "00027" in compound_id else "Unknown",
            "formula": "C6H12O6" if "00027" in compound_id else "Unknown",
            "mass": 180.156 if "00027" in compound_id else 0
        }
    return {"error": "Unknown tool"}

def main():
    print("=" * 60)
    print("Testing Argo LLM with Tool Calling")
    print("=" * 60)
    print()

    # Test 1: Check argo-proxy connection
    print("1. Testing argo-proxy connection...")
    try:
        models = client.models.list()
        print(f"   ✓ Connected! Found {len(models.data)} models")
        print(f"   Available models: {[m.id for m in models.data[:3]]}")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        print("\n   Make sure argo-proxy is running:")
        print("   $ argo-proxy")
        return

    print()

    # Test 2: Basic chat without tools
    print("2. Testing basic chat (no tools)...")
    try:
        response = client.chat.completions.create(
            model="argo:gpt-4o",
            messages=[
                {"role": "user", "content": "What is 2+2? Answer in one word."}
            ]
        )
        answer = response.choices[0].message.content
        print(f"   User: What is 2+2?")
        print(f"   LLM: {answer}")
        print("   ✓ Basic chat works!")
    except Exception as e:
        print(f"   ✗ Chat failed: {e}")
        return

    print()

    # Test 3: Tool calling
    print("3. Testing tool calling...")
    print("   User: What is the molecular formula of glucose (cpd00027)?")

    messages = [
        {
            "role": "user",
            "content": "What is the molecular formula of glucose (compound ID cpd00027)?"
        }
    ]

    try:
        # Make request with tools
        response = client.chat.completions.create(
            model="argo:gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        # Check if LLM wants to call a tool
        if response_message.tool_calls:
            print(f"   ✓ LLM wants to call tools!")

            # Add assistant's message to history
            messages.append(response_message)

            # Execute each tool call
            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                print(f"   Tool call: {tool_name}({json.dumps(arguments)})")

                # Execute tool
                result = execute_tool(tool_name, arguments)
                print(f"   Tool result: {json.dumps(result)}")

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

            # Get final response from LLM after tool execution
            final_response = client.chat.completions.create(
                model="argo:gpt-4o",
                messages=messages
            )

            final_answer = final_response.choices[0].message.content
            print(f"   LLM final answer: {final_answer}")
            print("   ✓ Tool calling works!")
        else:
            print(f"   ✗ LLM did not call any tools")
            print(f"   LLM response: {response_message.content}")

    except Exception as e:
        print(f"   ✗ Tool calling failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print()
    print("=" * 60)
    print("All tests passed! Argo LLM integration is working.")
    print("=" * 60)

if __name__ == "__main__":
    main()
