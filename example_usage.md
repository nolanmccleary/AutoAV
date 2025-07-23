# AutoAV Example Usage

This guide demonstrates how to use AutoAV for different security investigation scenarios.

## Setup

1. **Install dependencies:**
   ```bash
   python setup.py
   ```

2. **Configure API key:**
   ```bash
   # Edit .env file and add your OpenAI API key
   OPENAI_API_KEY=your_actual_api_key_here
   ```

3. **Run AutoAV:**
   ```bash
   python main.py
   ```

## Example Scenarios

### 1. Suspicious Pop-ups Investigation

**User Input:**
```
I'm getting suspicious pop-ups on my system
```

**Expected AutoAV Behavior:**
1. Lists running processes to identify potential pop-up sources
2. Checks for processes with windows or GUI elements
3. Examines startup items and launch agents
4. Scans identified suspicious files with ClamAV
5. Provides analysis and recommendations

**Sample Investigation Flow:**
```
AutoAV: Investigating: I'm getting suspicious pop-ups on my system

[Tool Call] list_processes
[Result] Found 127 processes running...

[Tool Call] list_processes filter="chrome"
[Result] Found 3 Chrome processes...

[Tool Call] check_startup_items
[Result] Found 5 startup items...

[Tool Call] scan_file path="/Users/username/Library/LaunchAgents/suspicious.plist"
[Result] ClamAV Scan Results: Status: INFECTED - Found: Trojan.Generic

[Final Report] 
# AutoAV Investigation Report

**Session ID:** 20241201_143022
**Investigation Steps:** 4

## Summary
I found a suspicious launch agent that appears to be causing pop-ups. The file 
/Users/username/Library/LaunchAgents/suspicious.plist was flagged as infected 
by ClamAV with Trojan.Generic. This file is configured to run at startup and 
likely responsible for the pop-ups you're experiencing.

## Recommendations
1. Remove the infected file: /Users/username/Library/LaunchAgents/suspicious.plist
2. Check for other suspicious startup items
3. Run a full system scan
4. Consider resetting browser settings
```

### 2. Search Marquis Detection

**User Input:**
```
I think I have a search marquis
```

**Expected AutoAV Behavior:**
1. Checks browser extensions and settings
2. Examines DNS configuration
3. Looks for search engine hijacking
4. Scans browser configuration files
5. Checks for suspicious network connections

**Sample Investigation Flow:**
```
AutoAV: Investigating: I think I have a search marquis

[Tool Call] check_browser_extensions browser="all"
[Result] Browser Extensions Analysis:
=== Chrome ===
Found 8 extension directories
  - a1b2c3d4e5f6
  - g7h8i9j0k1l2

[Tool Call] read_file path="/Users/username/Library/Application Support/Google/Chrome/Default/Preferences"
[Result] File: /Users/username/Library/Application Support/Google/Chrome/Default/Preferences
Type: application/json
Size: 2048 bytes
Content:
{
  "default_search_provider": {
    "search_url": "http://searchmarquis.com/search?q={searchTerms}"
  }
}

[Tool Call] get_network_connections filter="chrome"
[Result] Found 5 network connections matching 'chrome'...

[Final Report]
# AutoAV Investigation Report

**Session ID:** 20241201_143045
**Investigation Steps:** 3

## Summary
I confirmed that you have a search marquis infection. Your Chrome browser's 
default search provider has been changed to "searchmarquis.com", which is a 
known search hijacker. The browser is making connections to suspicious domains.

## Recommendations
1. Reset Chrome's search settings to Google
2. Remove suspicious browser extensions
3. Clear browser cache and cookies
4. Run a full system scan for additional malware
5. Consider using a different browser temporarily
```

### 3. General Malware Investigation

**User Input:**
```
My computer is running slowly and I'm worried about malware
```

**Expected AutoAV Behavior:**
1. Lists all running processes to identify suspicious activity
2. Checks for high CPU/memory usage processes
3. Scans startup items and launch agents
4. Examines network connections
5. Performs targeted file scans

**Sample Investigation Flow:**
```
AutoAV: Investigating: My computer is running slowly and I'm worried about malware

[Tool Call] list_processes
[Result] Found 127 processes running...
PID: 1234
Name: suspicious_process
Memory: 512.5 MB
Path: /Users/username/Library/suspicious_process
Command: /Users/username/Library/suspicious_process --daemon

[Tool Call] scan_file path="/Users/username/Library/suspicious_process"
[Result] ClamAV Scan Results: Status: INFECTED - Found: Backdoor.Generic

[Tool Call] get_network_connections
[Result] Found 23 network connections...
Process: suspicious_process (PID: 1234)
Type: TCP
Local: 192.168.1.100:54321
Remote: 185.220.101.45:443
Status: ESTABLISHED

[Final Report]
# AutoAV Investigation Report

**Session ID:** 20241201_143100
**Investigation Steps:** 3

## Summary
I found a backdoor infection on your system. The process "suspicious_process" 
is consuming significant memory (512MB) and has been flagged as infected by 
ClamAV. It's making suspicious network connections to a remote server.

## Recommendations
1. Immediately terminate the suspicious_process
2. Remove the infected file: /Users/username/Library/suspicious_process
3. Check for persistence mechanisms in startup items
4. Change all passwords from a different device
5. Consider reinstalling the operating system
6. Enable firewall and security software
```

## Advanced Usage

### Using Different Models

```bash
# Use GPT-3.5-turbo (faster, cheaper)
python main.py --model gpt-3.5-turbo

# Use GPT-4 (more thorough, more expensive)
python main.py --model gpt-4
```

### Verbose Mode

```bash
# Enable verbose logging for debugging
python main.py --verbose
```

### Custom Configuration

```bash
# Use a custom configuration file
python main.py --config my_config.yaml
```

## Troubleshooting

### Common Issues

1. **"OpenAI API key not set"**
   - Edit `.env` file and add your API key
   - Or set environment variable: `export OPENAI_API_KEY=your_key`

2. **"ClamAV not found"**
   - Run: `brew install clamav`
   - Update database: `freshclam`

3. **"Permission denied"**
   - AutoAV will request sudo access when needed
   - You can deny access for sensitive operations

4. **"File too large"**
   - AutoAV limits file reading to 10MB by default
   - Binary files are scanned but not displayed

### Getting Help

- Check the logs in `autoav.log`
- Run with `--verbose` flag for detailed output
- Ensure all dependencies are installed correctly
- Verify ClamAV is working: `clamscan --version`

## Security Notes

- AutoAV is **read-only** by design
- No files are modified or deleted
- Sudo access is requested only when needed
- All operations are logged for audit purposes
- Network access is limited to OpenAI API calls 