# AutoAV - Minimal AI-Driven Antivirus

A simple AI-powered security investigation tool for macOS.

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set your OpenAI API key:**
```bash
export OPENAI_API_KEY=your_api_key_here
```

3. **Run:**
```bash
python main.py
```

4. **Describe your problem:**
```
Problem: I'm getting suspicious pop-ups
```

## What it does

- Lists running processes
- Reads files safely
- Scans files with ClamAV
- Finds files by pattern
- Lists directory contents
- Checks browser extensions
- Checks startup items
- Shows network connections

## Requirements

- macOS
- Python 3.8+
- OpenAI API key
- ClamAV (optional, for virus scanning) 