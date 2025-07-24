"""
Minimal ClamAV Scanner for AutoAV
"""

import asyncio
import subprocess
from pathlib import Path


class ClamAVScanner:
    """Minimal ClamAV scanner"""
    
    def __init__(self):
        self.clamscan_path = self._find_clamscan()
    
    def _find_clamscan(self) -> str:
        """Find clamscan executable"""
        possible_paths = [
            '/usr/local/bin/clamscan',
            '/opt/homebrew/bin/clamscan',
            '/usr/bin/clamscan',
            'clamscan'
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return path
            except:
                continue
        
        return 'clamscan'  # Fallback
    
    async def scan_file(self, file_path: str) -> str:
        """Scan a file with ClamAV"""
        
        if not Path(file_path).exists():
            return f"Error: File '{file_path}' not found"
        
        try:
            cmd = [self.clamscan_path, '--no-summary', file_path]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=30
            )
            
            if process.returncode == 0:
                return "Status: Clean"
            elif process.returncode == 1:
                return f"Status: INFECTED\n{stdout.decode()}"
            else:
                return f"Error: {stderr.decode()}"
                
        except asyncio.TimeoutError:
            return "Error: Scan timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if ClamAV is available"""
        try:
            result = subprocess.run([self.clamscan_path, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False 