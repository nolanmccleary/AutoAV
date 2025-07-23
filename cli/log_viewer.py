"""
Session Log Viewer for AutoAV
Provides utilities to view and analyze investigation session logs
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint

console = Console()


class SessionLogViewer:
    """Viewer for AutoAV session logs"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions"""
        sessions = []
        
        for log_file in self.logs_dir.glob("session_*.log"):
            session_id = log_file.stem.replace("session_", "")
            sessions.append({
                "session_id": session_id,
                "log_file": log_file,
                "size": log_file.stat().st_size,
                "modified": datetime.fromtimestamp(log_file.stat().st_mtime)
            })
        
        # Sort by modification time (newest first)
        sessions.sort(key=lambda x: x["modified"], reverse=True)
        return sessions
    
    def display_sessions_list(self):
        """Display a table of all sessions"""
        sessions = self.list_sessions()
        
        if not sessions:
            console.print("[yellow]No session logs found.[/yellow]")
            return
        
        table = Table(title="📋 Available Sessions")
        table.add_column("Session ID", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Time", style="blue")
        table.add_column("Size", style="magenta")
        
        for session in sessions:
            table.add_row(
                session["session_id"],
                session["modified"].strftime("%Y-%m-%d"),
                session["modified"].strftime("%H:%M:%S"),
                f"{session['size']} bytes"
            )
        
        console.print(table)
    
    def load_session_log(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a session log file"""
        log_file = self.logs_dir / f"session_{session_id}.log"
        
        if not log_file.exists():
            console.print(f"[red]Session log not found: {session_id}[/red]")
            return None
        
        try:
            with open(log_file, 'r') as f:
                content = f.read()
            
            # Parse log content (this is a simplified parser)
            # In a real implementation, you'd want a more robust log parser
            return self._parse_log_content(content, session_id)
            
        except Exception as e:
            console.print(f"[red]Error loading session log: {e}[/red]")
            return None
    
    def _parse_log_content(self, content: str, session_id: str) -> Dict[str, Any]:
        """Parse log content into structured data"""
        lines = content.split('\n')
        
        session_data = {
            "session_id": session_id,
            "events": [],
            "tool_calls": [],
            "errors": [],
            "summary": {}
        }
        
        for line in lines:
            if not line.strip():
                continue
            
            # Parse timestamp and message
            try:
                # Expected format: 2024-12-01 14:30:22,123 - autoav_session_20241201_143022 - INFO - message
                parts = line.split(' - ', 3)
                if len(parts) >= 4:
                    timestamp_str = parts[0]
                    level = parts[2]
                    message = parts[3]
                    
                    event = {
                        "timestamp": timestamp_str,
                        "level": level,
                        "message": message
                    }
                    
                    session_data["events"].append(event)
                    
                    # Categorize events
                    if "Executing tool:" in message:
                        session_data["tool_calls"].append(event)
                    elif level == "ERROR":
                        session_data["errors"].append(event)
                    elif "Session" in message and "started" in message:
                        session_data["summary"]["start_time"] = timestamp_str
                    elif "Investigation completed" in message:
                        session_data["summary"]["end_time"] = timestamp_str
                        
            except Exception:
                # Skip malformed lines
                continue
        
        return session_data
    
    def display_session_summary(self, session_id: str):
        """Display a summary of a specific session"""
        session_data = self.load_session_log(session_id)
        
        if not session_data:
            return
        
        # Create summary panel
        summary_panel = Panel(
            f"[bold]Session Summary[/bold]\n\n"
            f"[cyan]Session ID:[/cyan] {session_id}\n"
            f"[cyan]Total Events:[/cyan] {len(session_data['events'])}\n"
            f"[cyan]Tool Calls:[/cyan] {len(session_data['tool_calls'])}\n"
            f"[cyan]Errors:[/cyan] {len(session_data['errors'])}\n"
            f"[cyan]Start Time:[/cyan] {session_data['summary'].get('start_time', 'N/A')}\n"
            f"[cyan]End Time:[/cyan] {session_data['summary'].get('end_time', 'N/A')}",
            title="📊 Session Overview",
            border_style="blue"
        )
        
        console.print(summary_panel)
        
        # Display tool calls timeline
        if session_data["tool_calls"]:
            self._display_tool_timeline(session_data["tool_calls"])
        
        # Display errors if any
        if session_data["errors"]:
            self._display_errors(session_data["errors"])
    
    def _display_tool_timeline(self, tool_calls: List[Dict[str, Any]]):
        """Display a timeline of tool calls"""
        table = Table(title="🔧 Tool Execution Timeline")
        table.add_column("Time", style="blue")
        table.add_column("Tool", style="cyan")
        table.add_column("Arguments", style="yellow")
        table.add_column("Status", style="green")
        
        for i, call in enumerate(tool_calls, 1):
            message = call["message"]
            
            # Extract tool name and arguments
            if "Executing tool:" in message:
                tool_info = message.split("Executing tool: ")[1]
                if " with args:" in tool_info:
                    tool_name, args_str = tool_info.split(" with args: ", 1)
                else:
                    tool_name = tool_info
                    args_str = "N/A"
                
                # Find corresponding completion message
                completion_status = "Unknown"
                for event in tool_calls:
                    if f"Tool {tool_name} completed" in event["message"]:
                        if "success: True" in event["message"]:
                            completion_status = "✅ Success"
                        else:
                            completion_status = "❌ Failed"
                        break
                
                table.add_row(
                    call["timestamp"],
                    tool_name,
                    args_str[:50] + "..." if len(args_str) > 50 else args_str,
                    completion_status
                )
        
        console.print(table)
    
    def _display_errors(self, errors: List[Dict[str, Any]]):
        """Display errors from the session"""
        if not errors:
            return
        
        error_panel = Panel(
            "\n".join([f"[red]{error['timestamp']}: {error['message']}[/red]" for error in errors]),
            title="❌ Errors",
            border_style="red"
        )
        
        console.print(error_panel)
    
    def export_session(self, session_id: str, format: str = "json", output_file: str = None):
        """Export session data in specified format"""
        session_data = self.load_session_log(session_id)
        
        if not session_data:
            return
        
        if format == "json":
            content = json.dumps(session_data, indent=2, default=str)
        elif format == "yaml":
            content = yaml.dump(session_data, default_flow_style=False, allow_unicode=True)
        else:
            console.print(f"[red]Unsupported format: {format}[/red]")
            return
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
            console.print(f"[green]Session exported to: {output_file}[/green]")
        else:
            console.print(content)
    
    def search_sessions(self, query: str):
        """Search through session logs for specific terms"""
        sessions = self.list_sessions()
        results = []
        
        for session in sessions:
            session_data = self.load_session_log(session["session_id"])
            if not session_data:
                continue
            
            # Search in messages
            matching_events = []
            for event in session_data["events"]:
                if query.lower() in event["message"].lower():
                    matching_events.append(event)
            
            if matching_events:
                results.append({
                    "session_id": session["session_id"],
                    "matches": len(matching_events),
                    "events": matching_events
                })
        
        # Display search results
        if results:
            console.print(f"[green]Found {len(results)} sessions matching '{query}':[/green]\n")
            
            for result in results:
                console.print(f"[cyan]Session {result['session_id']}[/cyan] - {result['matches']} matches")
                for event in result["events"][:3]:  # Show first 3 matches
                    console.print(f"  {event['timestamp']}: {event['message']}")
                console.print()
        else:
            console.print(f"[yellow]No sessions found matching '{query}'[/yellow]")


def main():
    """CLI interface for log viewer"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AutoAV Session Log Viewer")
    parser.add_argument("command", choices=["list", "view", "export", "search"], help="Command to execute")
    parser.add_argument("--session-id", help="Session ID for view/export commands")
    parser.add_argument("--format", choices=["json", "yaml"], default="json", help="Export format")
    parser.add_argument("--output", help="Output file for export")
    parser.add_argument("--query", help="Search query")
    
    args = parser.parse_args()
    
    viewer = SessionLogViewer()
    
    if args.command == "list":
        viewer.display_sessions_list()
    
    elif args.command == "view":
        if not args.session_id:
            console.print("[red]Session ID required for view command[/red]")
            return
        viewer.display_session_summary(args.session_id)
    
    elif args.command == "export":
        if not args.session_id:
            console.print("[red]Session ID required for export command[/red]")
            return
        viewer.export_session(args.session_id, args.format, args.output)
    
    elif args.command == "search":
        if not args.query:
            console.print("[red]Query required for search command[/red]")
            return
        viewer.search_sessions(args.query)


if __name__ == "__main__":
    main() 