"""
OpenAI Client for AutoAV
Handles communication with OpenAI models and tool execution
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

import openai
from openai import AsyncOpenAI

from tools.tool_registry import ToolRegistry


@dataclass
class ToolCall:
    """Represents a tool call from the LLM"""
    id: str
    function: Dict[str, Any]
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """Represents a response from the LLM"""
    content: str
    tool_calls: List[ToolCall]
    is_complete: bool
    usage: Dict[str, Any]


class OpenAIClient:
    """Handles communication with OpenAI models"""
    
    def __init__(self, api_key: str, model: str, tool_registry: ToolRegistry):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.tool_registry = tool_registry
        self.conversation_history: List[Dict[str, Any]] = []
        
        # System prompt for security investigations
        self.system_prompt = self._get_system_prompt()
    
    async def get_response(self, messages: List[Dict[str, Any]], context: Dict[str, Any]) -> LLMResponse:
        """Get a response from the LLM with potential tool calls"""
        
        # Prepare messages for OpenAI
        openai_messages = self._prepare_messages(messages, context)
        
        # Get available tools
        tools = self.tool_registry.get_tool_definitions()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.1,
                max_tokens=4000
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
            
            # Determine if investigation is complete
            is_complete = self._is_investigation_complete(content, tool_calls)
            
            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                is_complete=is_complete,
                usage=response.usage.model_dump() if response.usage else {}
            )
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def execute_tool_call(self, tool_call: ToolCall) -> str:
        """Execute a tool call and return the result"""
        try:
            result = await self.tool_registry.execute_tool(
                tool_call.function["name"],
                tool_call.arguments
            )
            return result
        except Exception as e:
            return f"Error executing {tool_call.function['name']}: {str(e)}"
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return self.tool_registry.get_available_tools()
    
    def _prepare_messages(self, messages: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare messages for OpenAI API"""
        
        # Start with system message
        openai_messages = [
            {
                "role": "system",
                "content": self.system_prompt.format(**context)
            }
        ]
        
        # Add conversation history
        for message in messages:
            if message["role"] in ["user", "assistant"]:
                openai_messages.append({
                    "role": message["role"],
                    "content": message["content"]
                })
            elif message["role"] == "tool":
                openai_messages.append({
                    "role": "tool",
                    "content": message["content"],
                    "tool_call_id": message.get("tool_call_id", "")
                })
        
        return openai_messages
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for security investigations"""
        
        return """You are AutoAV, an AI-driven antivirus system designed to investigate security problems on macOS systems.

Your role is to:
1. Understand the user's security problem description
2. Use available tools to investigate the issue systematically
3. Identify suspicious files, processes, and behaviors
4. Provide a comprehensive analysis and recommendations

Available tools:
{available_tools}

Investigation goals for this session:
{investigation_goals}

System information:
- OS: {system_info[os]}
- Version: {system_info[os_version]}
- Architecture: {system_info[architecture]}

IMPORTANT GUIDELINES:
- Always use tools to gather information before making conclusions
- Be thorough and systematic in your investigation
- Focus on the specific problem described by the user
- Provide clear explanations of your findings
- When you have enough information to provide a comprehensive analysis, indicate that the investigation is complete

Current session ID: {session_id}
Problem type: {problem_type}

Begin your investigation by using appropriate tools to gather information about the described security issue."""
    
    def _is_investigation_complete(self, content: str, tool_calls: List[ToolCall]) -> bool:
        """Determine if the investigation is complete"""
        
        # Check for completion indicators in content
        completion_phrases = [
            "investigation is complete",
            "analysis complete",
            "investigation complete",
            "comprehensive analysis",
            "final analysis",
            "conclusion"
        ]
        
        content_lower = content.lower()
        has_completion_phrase = any(phrase in content_lower for phrase in completion_phrases)
        
        # If no tool calls and has completion phrase, consider complete
        if not tool_calls and has_completion_phrase:
            return True
        
        # If there are tool calls, investigation is not complete
        if tool_calls:
            return False
        
        # If content is substantial and mentions findings, consider complete
        if len(content) > 200 and any(word in content_lower for word in ["found", "identified", "detected", "located"]):
            return True
        
        return False 