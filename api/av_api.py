import os
import hashlib
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
import subprocess
import psutil
import magic


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
RESTRICTED_DIRS = ['/System', '/Library', '/bin', '/sbin', '/usr']
AVAILABLE_COMMANDS = [
    'cd', 'ls', 'cat', 'stat', 'ps', 'netstat', 'ifconfig', 'route', 'dig', 'ping', 'traceroute',
    'whoami', 'who', 'last', 'w', 'free', 'df', 'clamscan', 'clamdscan', 'freshclam', 'grep'
]



__all__ = [
    "api_read_file",
    "api_list_network_connections",
    "api_list_processes",
    "api_get_file_info",
    "api_find_files",
    "api_list_directory_contents",
    "api_execute_command"
]



def _execute_sudo_command(command: List[str], password: str) -> Tuple[str, int]:
    """Execute a command with sudo"""
    sudo_command = ['sudo', '-S'] + command
    result = subprocess.run(sudo_command, input=password.encode(), capture_output=True, text=True)
    if result.returncode != 0:
        raise f"Error: {result.stderr}"
   
    return result.stdout, result.returncode



def _execute_command(command: List[str]) -> Tuple[str, int]:
    """Execute a command"""
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise f"Error: {result.stderr}"
    return result.stdout, result.returncode



def _can_read_file(file_path: str) -> bool:
    """Check if we can read a file"""
    path = Path(file_path).resolve()
    return os.access(str(path), os.R_OK)



def _can_read_directory(dir_path: str) -> bool:
    """Check if we can read a directory"""
    path = Path(dir_path).resolve()
    return os.access(str(path), os.R_OK)



def _is_restricted_path(path: str) -> bool:
    """Check if a path is in a restricted directory"""
    path_parts = Path(path).parts
    for restricted_dir in RESTRICTED_DIRS:
        if restricted_dir in path_parts:
            return True
    return False



def _calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest() 
    
    

def _read_file_with_sudo(file_path: str, max_size: int) -> dict:
    """Read a file using sudo if needed"""
    
    size_result, returncode = _execute_sudo_command(
        command=['stat', '-f', '%z', file_path],
        password=input(f"Sudo permissions required for reading file: {file_path} - Please enter your password: ")
    )
    
    if returncode != 0:
        raise f"Error: Could not get file size: {size_result}"
    
    file_size = int(size_result.strip())
    
    if file_size > max_size:
        raise f"Error: File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)"
    
    content_result, returncode = _execute_sudo_command(
        command = ['cat', file_path],
        password=input(f"Sudo permissions required for catting file: {file_path} - Please enter your password: ")
    )
    
    if returncode != 0:
        raise f"Error: Could not read file: {content_result}"
    
    mime_type = magic.from_buffer(content_result.encode('utf-8', errors='ignore')[:1024], mime=True)
    return {
        "file_path" : file_path,
        "mime_type" : mime_type,
        "size_in_bytes" : file_size,
        "content" : content_result
    }



def _get_stats(path: str) -> dict:
    """Get stats for a file or directory"""
    path = Path(path).resolve()
    stat = path.stat()
    return {
        "path": path,
        "size_in_bytes": stat.st_size,
        "type": "file" if path.is_file() else "directory" if path.is_dir() else "N/A",
        "mime_type": magic.from_file(str(path), mime=True),
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
        "owner": stat.st_uid,
        "group": stat.st_gid,
    }




########################################################
# API Functions
########################################################


def api_execute_command(command: str, command_args: List[str] = None) -> dict:
    """Execute a command"""
    if command not in AVAILABLE_COMMANDS:
        raise f"Error: Command '{command}' is not available"
    
    if command_args is None:
        command_args = []
    
    result, returncode = _execute_command([command] + command_args)
    
    return {
        "command": command,
        "args": command_args,
        "output": result,
        "return_code": returncode
    }
    


