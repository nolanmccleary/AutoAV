#!/usr/bin/env python3
"""
AutoAV - Lightweight Agentic Antivirus Suite
"""

import os
from cli.session_manager import SessionManager
from llm.openai_client import OpenAIClient
from tools.tool_registry import ToolRegistry


def main():
    """Main entry point"""
    # Check for OpenAI API key, you will need to set this up in your shell config if you have not already done so
    api_key = os.getenv('OPENAI_API_KEY')  
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("export OPENAI_API_KEY=your_api_key_here")
        return
    

    tool_registry = ToolRegistry()
    openai_client = OpenAIClient(api_key, tool_registry)
    session_manager = SessionManager(openai_client)
    

    problem = input("Please describe problem: ").strip()
    print("Investigating...")
    result = session_manager.investigate(problem)
    print(f"\nResult:\n{result}\n")


if __name__ == '__main__':
    main() 