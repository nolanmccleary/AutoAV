#!/usr/bin/env python3
"""
AutoAV - AI-Driven Antivirus Suite
Main entry point for the application
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.prompt import Prompt
from dotenv import load_dotenv

from cli.session_manager import SessionManager
from llm.openai_client import OpenAIClient
from inspector.file_inspector import FileInspector
from permissions.permission_manager import PermissionManager
from tools.tool_registry import ToolRegistry

# Load environment variables
load_dotenv()

console = Console()


@click.command()
@click.option('--model', default='gpt-4', help='OpenAI model to use')
@click.option('--config', default='config.yaml', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(model: str, config: str, verbose: bool):
    """AutoAV - AI-Driven Antivirus Suite
    
    Describe your security problem in natural language and let AI investigate.
    
    Examples:
        autoav "I'm getting suspicious pop-ups on my system"
        autoav "I think I have a search marquis"
    """
    
    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        console.print("[red]Error: OPENAI_API_KEY environment variable not set[/red]")
        console.print("Please set your OpenAI API key:")
        console.print("export OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    # Initialize components
    permission_manager = PermissionManager()
    file_inspector = FileInspector(permission_manager)
    tool_registry = ToolRegistry(file_inspector)
    openai_client = OpenAIClient(api_key, model, tool_registry)
    session_manager = SessionManager(openai_client)
    
    # Start interactive session
    run_interactive_session(session_manager, verbose)


def run_interactive_session(session_manager: SessionManager, verbose: bool):
    """Run the interactive CLI session"""
    
    console.print("[bold blue]AutoAV - AI-Driven Antivirus Suite[/bold blue]")
    console.print("Describe your security problem and I'll investigate it for you.\n")
    console.print("Examples:")
    console.print("  • 'I'm getting suspicious pop-ups on my system'")
    console.print("  • 'I think I have a search marquis'")
    console.print("  • 'My browser is redirecting to strange websites'\n")
    console.print("Type 'quit' or 'exit' to end the session.\n")
    
    while True:
        # Get user input
        problem_description = Prompt.ask("[bold green]Describe your problem[/bold green]")
        
        if problem_description.lower() in ['quit', 'exit', 'q']:
            console.print("[yellow]Goodbye![/yellow]")
            break
        
        if not problem_description.strip():
            continue
        
        # Start investigation
        console.print(f"\n[bold]Starting Investigation[/bold]")
        console.print(f"[dim]Problem:[/dim] {problem_description}")
        console.print()
        
        # Run the investigation
        result = asyncio.run(session_manager.investigate(problem_description))
        
        # Display results
        console.print("\n" + "="*60)
        console.print("[bold green]🎉 Investigation Complete![/bold green]")
        console.print("="*60 + "\n")
        console.print(result)
        console.print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    main() 