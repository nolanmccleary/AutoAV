"""
Minimal Session Manager for AutoAV
"""

import asyncio
from typing import List, Dict, Any
from llm.openai_client import OpenAIClient


class SessionManager:
    """Minimal session manager"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        self.conversation_history: List[Dict[str, Any]] = []
    
    async def investigate(self, problem_description: str) -> str:
        """Main investigation method"""
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": problem_description
        })
        
        # Get LLM response
        response = await self.openai_client.get_response(
            messages=self.conversation_history
        )
        
        # Add response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })
        
        # Execute tool calls if any
        if response.tool_calls:
            for tool_call in response.tool_calls:
                result = await self.openai_client.execute_tool_call(tool_call)
                
                # Add tool result to conversation
                self.conversation_history.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tool_call.id
                })
        
        return response.content 