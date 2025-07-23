# AutoAV - AI-Driven Antivirus Suite

An intelligent antivirus system that uses cloud-hosted LLMs to investigate and identify malicious files on macOS systems through natural language problem descriptions.

## Overview

AutoAV acts as a bridge between a cloud LLM and your local filesystem, allowing the AI to investigate security issues by reading files and analyzing their contents. The system is designed to help users who can describe a problem (like suspicious pop-ups or search marquis) but don't know how to investigate it technically.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User (CLI)    │    │   Local AutoAV   │    │  Cloud LLM      │
│                 │◄──►│   Application    │◄──►│  (OpenAI)       │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Filesystem     │
                       │   (Read-only)    │
                       └──────────────────┘
```

### Key Components

1. **CLI Interface**: Command-line interface for user interaction
2. **LLM Bridge**: Handles communication with OpenAI models
3. **File Inspector**: Secure file reading and analysis
4. **ClamAV Integration**: Backend virus scanning
5. **Permission Manager**: Handles sudo access requests
6. **Tool Registry**: Available operations for the LLM

## Features

- **Natural Language Problem Description**: Describe issues in plain English
- **Intelligent File Investigation**: AI-driven file system exploration
- **Malware Detection**: Integration with ClamAV for virus scanning
- **Safe Operations**: Read-only file access with no destructive actions
- **Permission Management**: On-demand sudo access requests with password prompt handling
- **Real-Time Transparency**: See every step of the investigation as it happens
- **Comprehensive Logging**: Detailed session logs with timing and audit trail
- **Session Analysis**: View and analyze past investigation sessions
- **Focus Areas**: Pop-up detection and search marquis investigation

## Current Use Cases

1. **Suspicious Pop-ups**: Identify processes and files causing unwanted pop-ups
2. **Search Marquis**: Detect and locate search marquis malware components

## Security Model

- **Read-only Access**: No file creation, modification, or deletion
- **Permission Escalation**: User approval required for sudo access
- **Password Handling**: Proper handling of sudo password prompts
- **Input Validation**: All LLM requests validated before execution
- **Sandboxed Operations**: Limited filesystem access scope

## Development Status

🚧 **In Development** - Initial specification and architecture phase

## Next Steps

1. Set up project structure and dependencies
2. Implement core CLI interface
3. Create LLM communication layer
4. Build file inspection system
5. Integrate ClamAV backend
6. Add permission management
7. Implement tool registry for LLM operations
8. Add comprehensive logging and transparency features
9. Create session analysis tools
10. Test with real security scenarios 