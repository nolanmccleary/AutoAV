"""
Permission Manager for AutoAV
Handles filesystem access permissions and sudo requests
"""

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console
from rich.prompt import Confirm

console = Console()


class PermissionManager:
    """Manages filesystem access permissions and sudo requests"""
    
    def __init__(self):
        self.sudo_granted = False
        self.sudo_timeout = 300  # 5 minutes
        self.last_sudo_time = None
        self.restricted_dirs = ['/System', '/Library', '/bin', '/sbin', '/usr']
        self.allowed_dirs = ['/Users', '/Applications', '/tmp']
    
    async def can_read_file(self, file_path: str) -> bool:
        """Check if we can read a file"""
        
        path = Path(file_path).resolve()
        
        # Check if path is in restricted directories
        if self._is_restricted_path(str(path)):
            return await self._request_sudo_access(f"read file: {file_path}")
        
        # Check if file is readable
        return os.access(str(path), os.R_OK)
    
    async def execute_sudo_command(self, command: List[str], description: str) -> str:
        """Execute a command with sudo if needed"""
        
        # Check if we have active sudo access
        if self.sudo_granted and self.last_sudo_time:
            import time
            if time.time() - self.last_sudo_time < self.sudo_timeout:
                # Use sudo with -n flag (no password needed)
                sudo_command = ['sudo', '-n'] + command
                process = await asyncio.create_subprocess_exec(
                    *sudo_command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                return stdout.decode('utf-8', errors='ignore')
        
        # If no active sudo access, request it
        if await self._request_sudo_access(description):
            # Try with -n flag first
            sudo_command = ['sudo', '-n'] + command
            process = await asyncio.create_subprocess_exec(
                *sudo_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return stdout.decode('utf-8', errors='ignore')
            
            # If -n failed, try interactive sudo
            stderr_text = stderr.decode('utf-8', errors='ignore').lower()
            if 'password' in stderr_text or 'sudo' in stderr_text:
                console.print("[yellow]Sudo requires password. Please enter your password when prompted.[/yellow]")
                
                import subprocess
                result = subprocess.run(
                    ['sudo'] + command,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return result.stdout
                else:
                    return f"Error: {result.stderr}"
            
            return f"Error: {stderr.decode('utf-8', errors='ignore')}"
        
        return "Error: Sudo access denied by user"
    
    async def can_read_directory(self, dir_path: str) -> bool:
        """Check if we can read a directory"""
        
        path = Path(dir_path).resolve()
        
        # Check if path is in restricted directories
        if self._is_restricted_path(str(path)):
            return await self._request_sudo_access(f"read directory: {dir_path}")
        
        # Check if directory is readable
        return os.access(str(path), os.R_OK)
    
    async def can_write_file(self, file_path: str) -> bool:
        """Check if we can write to a file (should always return False for security)"""
        return False  # AutoAV is read-only
    
    async def can_execute_file(self, file_path: str) -> bool:
        """Check if we can execute a file (should always return False for security)"""
        return False  # AutoAV does not execute files
    
    def _is_restricted_path(self, path: str) -> bool:
        """Check if a path is in a restricted directory"""
        
        path_parts = Path(path).parts
        
        for restricted_dir in self.restricted_dirs:
            if restricted_dir in path_parts:
                return True
        
        return False
    
    async def _request_sudo_access(self, operation: str) -> bool:
        """Request sudo access for a specific operation"""
        
        # Check if we already have sudo access
        if self.sudo_granted and self.last_sudo_time:
            import time
            if time.time() - self.last_sudo_time < self.sudo_timeout:
                return True
        
        # Request sudo access from user
        console.print(f"\n[yellow]Permission required for: {operation}[/yellow]")
        console.print("This operation requires elevated privileges.")
        
        granted = Confirm.ask("Grant sudo access for this operation?", default=False)
        
        if granted:
            # Test sudo access
            if await self._test_sudo_access():
                self.sudo_granted = True
                import time
                self.last_sudo_time = time.time()
                console.print("[green]Sudo access granted.[/green]")
                return True
            else:
                console.print("[red]Sudo access test failed. Please check your password.[/red]")
                return False
        else:
            console.print("[yellow]Operation cancelled by user.[/yellow]")
            return False
    
    async def _test_sudo_access(self) -> bool:
        """Test if sudo access is working"""
        
        try:
            # First, try without password (in case sudo is configured for no password)
            process = await asyncio.create_subprocess_exec(
                'sudo', '-n', 'echo', 'test',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return True
            
            # If that failed, it might be because password is required
            # Check if the error message indicates password is needed
            stderr_text = stderr.decode('utf-8', errors='ignore').lower()
            if 'password' in stderr_text or 'sudo' in stderr_text:
                console.print("[yellow]Sudo requires password. Please enter your password when prompted.[/yellow]")
                
                # For interactive sudo, we need to run it without capturing output
                # so the user can see and respond to the password prompt
                console.print("[cyan]Testing sudo access with password prompt...[/cyan]")
                
                # Use subprocess.run without capturing output to allow interactive password entry
                import subprocess
                try:
                    result = subprocess.run(
                        ['sudo', 'echo', 'test'],
                        timeout=30  # 30 second timeout for password entry
                    )
                    return result.returncode == 0
                except subprocess.TimeoutExpired:
                    console.print("[red]Sudo password prompt timed out.[/red]")
                    return False
                except Exception as e:
                    console.print(f"[red]Sudo test failed: {e}[/red]")
                    return False
            
            return False
            
        except Exception as e:
            console.print(f"[red]Sudo test failed with exception: {e}[/red]")
            return False
    
    def get_permission_summary(self) -> Dict[str, Any]:
        """Get a summary of current permissions"""
        
        import time
        
        return {
            "sudo_granted": self.sudo_granted,
            "sudo_timeout": self.sudo_timeout,
            "last_sudo_time": self.last_sudo_time,
            "sudo_active": (
                self.sudo_granted and 
                self.last_sudo_time and 
                (time.time() - self.last_sudo_time < self.sudo_timeout)
            ),
            "restricted_dirs": self.restricted_dirs,
            "allowed_dirs": self.allowed_dirs
        }
    
    def reset_sudo_access(self):
        """Reset sudo access (for testing or security)"""
        self.sudo_granted = False
        self.last_sudo_time = None
        console.print("[yellow]Sudo access reset.[/yellow]") 