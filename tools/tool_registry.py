from typing import List, Dict, Any, Callable

from api import api_execute_command


class ToolRegistry:
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {
            "api_execute_command": api_execute_command,
        }
    

    def get_available_tools(self) -> List[str]:
        return list(self.tools.keys())
    

    #TODO: Better tool defs
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "api_execute_command",
                    "description": f"Execute any shell command. Put the command name in 'command' field and arguments as a list in 'command_args' field.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": f"Shell command to be executed."
                            },
                            "command_args": {
                                "type": "array",
                                "description": "Command argument sequence. For example, if we want to grep recursively for string/substring 'beans' from our current location in the filesystem, we would set our args as ['-r', 'beans']"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "api_get_user_input",
                    "description": "Get user input if you are not sure what to do next. Put your message to the user in the 'prompt' field.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Prompt to get user input"
                            }
                        },
                        "required": ["prompt"]
                    }
                }
            }
        ]


    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name not in self.tools:
            raise ValueError(f"Error: Unknown tool '{tool_name}'")
        return self.tools[tool_name](**arguments)



    