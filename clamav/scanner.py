"""
ClamAV Scanner for AutoAV
Handles virus scanning integration
"""

import asyncio
import subprocess
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ClamAVScanner:
    """Handles ClamAV virus scanning operations"""
    
    def __init__(self):
        self.clamscan_path = self._find_clamscan()
        self.database_path = self._find_database()
        self.scan_timeout = 30  # seconds
    
    def _find_clamscan(self) -> Optional[str]:
        """Find the clamscan executable"""
        
        possible_paths = [
            '/usr/local/bin/clamscan',
            '/opt/homebrew/bin/clamscan',
            '/usr/bin/clamscan',
            'clamscan'  # Try PATH
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                continue
        
        return None
    
    def _find_database(self) -> Optional[str]:
        """Find the ClamAV database directory"""
        
        possible_paths = [
            '/usr/local/share/clamav',
            '/opt/homebrew/share/clamav',
            '/usr/share/clamav',
            '/var/lib/clamav'
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                # Check if database files exist
                db_files = list(Path(path).glob("*.cvd")) + list(Path(path).glob("*.cud"))
                if db_files:
                    return path
        
        return None
    
    async def scan_file(self, file_path: str) -> str:
        """Scan a single file with ClamAV"""
        
        if not self.clamscan_path:
            return "Error: ClamAV not found. Please install ClamAV first:\nbrew install clamav"
        
        if not self.database_path:
            return "Error: ClamAV database not found. Please update virus definitions:\nfreshclam"
        
        try:
            # Build clamscan command
            cmd = [
                self.clamscan_path,
                '--database=' + self.database_path,
                '--no-summary',
                '--infected',
                file_path
            ]
            
            # Run scan with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.scan_timeout
                )
                
                # Parse results
                if process.returncode == 0:
                    return "Status: Clean (no threats detected)"
                elif process.returncode == 1:
                    # Virus found
                    output = stdout.decode('utf-8', errors='ignore')
                    return f"Status: INFECTED\nDetails: {output}"
                else:
                    # Error occurred
                    error = stderr.decode('utf-8', errors='ignore')
                    return f"Error during scan: {error}"
                
            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.terminate()
                await process.wait()
                return "Error: Scan timed out"
                
        except Exception as e:
            return f"Error running ClamAV scan: {str(e)}"
    
    async def scan_directory(self, directory_path: str) -> str:
        """Scan a directory with ClamAV"""
        
        if not self.clamscan_path:
            return "Error: ClamAV not found. Please install ClamAV first:\nbrew install clamav"
        
        if not self.database_path:
            return "Error: ClamAV database not found. Please update virus definitions:\nfreshclam"
        
        try:
            # Build clamscan command for directory
            cmd = [
                self.clamscan_path,
                '--database=' + self.database_path,
                '--recursive',
                '--infected',
                directory_path
            ]
            
            # Run scan with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.scan_timeout * 2  # Longer timeout for directories
                )
                
                # Parse results
                output = stdout.decode('utf-8', errors='ignore')
                error = stderr.decode('utf-8', errors='ignore')
                
                if process.returncode == 0:
                    return "Status: Clean (no threats detected in directory)"
                elif process.returncode == 1:
                    return f"Status: INFECTED\nDetails:\n{output}"
                else:
                    return f"Error during directory scan: {error}"
                
            except asyncio.TimeoutError:
                # Kill the process if it times out
                process.terminate()
                await process.wait()
                return "Error: Directory scan timed out"
                
        except Exception as e:
            return f"Error running ClamAV directory scan: {str(e)}"
    
    async def update_database(self) -> str:
        """Update ClamAV virus definitions"""
        
        try:
            # Try to run freshclam
            process = await asyncio.create_subprocess_exec(
                'freshclam',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=60  # Longer timeout for updates
            )
            
            output = stdout.decode('utf-8', errors='ignore')
            error = stderr.decode('utf-8', errors='ignore')
            
            if process.returncode == 0:
                return f"Database updated successfully:\n{output}"
            else:
                return f"Error updating database: {error}"
                
        except asyncio.TimeoutError:
            return "Error: Database update timed out"
        except FileNotFoundError:
            return "Error: freshclam not found. Please install ClamAV first:\nbrew install clamav"
        except Exception as e:
            return f"Error updating database: {str(e)}"
    
    def get_status(self) -> Dict[str, Any]:
        """Get ClamAV scanner status"""
        
        return {
            "clamscan_available": self.clamscan_path is not None,
            "clamscan_path": self.clamscan_path,
            "database_available": self.database_path is not None,
            "database_path": self.database_path,
            "scan_timeout": self.scan_timeout
        }
    
    def is_available(self) -> bool:
        """Check if ClamAV is available and properly configured"""
        return self.clamscan_path is not None and self.database_path is not None 