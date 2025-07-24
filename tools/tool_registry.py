"""
Tool Registry for AutoAV
Defines and manages available filesystem operations for the LLM
"""

import asyncio
import json
from typing import List, Dict, Any, Callable
from pathlib import Path

from inspector.file_inspector import FileInspector


class ToolRegistry:
    """Registry of available tools for the LLM"""
    
    def __init__(self, file_inspector: FileInspector):
        self.file_inspector = file_inspector
        self.tools: Dict[str, Callable] = {
            "list_processes": self._list_processes,
            "read_file": self._read_file,
            "scan_file": self._scan_file,
            "find_files": self._find_files,
            "get_file_info": self._get_file_info,
            "list_directory": self._list_directory,
            "check_browser_extensions": self._check_browser_extensions,
            "check_startup_items": self._check_startup_items,
            "get_network_connections": self._get_network_connections
        }
    

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return list(self.tools.keys())
    

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for OpenAI API"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_processes",
                    "description": "List running processes with details including command line, memory usage, and file paths",
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
                    "name": "read_file",
                    "description": "Read file contents safely with size limits and validation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Absolute file path to read"
                            },
                            "max_size": {
                                "type": "integer",
                                "description": "Maximum file size to read in bytes (default: 10485760 = 10MB)"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scan_file",
                    "description": "Scan file with ClamAV antivirus engine",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path to scan"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_files",
                    "description": "Find files matching criteria using glob patterns",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "File pattern to search for (e.g., '*.plist', '*.app')"
                            },
                            "directory": {
                                "type": "string",
                                "description": "Directory to search in (default: user home directory)"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 50)"
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_file_info",
                    "description": "Get detailed file information including permissions, timestamps, and metadata",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "List contents of a directory with file details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path to list"
                            },
                            "show_hidden": {
                                "type": "boolean",
                                "description": "Include hidden files (default: false)"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_browser_extensions",
                    "description": "Check for suspicious browser extensions and settings",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "browser": {
                                "type": "string",
                                "description": "Browser to check (chrome, safari, firefox)",
                                "enum": ["chrome", "safari", "firefox", "all"]
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_startup_items",
                    "description": "Check for suspicious startup items and launch agents",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_network_connections",
                    "description": "Get active network connections and associated processes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "Optional filter for specific processes or addresses"
                            }
                        }
                    }
                }
            }
        ]

    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool with the given arguments"""
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"
        
        result = await self.tools[tool_name](**arguments)
        return result

    
    async def _list_processes(self, filter: str = None) -> str:
        """List running processes"""
        return await self.file_inspector.list_processes(filter)
    

    async def _read_file(self, path: str, max_size: int = 10485760) -> str:
        """Read file contents"""
        return await self.file_inspector.read_file(path, max_size)
    

    async def _scan_file(self, path: str) -> str:
        """Scan file with ClamAV"""
        return await self.file_inspector.scan_file(path)
    

    async def _find_files(self, pattern: str, directory: str = None, max_results: int = 50) -> str:
        """Find files matching pattern"""
        return await self.file_inspector.find_files(pattern, directory, max_results)
    
    async def _get_file_info(self, path: str) -> str:
        """Get file information"""
        return await self.file_inspector.get_file_info(path)
    
    async def _list_directory(self, path: str, show_hidden: bool = False) -> str:
        """List directory contents"""
        return await self.file_inspector.list_directory(path, show_hidden)
    
    async def _check_browser_extensions(self, browser: str = "all") -> str:
        """Check browser extensions"""
        return await self.file_inspector.check_browser_extensions(browser)
    
    async def _check_startup_items(self) -> str:
        """Check startup items"""
        return await self.file_inspector.check_startup_items()
    
    async def _get_network_connections(self, filter: str = None) -> str:
        """Get network connections"""
        return await self.file_inspector.get_network_connections(filter) 