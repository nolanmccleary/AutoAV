#!/usr/bin/env python3
"""
Basic functionality test for AutoAV
Tests core components without excessive error handling
"""

import asyncio
import os
from pathlib import Path

from permissions.permission_manager import PermissionManager
from inspector.file_inspector import FileInspector
from tools.tool_registry import ToolRegistry


async def test_basic_functionality():
    """Test basic functionality of core components"""
    
    print("🧪 Testing AutoAV Basic Functionality")
    print("=" * 50)
    
    # Test 1: Permission Manager
    print("\n1. Testing Permission Manager...")
    pm = PermissionManager()
    
    # Test file access
    home_dir = str(Path.home())
    can_read_home = await pm.can_read_file(f"{home_dir}/.bash_profile")
    print(f"   Can read home file: {can_read_home}")
    
    # Test 2: File Inspector
    print("\n2. Testing File Inspector...")
    fi = FileInspector(pm)
    
    # Test process listing
    processes = await fi.list_processes()
    print(f"   Process listing: {len(processes)} chars returned")
    
    # Test file info
    file_info = await fi.get_file_info(__file__)
    print(f"   File info: {len(file_info)} chars returned")
    
    # Test 3: Tool Registry
    print("\n3. Testing Tool Registry...")
    tr = ToolRegistry(fi)
    
    tools = tr.get_available_tools()
    print(f"   Available tools: {len(tools)} tools registered")
    
    print("\n✅ Basic functionality tests completed!")
    print("System is ready for development and testing.")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality()) 