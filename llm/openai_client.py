from typing import List, Dict, Any, Tuple
from openai import OpenAI
from tools import ToolRegistry, AVAILABLE_COMMANDS



#TODO: Better system prompt
SYSTEM_PROMPT = {"role": "system", "content": 
f"You are a security investigator with access to a UNIX shell. You can use the following tools to investigate security problems: {', '.join(AVAILABLE_COMMANDS)} If you are not sure what to do next, you can use the 'api_get_user_input' tool to get user input on what to do next."}



class OpenAIClient:
    
    def __init__(self, api_key: str, tool_registry: ToolRegistry, system_prompt = SYSTEM_PROMPT):
        self.client = OpenAI(api_key=api_key)
        self.tool_registry = tool_registry
        self.tool_defs = self.tool_registry.get_tool_definitions()
        self.system_prompt = system_prompt


    def get_system_prompt(self):
        return self.system_prompt


    def get_response(self, messages: List[Dict[str, Any]]) -> Tuple[Dict, Dict]:
        """Get a response from the LLM"""
        client_messages = [self.system_prompt] + messages
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=client_messages,
            tools=self.tool_defs,
            tool_choice="auto",
            temperature=0.1,
            n=1
        )
        choice = response.choices[0]
        usage = response.usage

        return choice, usage


    def execute_tool_call(self, tool_call: Dict) -> Dict:
        """Execute a tool call"""
        content = self.tool_registry.execute_tool(
            tool_call["function"]["name"],
            tool_call["function"]["arguments"]
        )

        return{
            "role" : "tool", 
            "tool_call_id" : tool_call['tool_call_id'],
            "content" : content
        }