# AutoAV Technical Specification

## System Architecture

### Core Components

#### 1. CLI Interface (`cli/`)
- **Entry Point**: `main.py` - Main application entry
- **Command Parser**: Handles user input and natural language descriptions
- **Session Manager**: Manages conversation state with LLM
- **Output Formatter**: Formats LLM responses for terminal display

#### 2. LLM Bridge (`llm/`)
- **OpenAI Client**: Handles API communication with OpenAI models
- **Tool Registry**: Defines available filesystem operations
- **Conversation Manager**: Maintains context and conversation history
- **Response Parser**: Parses LLM responses and extracts tool calls

#### 3. File Inspector (`inspector/`)
- **File Reader**: Secure file reading with validation
- **Content Analyzer**: Analyzes file contents for suspicious patterns
- **Metadata Extractor**: Extracts file metadata (permissions, timestamps, etc.)
- **Hash Calculator**: Generates file hashes for identification

#### 4. ClamAV Integration (`clamav/`)
- **Scanner**: Interface to ClamAV virus scanning
- **Result Parser**: Parses ClamAV scan results
- **Database Manager**: Manages virus signature database updates

#### 5. Permission Manager (`permissions/`)
- **Access Controller**: Manages filesystem access permissions
- **Sudo Request**: Handles elevated privilege requests
- **Security Validator**: Validates all operations for safety

#### 6. Tools Registry (`tools/`)
- **Tool Definitions**: JSON schema for available operations
- **Tool Executor**: Executes LLM-requested operations
- **Result Formatter**: Formats tool results for LLM consumption

## API Design

### LLM Tool Definitions

```json
{
  "tools": [
    {
      "name": "list_processes",
      "description": "List running processes with details",
      "parameters": {
        "type": "object",
        "properties": {
          "filter": {
            "type": "string",
            "description": "Optional filter for process names"
          }
        }
      }
    },
    {
      "name": "read_file",
      "description": "Read file contents safely",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "File path to read"
          },
          "max_size": {
            "type": "integer",
            "description": "Maximum file size to read in bytes"
          }
        },
        "required": ["path"]
      }
    },
    {
      "name": "scan_file",
      "description": "Scan file with ClamAV",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "File path to scan"
          }
        },
        "required": ["path"]
      }
    },
    {
      "name": "find_files",
      "description": "Find files matching criteria",
      "parameters": {
        "type": "object",
        "properties": {
          "pattern": {
            "type": "string",
            "description": "File pattern to search for"
          },
          "directory": {
            "type": "string",
            "description": "Directory to search in"
          }
        },
        "required": ["pattern"]
      }
    },
    {
      "name": "get_file_info",
      "description": "Get detailed file information",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "File path"
          }
        },
        "required": ["path"]
      }
    }
  ]
}
```

### Security Constraints

1. **File Access Limits**:
   - Maximum file size: 10MB for text files
   - Binary files: metadata only + ClamAV scan
   - Restricted directories: `/System`, `/Library` (read-only)
   - User approval required for system directories

2. **Operation Validation**:
   - All paths must be absolute and validated
   - No write operations allowed
   - No execution of files
   - No network access except to OpenAI API

3. **Permission Escalation**:
   - Sudo access requested only when needed
   - User must approve each sudo request
   - Temporary sudo access with timeout

## Implementation Details

### File Reading Strategy

```python
class FileReader:
    def read_file(self, path: str, max_size: int = 10_485_760) -> FileContent:
        # Validate path
        # Check file size
        # Determine file type
        # Read content based on type
        # Return structured data
```

### LLM Communication Flow

1. **User Input**: Natural language problem description
2. **Context Building**: Add relevant system information
3. **LLM Request**: Send to OpenAI with available tools
4. **Tool Execution**: Execute requested operations locally
5. **Result Processing**: Format results for LLM
6. **Iteration**: Continue until investigation complete

### Error Handling

- **File Not Found**: Graceful error with suggestions
- **Permission Denied**: Request elevated access
- **Network Issues**: Retry with exponential backoff
- **LLM Errors**: Fallback responses and logging

## Use Case Implementations

### Pop-up Investigation

1. **Process Enumeration**: List all running processes
2. **Window Analysis**: Identify processes with windows
3. **File Association**: Find files associated with suspicious processes
4. **Content Analysis**: Analyze process files for malicious patterns
5. **ClamAV Scanning**: Scan identified files

### Search Marquis Detection

1. **Browser Analysis**: Check browser extensions and settings
2. **DNS Investigation**: Look for DNS hijacking
3. **Startup Items**: Check launch agents and startup items
4. **Network Connections**: Identify suspicious network activity
5. **File Scanning**: Scan identified components

## Configuration

### Environment Variables

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo
CLAMAV_DATABASE_PATH=/usr/local/share/clamav
MAX_FILE_SIZE=10485760
LOG_LEVEL=INFO
```

### Configuration File

```yaml
# config.yaml
llm:
  model: gpt-4
  temperature: 0.1
  max_tokens: 4000

security:
  max_file_size: 10485760
  allowed_directories:
    - /Users
    - /Applications
  restricted_directories:
    - /System
    - /Library

clamav:
  database_path: /usr/local/share/clamav
  scan_timeout: 30
```

## Testing Strategy

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: LLM communication testing
3. **Security Tests**: Permission and access control testing
4. **End-to-End Tests**: Complete workflow testing
5. **Mock Tests**: ClamAV and filesystem mocking

## Deployment

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install ClamAV
brew install clamav

# Update virus database
freshclam

# Run application
python main.py
```

### Development Setup

```bash
# Clone repository
git clone <repository>

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8
``` 