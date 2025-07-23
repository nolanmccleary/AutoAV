#!/usr/bin/env python3
"""
Test script for sudo handling in AutoAV
This script tests the permission manager's sudo handling capabilities
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from permissions.permission_manager import PermissionManager
from rich.console import Console

console = Console()


async def test_sudo_handling():
    """Test sudo handling functionality"""
    
    console.print("[bold blue]Testing AutoAV Sudo Handling[/bold blue]")
    console.print("=" * 50)
    
    permission_manager = PermissionManager()
    
    # Test 1: Check if we can read a system file
    console.print("\n[cyan]Test 1: Checking access to system file[/cyan]")
    system_file = "/etc/hosts"
    
    can_read = await permission_manager.can_read_file(system_file)
    console.print(f"Can read {system_file}: {can_read}")
    
    # Test 2: Try to execute a sudo command
    console.print("\n[cyan]Test 2: Testing sudo command execution[/cyan]")
    
    result = await permission_manager.execute_sudo_command(
        ['echo', 'test'],
        "test sudo command"
    )
    
    console.print(f"Sudo command result: {result}")
    
    # Test 3: Check permission summary
    console.print("\n[cyan]Test 3: Permission summary[/cyan]")
    summary = permission_manager.get_permission_summary()
    
    for key, value in summary.items():
        console.print(f"  {key}: {value}")
    
    console.print("\n[green]Sudo handling test completed![/green]")


if __name__ == "__main__":
    asyncio.run(test_sudo_handling()) 