"""
File Inspector for AutoAV
Handles file reading, system analysis, and security checks
"""

import asyncio
import os
import json
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import psutil
import magic

from permissions.permission_manager import PermissionManager
from clamav.scanner import ClamAVScanner


class FileInspector:
    """Handles file inspection and system analysis operations"""
    
    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager
        self.clamav_scanner = ClamAVScanner()
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # Restricted directories that require special permission
        self.restricted_dirs = ['/System', '/Library', '/bin', '/sbin', '/usr']
    
    
    async def list_processes(self, filter: str = None) -> str:
        """List running processes with details"""
        
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'exe']):
            proc_info = proc.info
            
            # Apply filter if specified
            if filter and filter.lower() not in proc_info['name'].lower():
                continue
            
            # Get additional info
            cmdline = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
            memory_mb = proc_info['memory_info'].rss / 1024 / 1024 if proc_info['memory_info'] else 0
            exe_path = proc_info['exe'] if proc_info['exe'] else 'N/A'
            
            processes.append({
                'pid': proc_info['pid'],
                'name': proc_info['name'],
                'cmdline': cmdline,
                'memory_mb': round(memory_mb, 2),
                'exe_path': exe_path
            })
        
        # Sort by memory usage
        processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        
        # Format output
        result = f"Found {len(processes)} processes"
        if filter:
            result += f" matching '{filter}'"
        result += ":\n\n"
        
        for proc in processes[:20]:  # Limit to top 20
            result += f"PID: {proc['pid']}\n"
            result += f"Name: {proc['name']}\n"
            result += f"Memory: {proc['memory_mb']} MB\n"
            result += f"Path: {proc['exe_path']}\n"
            if proc['cmdline']:
                result += f"Command: {proc['cmdline']}\n"
            result += "-" * 50 + "\n"
        
        return result
    
    
    async def read_file(self, path: str, max_size: int = None) -> str:
        """Read file contents safely"""
        
        if max_size is None:
            max_size = self.max_file_size
        
        # Validate path
        file_path = Path(path).resolve()
        
        # Check if file exists
        if not file_path.exists():
            return f"Error: File '{path}' does not exist"
        
        # Check if it's a file
        if not file_path.is_file():
            return f"Error: '{path}' is not a file"
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > max_size:
            return f"Error: File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)"
        
        # Check permissions and handle restricted files
        if not await self.permission_manager.can_read_file(str(file_path)):
            # Try to read with sudo if it's a restricted file
            if self._is_restricted_path(str(file_path)):
                return await self._read_file_with_sudo(str(file_path), max_size)
            else:
                return f"Error: Permission denied reading '{path}'"
        
        # Determine file type
        mime_type = magic.from_file(str(file_path), mime=True)
        
        # Read file based on type
        if mime_type.startswith('text/') or mime_type in ['application/json', 'application/xml']:
            # Text file - read content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return f"""File: {path}
                    Type: {mime_type}
                    Size: {file_size} bytes
                    Content:
                    {content}"""
        
        else:
            # Binary file - return metadata only
            file_hash = self._calculate_file_hash(file_path)
            
            return f"""File: {path}
            Type: {mime_type} (binary)
            Size: {file_size} bytes
            SHA256: {file_hash}
            Note: Binary file - content not displayed for security reasons"""
    

    async def scan_file(self, path: str) -> str:
        """Scan file with ClamAV"""
        
        # Validate path
        file_path = Path(path).resolve()
        
        if not file_path.exists():
            return f"Error: File '{path}' does not exist"
        
        if not file_path.is_file():
            return f"Error: '{path}' is not a file"
        
        # Check permissions and handle restricted files
        if not await self.permission_manager.can_read_file(str(file_path)):
            # Try to scan with sudo if it's a restricted file
            if self._is_restricted_path(str(file_path)):
                return await self._scan_file_with_sudo(str(file_path))
            else:
                return f"Error: Permission denied scanning '{path}'"
        
        # Scan with ClamAV
        scan_result = await self.clamav_scanner.scan_file(str(file_path))
        
        return f"""ClamAV Scan Results for: {path}
                {scan_result}"""
    

    async def find_files(self, pattern: str, directory: str = None, max_results: int = 50) -> str:
        """Find files matching pattern"""
        
        if directory is None:
            directory = str(Path.home())
        
        search_path = Path(directory).resolve()
        
        if not search_path.exists():
            return f"Error: Directory '{directory}' does not exist"
        
        if not search_path.is_dir():
            return f"Error: '{directory}' is not a directory"
        
        # Check permissions
        if not await self.permission_manager.can_read_directory(str(search_path)):
            return f"Error: Permission denied searching '{directory}'"
        
        # Find files
        found_files = []
        for file_path in search_path.rglob(pattern):
            if file_path.is_file():
                stat = file_path.stat()
                found_files.append({
                    'path': str(file_path),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
                
                if len(found_files) >= max_results:
                    break
        
        # Format results
        result = f"Found {len(found_files)} files matching '{pattern}' in '{directory}':\n\n"
        
        for file_info in found_files:
            result += f"Path: {file_info['path']}\n"
            result += f"Size: {file_info['size']} bytes\n"
            result += f"Modified: {file_info['modified']}\n"
            result += "-" * 30 + "\n"
        
        return result
    

    async def get_file_info(self, path: str) -> str:
        """Get detailed file information"""
        
        file_path = Path(path).resolve()
        
        if not file_path.exists():
            return f"Error: File '{path}' does not exist"
        
        # Check permissions
        if not await self.permission_manager.can_read_file(str(file_path)):
            return f"Error: Permission denied accessing '{path}'"
        
        stat = file_path.stat()
        mime_type = magic.from_file(str(file_path), mime=True)
        file_hash = self._calculate_file_hash(file_path)
        
        # Get additional info
        is_executable = os.access(str(file_path), os.X_OK)
        is_readable = os.access(str(file_path), os.R_OK)
        is_writable = os.access(str(file_path), os.W_OK)
        
        return f"""File Information: {path}
            Type: {mime_type}
            Size: {stat.st_size} bytes
            Created: {datetime.fromtimestamp(stat.st_ctime).isoformat()}
            Modified: {datetime.fromtimestamp(stat.st_mtime).isoformat()}
            Accessed: {datetime.fromtimestamp(stat.st_atime).isoformat()}
            SHA256: {file_hash}
            Permissions: {'r' if is_readable else '-'}{'w' if is_writable else '-'}{'x' if is_executable else '-'}
            Owner: {stat.st_uid}
            Group: {stat.st_gid}"""
        

    async def list_directory(self, path: str, show_hidden: bool = False) -> str:
        """List directory contents"""
        
        dir_path = Path(path).resolve()
        
        if not dir_path.exists():
            return f"Error: Directory '{path}' does not exist"
        
        if not dir_path.is_dir():
            return f"Error: '{path}' is not a directory"
        
        # Check permissions
        if not await self.permission_manager.can_read_directory(str(dir_path)):
            return f"Error: Permission denied listing '{path}'"
        
        items = []
        for item in dir_path.iterdir():
            # Skip hidden files unless requested
            if not show_hidden and item.name.startswith('.'):
                continue
            
            stat = item.stat()
            items.append({
                'name': item.name,
                'type': 'directory' if item.is_dir() else 'file',
                'size': stat.st_size if item.is_file() else 0,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        # Sort items
        items.sort(key=lambda x: (x['type'], x['name']))
        
        # Format output
        result = f"Directory contents of '{path}':\n\n"
        
        for item in items:
            result += f"{'[DIR]' if item['type'] == 'directory' else '[FILE]'} {item['name']}\n"
            if item['type'] == 'file':
                result += f"  Size: {item['size']} bytes\n"
            result += f"  Modified: {item['modified']}\n"
            result += "-" * 30 + "\n"
        
        return result
    

    async def check_browser_extensions(self, browser: str = "all") -> str:
        """Check for suspicious browser extensions"""
        
        result = "Browser Extensions Analysis:\n\n"
        
        browsers_to_check = []
        if browser == "all" or browser == "chrome":
            browsers_to_check.append(("Chrome", "~/Library/Application Support/Google/Chrome/Default/Extensions"))
        if browser == "all" or browser == "safari":
            browsers_to_check.append(("Safari", "~/Library/Safari/Extensions"))
        if browser == "all" or browser == "firefox":
            browsers_to_check.append(("Firefox", "~/Library/Application Support/Firefox/Profiles"))
        
        for browser_name, ext_path in browsers_to_check:
            result += f"=== {browser_name} ===\n"
            
            ext_dir = Path(ext_path).expanduser()
            if ext_dir.exists():
                extensions = list(ext_dir.iterdir())
                result += f"Found {len(extensions)} extension directories\n"
                
                for ext in extensions[:10]:  # Limit to first 10
                    if ext.is_dir():
                        result += f"  - {ext.name}\n"
            else:
                result += "Extension directory not found\n"
            
            result += "\n"
        
        return result
    

    async def check_startup_items(self) -> str:
        """Check for suspicious startup items"""
        
        result = "Startup Items Analysis:\n\n"
        
        # Check common startup locations
        startup_locations = [
            ("LaunchAgents", "~/Library/LaunchAgents"),
            ("LaunchDaemons", "/Library/LaunchDaemons"),
            ("System LaunchDaemons", "/System/Library/LaunchDaemons"),
            ("Login Items", "~/Library/Application Support/com.apple.backgroundtaskmanagementagent")
        ]
        
        for name, path in startup_locations:
            result += f"=== {name} ===\n"
            
            check_path = Path(path).expanduser()
            if check_path.exists():
                items = list(check_path.glob("*.plist"))
                result += f"Found {len(items)} items\n"
                
                for item in items[:5]:  # Limit to first 5
                    result += f"  - {item.name}\n"
            else:
                result += "Directory not found\n"
            
            result += "\n"
        
        return result
    

    async def get_network_connections(self, filter: str = None) -> str:
        """Get active network connections"""
        
        connections = []
        
        for conn in psutil.net_connections():
            # Apply filter if specified
            if filter:
                process = psutil.Process(conn.pid) if conn.pid else None
                if process and filter.lower() not in process.name().lower():
                    continue
            
            process_name = "Unknown"
            if conn.pid:
                process = psutil.Process(conn.pid)
                process_name = process.name()
            
            connections.append({
                'pid': conn.pid,
                'process': process_name,
                'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A",
                'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                'status': conn.status,
                'type': 'TCP' if conn.type == 1 else 'UDP'
            })
        
        # Format output
        result = f"Found {len(connections)} network connections"
        if filter:
            result += f" matching '{filter}'"
        result += ":\n\n"
        
        for conn in connections[:20]:  # Limit to first 20
            result += f"Process: {conn['process']} (PID: {conn['pid']})\n"
            result += f"Type: {conn['type']}\n"
            result += f"Local: {conn['local_address']}\n"
            result += f"Remote: {conn['remote_address']}\n"
            result += f"Status: {conn['status']}\n"
            result += "-" * 40 + "\n"
        
        return result
    

    def _is_restricted_path(self, path: str) -> bool:
        """Check if a path is in a restricted directory"""
        path_parts = Path(path).parts
        
        for restricted_dir in self.restricted_dirs:
            if restricted_dir in path_parts:
                return True
        
        return False
    

    async def _scan_file_with_sudo(self, file_path: str) -> str:
        """Scan a file with ClamAV using sudo if needed"""
        
        # Check if ClamAV is available
        if not self.clamav_scanner.is_available():
            return "Error: ClamAV not available for sudo scanning"
        
        # Use sudo to run clamscan
        clamscan_path = self.clamav_scanner.clamscan_path
        
        scan_result = await self.permission_manager.execute_sudo_command(
            [clamscan_path, '--no-summary', file_path],
            f"scan file with ClamAV: {file_path}"
        )
        
        if scan_result.startswith("Error"):
            return f"Error scanning file with sudo: {scan_result}"
        
        return f"""ClamAV Scan Results for: {file_path} (with sudo)
                {scan_result}"""
    

    async def _read_file_with_sudo(self, file_path: str, max_size: int) -> str:
        """Read a file using sudo if needed"""
        
        # Get file size first
        size_result = await self.permission_manager.execute_sudo_command(
            ['stat', '-f', '%z', file_path],
            f"get file size: {file_path}"
        )
        
        if size_result.startswith("Error"):
            return f"Error: Could not get file size: {size_result}"
        
        file_size = int(size_result.strip())
        
        # Check file size
        if file_size > max_size:
            return f"Error: File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)"
        
        # Read file content with sudo
        content_result = await self.permission_manager.execute_sudo_command(
            ['cat', file_path],
            f"read file: {file_path}"
        )
        
        if content_result.startswith("Error"):
            return f"Error: Could not read file: {content_result}"
        
        # Try to determine file type
        mime_type = magic.from_buffer(content_result.encode('utf-8', errors='ignore')[:1024], mime=True)
        
        # Return content based on type
        if mime_type.startswith('text/') or mime_type in ['application/json', 'application/xml']:
            return f"""File: {file_path}
                    Type: {mime_type}
                    Size: {file_size} bytes
                    Content (read with sudo):
                    {content_result}"""
        else:
            # For binary files, just return metadata
            return f"""File: {file_path}
                    Type: {mime_type} (binary)
                    Size: {file_size} bytes
                    Note: Binary file - content not displayed for security reasons
                    Read with sudo: Yes"""
    

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest() 