def api_read_file(file_path: str, max_size: int = None) -> dict:
    """Read file contents safely"""
    
    if max_size is None:
        max_size = MAX_FILE_SIZE
    
    stats = _get_stats(file_path)
    
    if not _can_read_file(str(file_path)):
        if _is_restricted_path(str(file_path)):
            return _read_file_with_sudo(str(file_path), max_size)
        else:
            raise f"Error: Permission denied reading '{file_path}'"
    
    if stats["mime_type"].startswith('text/') or stats["mime_type"] in ['application/json', 'application/xml']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return {
            **stats,
            "content": content
        }
    
    else:
        return stats



def api_list_network_connections(filter: str = None) -> dict:
    """Get active network connections"""
    connections = []
    for i, conn in enumerate(psutil.net_connections()):
        process_name = "Unknown"
        if conn.pid:
            process = psutil.Process(conn.pid)
            process_name = process.name()
            if filter and filter not in process_name.lower():
                continue
        
        connections.append({
            'connection': i,
            'pid': conn.pid if conn.pid else "N/A",
            'process': process_name,
            'local_address': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A",
            'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
            'status': conn.status,
            'type': 'TCP' if conn.type == 1 else 'UDP'
        })
    
    return {
        "filter": filter if filter else "All",
        "connections": connections,
        "num_connections_found": len(connections)
    }



def api_list_processes(filter: str = None) -> dict:
    """List running processes with details"""
    
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'exe']):
        proc_info = proc.info
        
        if filter and filter.lower() not in proc_info['name'].lower():
            continue
        
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
    
    processes.sort(key=lambda x: x['memory_mb'], reverse=True)
    
    result = {
        "filter": filter if filter else "All",
        "processes": processes,
        "num_processes_found": len(processes)
    }
    
    return result



def api_get_file_info(path: str) -> dict:
    """Get detailed file information"""
    
    file_path = Path(path).resolve()
    
    if not file_path.exists():
        raise f"Error: File '{path}' does not exist"
    
    if not _can_read_file(str(file_path)):
        raise f"Error: Permission denied accessing '{path}'"
    
    file_hash = _calculate_file_hash(file_path)
    
    is_executable = os.access(str(file_path), os.X_OK)
    is_readable = os.access(str(file_path), os.R_OK)
    is_writable = os.access(str(file_path), os.W_OK)
    
    return {
        **_get_stats(str(file_path)),
        "sha256": file_hash,
        "permissions": f"{'r' if is_readable else '-'}{'w' if is_writable else '-'}{'x' if is_executable else '-'}",
    }



def api_find_files(pattern: str, directory: str = None, max_results: int = 50) -> dict:
    """Recursively find files matching pattern inside a directory"""
    
    if directory is None:
        directory = str(Path.home())
    
    search_path = Path(directory).resolve()
    
    if not search_path.exists():
        raise f"Error: Directory '{directory}' does not exist"
    
    if not search_path.is_dir():
        raise f"Error: '{directory}' is not a directory"
    
    if not _can_read_directory(str(search_path)):
        raise f"Error: Permission denied searching '{directory}'"
    
    result = {
        "directory" : directory,
        "match_pattern" : pattern,
        "matches" : []}

    for file_path in search_path.rglob(pattern):
        if file_path.is_file():
            result["matches"].append(_get_stats(str(file_path)))
            
            if len(result["matches"]) >= max_results:
                break

    result["num_matches"] = len(result["matches"])
    
    return result



def api_list_directory_contents(directory_path: str, show_hidden: bool = False) -> dict:
    """List directory contents"""
    
    dir_path = Path(directory_path).resolve()
    
    if not dir_path.exists():
        raise f"Error: Directory '{directory_path}' does not exist"
    
    if not dir_path.is_dir():
        raise f"Error: '{directory_path}' is not a directory"
    
    if not _can_read_directory(str(dir_path)):
        raise f"Error: Permission denied listing '{directory_path}'"
    
    items = []
    for item in dir_path.iterdir():
        if not show_hidden and item.name.startswith('.'):
            continue
        
        items.append({
            "name": item.name,
            **_get_stats(str(item))
        })
    
    return {
        "dir_path": directory_path,
        "contents": items
    }