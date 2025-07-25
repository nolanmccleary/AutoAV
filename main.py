import argparse
import os
from cli import SessionManager
from llm import OpenAIClient
from tools import ToolRegistry


def main(args):
    
    # Check for OpenAI API key, you will need to set this up in your shell config if you have not already done so
    api_key = os.getenv('OPENAI_API_KEY')  
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("export OPENAI_API_KEY=your_api_key_here")
        return
    

    tool_registry = ToolRegistry()
    openai_client = OpenAIClient(api_key, tool_registry)
    session_manager = SessionManager(openai_client)
    

    problem = args.problem
    print(f"Investigating problem: {problem}")
    result = session_manager.investigate(problem)
    print(f"\nResult:\n{result}\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AutoAV - Lightweight Agentic Antivirus Suite')
    parser.add_argument('--problem', '-p', type=str, required=True, help='Problem description')
    args = parser.parse_args()
    main(args) 