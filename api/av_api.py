from typing import List, Tuple
import subprocess


AVAILABLE_COMMANDS = [
    'ls', 'cat', 'head', 'tail', 'less', 'more', 'file', 'stat', 'find', 'locate', 'which', 'whereis',
    'du', 'df', 'mount', 'wc', 'grep', 'egrep', 'fgrep', 'awk', 'sed', 'sort', 'uniq',
    
    'ps', 'top', 'htop', 'pgrep', 'lsof', 'fuser',
    
    'netstat', 'ss', 'ifconfig', 'ip', 'route', 'arp', 'ping', 'traceroute', 'tracert', 'nslookup',
    'dig', 'host', 'whois', 'telnet', 'nc', 'nmap', 'curl', 'wget', 'ssh',

    'uname', 'hostname', 'whoami', 'id', 'who', 'w', 'last', 'lastlog', 'uptime', 'date',
    'free', 'vmstat', 'iostat', 'sar', 'dmesg', 'journalctl', 'systemctl', 'service',
    
    'passwd', 'chage', 'groups', 'getent', 'crontab', 'at',
    'lsattr', 'chattr', 'getfacl',
    
    'rpm', 'dpkg', 'apt', 'yum', 'dnf', 'pacman', 'brew', 'pip', 'npm',
    
    'clamscan', 'clamdscan', 'freshclam', 'chkrootkit', 'rkhunter', 'lynis', 'tripwire',
    
    'tail', 'head', 'grep', 'awk', 'sed', 'cut', 'tr', 'tee',
    
    'iotop', 'iftop', 'nethogs', 'htop', 'glances', 'atop', 'powertop',
    
    'strings', 'hexdump', 'xxd', 'od', 'file', 'md5sum', 'sha1sum', 'sha256sum',
    'objdump', 'nm', 'readelf', 'ldd', 'strace', 'ltrace', 'gdb', 'valgrind',
    
    'grep', 'awk', 'sed', 'cut', 'paste', 'join', 'comm', 'diff',
    'sort', 'uniq', 'wc', 'nl', 'fold', 'fmt', 'pr', 'column',
    
    'cd', 'pwd', 'pushd', 'popd', 'dirs', 'tree', 'ls', 'dir',
    
    'env', 'set', 'unset', 'export', 'alias', 'type', 'hash',
    'history', 'fc', 'jobs', 'bg', 'fg', 'wait', 'time', 'timeout',
    
    'echo', 'printf', 'test', '[', '[[', 'true', 'false', 'yes', 'no',
    'sleep', 'watch', 'seq', 'factor', 'bc', 'dc', 'expr', 'let',

    'man', 'info', 'help', 'apropos', 'whatis', 'whereis', 'which', 'type',
    'ldd', 'ldconfig', 'locale', 'localedef', 'iconv', 'gettext'
]



__all__ = [
    "api_execute_command"
]



def _execute_sudo_command(command: List[str], password: str) -> Tuple[str, int]:
    sudo_command = ['sudo', '-S'] + command
    result = subprocess.run(sudo_command, input=password.encode(), capture_output=True, text=True)
    if result.returncode != 0:
        raise f"Error: {result.stderr}"
   
    return result.stdout, result.returncode



def _execute_command(command: List[str]) -> Tuple[str, int]:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise f"Error: {result.stderr}"
    return result.stdout, result.returncode







########################################################
# API Functions
########################################################


def api_get_user_input(prompt: str) -> str:
    return input(prompt)




def api_execute_command(command: str, command_args: List[str] = None) -> dict:
    if command not in AVAILABLE_COMMANDS:
        raise f"Error: Command '{command}' is not available"
    
    if command_args is None:
        command_args = []
    
    result, returncode = _execute_command([command] + command_args)
    
    return str({
        "command": command,
        "args": command_args,
        "output": result,
        "return_code": returncode
    })