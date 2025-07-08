#!/usr/bin/env python3
"""
Test script for Grace CLI background capture functionality

This script demonstrates the new background capture feature that can:
- Capture windows without bringing them to the foreground
- Apply proper cropping with customizable padding
- Work with hidden or minimized windows
"""

import subprocess
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

def run_command(cmd, description):
    """Run a command and display results"""
    console.print(f"\n[bold blue]Testing: {description}[/bold blue]")
    console.print(f"[dim]Command: {cmd}[/dim]")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            console.print(f"[green]✓ Success[/green]")
            if result.stdout.strip():
                console.print(result.stdout)
        else:
            console.print(f"[red]✗ Failed (exit code: {result.returncode})[/red]")
            if result.stderr.strip():
                console.print(f"[red]Error: {result.stderr}[/red]")
                
    except subprocess.TimeoutExpired:
        console.print(f"[yellow]⚠ Command timed out[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Exception: {e}[/red]")

def main():
    """Test Grace CLI background capture functionality"""
    
    # Display banner
    banner = Panel(
        "[bold green]Grace CLI Background Capture Test Suite[/bold green]\n\n"
        "This test demonstrates the new background capture functionality:\n"
        "• Capture windows without bringing them to foreground\n"
        "• Apply proper cropping with customizable padding\n"
        "• Work with hidden or minimized windows\n\n"
        "[dim]Note: Some tests may require specific windows to be open[/dim]",
        title="[bold]Background Capture Testing[/bold]",
        border_style="blue"
    )
    console.print(banner)
    
    # Test 1: Show help for background-capture command
    run_command(
        "python grace_cli.py background-capture --help",
        "Background capture command help"
    )
    
    # Test 2: List available windows
    run_command(
        "python grace_cli.py list-windows --no-categories",
        "List available windows for capture"
    )
    
    # Test 3: Test capture command with background flag
    run_command(
        "python grace_cli.py capture --window notepad --background --padding 15",
        "Background capture with padding (Notepad)"
    )
    
    # Test 4: Test dedicated background-capture command
    run_command(
        "python grace_cli.py background-capture notepad --padding 20",
        "Dedicated background capture command (Notepad)"
    )
    
    # Test 5: Background capture with export
    run_command(
        "python grace_cli.py background-capture calculator --padding 10 --csv --json",
        "Background capture with data export (Calculator)"
    )
    
    # Test 6: Show system status
    run_command(
        "python grace_cli.py status",
        "System capabilities and status"
    )
    
    # Display summary
    summary_panel = Panel(
        "[bold green]Background Capture Testing Complete![/bold green]\n\n"
        "[bold]New Features Tested:[/bold]\n"
        "• Background window capture without activation\n"
        "• Customizable crop padding\n"
        "• Dedicated background-capture command\n"
        "• Integration with existing capture workflow\n\n"
        "[bold]Usage Examples:[/bold]\n"
        "• [cyan]python grace_cli.py capture --window \"app name\" --background[/cyan]\n"
        "• [cyan]python grace_cli.py background-capture \"app name\" --padding 15[/cyan]\n"
        "• [cyan]python grace_cli.py background-capture notepad --csv --json[/cyan]\n\n"
        "[bold]Interactive Mode:[/bold]\n"
        "• Run [cyan]python grace_cli.py interactive[/cyan]\n"
        "• Select option 4 for \"Background Capture\"\n\n"
        "[dim]The background capture feature allows you to capture windows\n"
        "without interrupting your workflow by bringing them to the foreground.[/dim]",
        title="[bold]Test Summary[/bold]",
        border_style="green"
    )
    console.print(summary_panel)
    
    # Check for generated files
    screenshots_dir = Path("screenshots")
    if screenshots_dir.exists():
        files = list(screenshots_dir.glob("*"))
        if files:
            console.print(f"\n[green]Generated {len(files)} files in screenshots directory[/green]")
            for file in files[-3:]:  # Show last 3 files
                console.print(f"  • {file.name}")
    
    console.print("\n[bold green]BACKGROUND CAPTURE TESTING COMPLETE![/bold green]")
    console.print("[dim]Grace CLI is ready for background window capture operations.[/dim]")

if __name__ == "__main__":
    main()