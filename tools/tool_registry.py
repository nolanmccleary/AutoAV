"""
Tool Registry for AutoAV
Defines and manages available filesystem operations for the LLM
"""

import inspect
from typing import List, Dict, Any, Callable

from api.av_api import api_execute_command, api_read_file, api_list_processes, api_get_file_info, api_find_files, api_list_directory_contents, api_list_network_connections, AVAILABLE_COMMANDS, _get_stats


class ToolRegistry:
    """Registry of available tools for the LLM"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {
            "api_execute_command": api_execute_command,
            "api_read_file": api_read_file,
            "api_list_processes": api_list_processes,
            "api_get_file_info": api_get_file_info,
            "api_find_files": api_find_files,
            "api_list_directory_contents": api_list_directory_contents,
            "api_list_network_connections": api_list_network_connections
        }
    

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return list(self.tools.keys())
    

    #TODO: Better tool defs
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for OpenAI API"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "api_execute_command",
                    "description": f"Execute a shell-based command.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": f"Shell command to be executed. For example, if we wnated to grep something, we would set this value to 'grep'. Available commands: {inspect.getsource(AVAILABLE_COMMANDS)}"
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
                    "name": "api_list_processes",
                    "description": f"List running processes with details including command line, memory usage, and file paths.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "Optional filter for process names (e.g., 'chrome', 'safari')"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "api_read_file",
                    "description": f"Read file contents safely with size limits and validation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Absolute file path to read"
                            },
                            "max_size": {
                                "type": "integer",
                                "description": "Maximum file size to read in bytes (default: 10485760 = 10MB)"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "api_find_files",
                    "description": f"Find files matching pattern criteria using glob patterns.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Target pattern to glob for"
                            },
                            "directory": {
                                "type": "string",
                                "description": "Directory to search in defaults to user home directory if not specified"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Hard cap on number of matches retrieved. Defaults to 50 if not specified"
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "api_get_file_info",
                    "description": f"Get detailed file information including permissions, timestamps, and metadata.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Target file path"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "api_list_directory_contents",
                    "description": f"Nonrecursively list contents of a directory with file details.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path to list contents of"
                            },
                            "show_hidden": {
                                "type": "boolean",
                                "description": "Include hidden files. Defaults to false if not specified"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "api_list_network_connections",
                    "description": f"Get active network connections and associated processes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "Optional filter on process names associated with a given connection. Defaults to None if not specified"
                            }
                        }
                    }
                }
            }
        ]


    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with the given arguments"""
        if tool_name not in self.tools:
            raise ValueError(f"Error: Unknown tool '{tool_name}'")
        return self.tools[tool_name](**arguments)



    