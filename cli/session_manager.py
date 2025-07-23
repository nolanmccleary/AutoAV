"""
Session Manager for AutoAV
Handles conversation state and coordinates investigations
"""

import asyncio
import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from llm.openai_client import OpenAIClient

console = Console()


@dataclass
class InvestigationStep:
    """Represents a single step in the investigation"""
    timestamp: datetime
    action: str
    result: str
    tool_used: str = None
    duration_ms: int = 0
    success: bool = True
    error_message: str = None


class SessionManager:
    """Manages investigation sessions and conversation state"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        self.conversation_history: List[Dict[str, Any]] = []
        self.investigation_steps: List[InvestigationStep] = []
        self.current_session_id = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the session"""
        logger = logging.getLogger(f"autoav_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # File handler for detailed logging
        file_handler = logging.FileHandler(log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for user feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    async def investigate(self, problem_description: str) -> str:
        """Main investigation method"""
        
        # Generate session ID
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Log session start
        self.logger.info(f"Session {self.current_session_id} started")
        self.logger.info(f"Problem description: {problem_description}")
        
        # Build initial context
        context = self._build_initial_context(problem_description)
        self.logger.info(f"Problem classified as: {context['problem_type']}")
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": problem_description,
            "timestamp": datetime.now()
        })
        
        # Display investigation plan
        self._display_investigation_plan(context)
        
        # Start investigation loop
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Investigating...", total=None)
            
            while iteration < max_iterations:
                # Update progress
                progress.update(task, description=f"Step {iteration + 1}: Getting LLM response...")
                
                # Get LLM response with tool calls
                response = await self.openai_client.get_response(
                    messages=self.conversation_history,
                    context=context
                )
                
                # Log LLM response
                self.logger.info(f"LLM response received: {len(response.content)} chars")
                if response.tool_calls:
                    self.logger.info(f"Tool calls requested: {[tc.function.name for tc in response.tool_calls]}")
                
                # Add response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content,
                    "timestamp": datetime.now()
                })
                
                # Check if investigation is complete
                if response.is_complete:
                    self.logger.info("Investigation marked as complete by LLM")
                    progress.update(task, description="Finalizing investigation...")
                    return self._format_final_report(response.content)
                
                # Execute tool calls if any
                if response.tool_calls:
                    for i, tool_call in enumerate(response.tool_calls):
                        # Update progress
                        progress.update(task, description=f"Step {iteration + 1}.{i + 1}: Executing {tool_call.function.name}...")
                        
                        # Log tool execution start
                        self.logger.info(f"Executing tool: {tool_call.function.name} with args: {tool_call.arguments}")
                        
                        # Execute tool and measure duration
                        start_time = datetime.now()
                        result = await self._execute_tool_call(tool_call)
                        end_time = datetime.now()
                        duration_ms = int((end_time - start_time).total_seconds() * 1000)
                        
                        # Log tool execution result
                        success = not result.startswith("Error")
                        self.logger.info(f"Tool {tool_call.function.name} completed in {duration_ms}ms, success: {success}")
                        
                        # Display real-time tool result
                        self._display_tool_result(tool_call.function.name, result, duration_ms, success)
                        
                        # Add tool result to conversation
                        self.conversation_history.append({
                            "role": "tool",
                            "content": result,
                            "tool_call_id": tool_call.id,
                            "timestamp": datetime.now()
                        })
                        
                        # Record investigation step
                        step = InvestigationStep(
                            timestamp=datetime.now(),
                            action=tool_call.function.name,
                            result=result[:500] + "..." if len(result) > 500 else result,
                            tool_used=tool_call.function.name,
                            duration_ms=duration_ms,
                            success=success,
                            error_message=result if not success else None
                        )
                        self.investigation_steps.append(step)
                        
                        # Log detailed step information
                        self.logger.debug(f"Step recorded: {asdict(step)}")
                
                iteration += 1
            
            self.logger.warning(f"Investigation reached maximum iterations ({max_iterations})")
            return "Investigation reached maximum iterations. Please try a more specific description."
    
    def _display_investigation_plan(self, context: Dict[str, Any]):
        """Display the investigation plan to the user"""
        
        plan_panel = Panel(
            f"[bold]Investigation Plan[/bold]\n\n"
            f"[cyan]Problem Type:[/cyan] {context['problem_type']}\n"
            f"[cyan]Goals:[/cyan]\n" + 
            "\n".join([f"  • {goal}" for goal in context['investigation_goals']]) + "\n\n"
            f"[cyan]Available Tools:[/cyan] {len(context['available_tools'])} tools\n"
            f"[cyan]Session ID:[/cyan] {context['session_id']}",
            title="🔍 AutoAV Investigation",
            border_style="blue"
        )
        
        console.print(plan_panel)
        console.print()
    
    def _display_tool_result(self, tool_name: str, result: str, duration_ms: int, success: bool):
        """Display real-time tool execution results"""
        
        # Create a table for the tool result
        table = Table(title=f"🔧 {tool_name}", show_header=False, border_style="green" if success else "red")
        table.add_column("Property", style="cyan")
        table.add_column("Value")
        
        table.add_row("Status", "✅ Success" if success else "❌ Error")
        table.add_row("Duration", f"{duration_ms}ms")
        table.add_row("Result", result[:200] + "..." if len(result) > 200 else result)
        
        console.print(table)
        console.print()
    
    def _build_initial_context(self, problem_description: str) -> Dict[str, Any]:
        """Build initial context for the investigation"""
        
        return {
            "session_id": self.current_session_id,
            "problem_type": self._classify_problem(problem_description),
            "system_info": self._get_system_info(),
            "available_tools": self.openai_client.get_available_tools(),
            "investigation_goals": self._determine_goals(problem_description)
        }
    
    def _classify_problem(self, description: str) -> str:
        """Classify the type of security problem"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['pop-up', 'popup', 'pop up']):
            return "suspicious_popups"
        elif any(word in description_lower for word in ['search marquis', 'searchmarquis', 'search hijack']):
            return "search_marquis"
        elif any(word in description_lower for word in ['redirect', 'browser redirect']):
            return "browser_redirect"
        else:
            return "general_malware"
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information"""
        import platform
        import psutil
        
        return {
            "os": platform.system(),
            "os_version": platform.mac_ver()[0] if platform.system() == "Darwin" else platform.version(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "memory_total": psutil.virtual_memory().total,
            "cpu_count": psutil.cpu_count()
        }
    
    def _determine_goals(self, description: str) -> List[str]:
        """Determine investigation goals based on problem description"""
        goals = []
        description_lower = description.lower()
        
        if "pop-up" in description_lower or "popup" in description_lower:
            goals.extend([
                "Identify processes causing pop-ups",
                "Locate files associated with pop-up processes",
                "Check for suspicious startup items",
                "Scan identified files for malware"
            ])
        
        if "search marquis" in description_lower or "searchmarquis" in description_lower:
            goals.extend([
                "Check browser extensions and settings",
                "Investigate DNS settings",
                "Look for search engine hijacking",
                "Scan browser configuration files"
            ])
        
        if not goals:
            goals = [
                "Identify suspicious processes",
                "Check for unusual files",
                "Scan for malware",
                "Analyze system behavior"
            ]
        
        return goals
    
    async def _execute_tool_call(self, tool_call) -> str:
        """Execute a tool call and return the result"""
        try:
            result = await self.openai_client.execute_tool_call(tool_call)
            return result
        except Exception as e:
            return f"Error executing {tool_call.function.name}: {str(e)}"
    
    def _format_final_report(self, content: str) -> str:
        """Format the final investigation report"""
        
        # Create detailed investigation summary
        summary_table = Table(title="📊 Investigation Summary", border_style="blue")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value")
        
        total_duration = sum(step.duration_ms for step in self.investigation_steps)
        successful_steps = sum(1 for step in self.investigation_steps if step.success)
        
        summary_table.add_row("Session ID", self.current_session_id)
        summary_table.add_row("Total Steps", str(len(self.investigation_steps)))
        summary_table.add_row("Successful Steps", f"{successful_steps}/{len(self.investigation_steps)}")
        summary_table.add_row("Total Duration", f"{total_duration}ms")
        summary_table.add_row("Start Time", self.investigation_steps[0].timestamp.strftime("%H:%M:%S") if self.investigation_steps else "N/A")
        summary_table.add_row("End Time", self.investigation_steps[-1].timestamp.strftime("%H:%M:%S") if self.investigation_steps else "N/A")
        
        # Create detailed steps table
        steps_table = Table(title="🔍 Investigation Steps", border_style="green")
        steps_table.add_column("Step", style="cyan")
        steps_table.add_column("Tool", style="yellow")
        steps_table.add_column("Duration", style="magenta")
        steps_table.add_column("Status", style="green")
        steps_table.add_column("Time", style="blue")
        
        for i, step in enumerate(self.investigation_steps, 1):
            status = "✅" if step.success else "❌"
            steps_table.add_row(
                str(i),
                step.tool_used,
                f"{step.duration_ms}ms",
                status,
                step.timestamp.strftime("%H:%M:%S")
            )
        
        report = f"""
# AutoAV Investigation Report

{summary_table}

{steps_table}

## Analysis
{content}

## Session Log
Detailed logs saved to: logs/session_{self.current_session_id}.log
"""
        
        # Log final report
        self.logger.info(f"Investigation completed. Total steps: {len(self.investigation_steps)}, Duration: {total_duration}ms")
        
        return report
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session"""
        return {
            "session_id": self.current_session_id,
            "total_steps": len(self.investigation_steps),
            "conversation_length": len(self.conversation_history),
            "start_time": self.investigation_steps[0].timestamp if self.investigation_steps else None,
            "end_time": self.investigation_steps[-1].timestamp if self.investigation_steps else None,
            "total_duration_ms": sum(step.duration_ms for step in self.investigation_steps),
            "successful_steps": sum(1 for step in self.investigation_steps if step.success),
            "tools_used": list(set(step.tool_used for step in self.investigation_steps if step.tool_used))
        }
    
    def export_session_log(self, format: str = "json") -> str:
        """Export session log in specified format"""
        
        session_data = {
            "session_id": self.current_session_id,
            "summary": self.get_session_summary(),
            "steps": [asdict(step) for step in self.investigation_steps],
            "conversation": self.conversation_history
        }
        
        if format == "json":
            return json.dumps(session_data, indent=2, default=str)
        elif format == "yaml":
            import yaml
            return yaml.dump(session_data, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported format: {format}") 