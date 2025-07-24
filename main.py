#!/usr/bin/env python3
"""
AutoAV - Minimal AI-Driven Antivirus Suite
"""

import os
import asyncio
from cli.session_manager import SessionManager
from llm.openai_client import OpenAIClient
from inspector.file_inspector import FileInspector
from permissions.permission_manager import PermissionManager
from tools.tool_registry import ToolRegistry


def main():
    """Main entry point"""
    
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("export OPENAI_API_KEY=your_api_key_here")
        return
    
    # Initialize components
    permission_manager = PermissionManager()
    file_inspector = FileInspector(permission_manager)
    tool_registry = ToolRegistry(file_inspector)
    openai_client = OpenAIClient(api_key, tool_registry)
    session_manager = SessionManager(openai_client)
    
    # Simple interactive loop
    print("AutoAV - Describe your security problem")
    print("Type 'quit' to exit\n")
    
    while True:
        problem = input("Problem: ").strip()
        if problem.lower() in ['quit', 'exit', 'q']:
            break
        
        if not problem:
            continue
        
        print("Investigating...")
        result = asyncio.run(session_manager.investigate(problem))
        print(f"\nResult:\n{result}\n")


if __name__ == '__main__':
    main() 