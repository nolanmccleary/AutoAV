"""
Minimal OpenAI Client for AutoAV
"""

import json
from typing import List, Dict, Any
from dataclasses import dataclass
from openai import AsyncOpenAI
from tools.tool_registry import ToolRegistry


@dataclass
class ToolCall:
    """Represents a tool call from the LLM"""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """Represents a response from the LLM"""
    content: str
    tool_calls: List[ToolCall]


class OpenAIClient:
    """Minimal OpenAI client"""
    
    def __init__(self, api_key: str, tool_registry: ToolRegistry):
        self.client = AsyncOpenAI(api_key=api_key)
        self.tool_registry = tool_registry
    
    async def get_response(self, messages: List[Dict[str, Any]]) -> LLMResponse:
        """Get a response from the LLM"""
        
        # Add system message
        openai_messages = [
            {"role": "system", "content": "You are a security investigator. Use available tools to investigate security problems."}
        ] + messages
        
        # Get tools
        tools = self.tool_registry.get_tool_definitions()
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=openai_messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.1
        )
        
        # Parse response
        content = response.choices[0].message.content or ""
        tool_calls = []
        
        if response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tool_call.id,
                    function={
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    },
                    arguments=json.loads(tool_call.function.arguments)
                ))
        
        return LLMResponse(content=content, tool_calls=tool_calls)
    
    async def execute_tool_call(self, tool_call: ToolCall) -> str:
        """Execute a tool call"""
        return await self.tool_registry.execute_tool(
            tool_call.function["name"],
            tool_call.arguments
        ) 