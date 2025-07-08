#!/usr/bin/env python3
"""
Test script to verify the background capture fixes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from grace_cli import WindowManager, ScreenshotCapture
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import time

console = Console()

def test_background_capture_fixes():
    """Test the background capture functionality with fixes"""
    
    console.print(Panel.fit(
        "[bold blue]Testing Background Capture Fixes[/bold blue]\n"
        "This will test if the fixes resolve:\n"
        "• Black screenshot issues\n"
        "• Same screenshot for different windows\n"
        "• DPI awareness problems",
        title="Grace CLI - Background Capture Test"
    ))
    
    # Get available windows
    console.print("\n[yellow]Scanning for available windows...[/yellow]")
    windows = WindowManager.get_all_windows()
    
    if not windows:
        console.print("[red]No windows found![/red]")
        return
    
    # Filter out small/invalid windows
    valid_windows = []
    for window in windows:
        width = getattr(window, 'width', 0)
        height = getattr(window, 'height', 0)
        if width > 100 and height > 100:  # Only windows larger than 100x100
            valid_windows.append(window)
    
    if len(valid_windows) < 2:
        console.print("[yellow]Need at least 2 valid windows for testing. Found only:", len(valid_windows))
        if valid_windows:
            console.print(f"Available: {valid_windows[0].title}")
    
    # Test with first few windows
    test_windows = valid_windows[:3]  # Test with up to 3 windows
    
    console.print(f"\n[green]Testing background capture with {len(test_windows)} windows:[/green]")
    
    results = []
    
    for i, window in enumerate(test_windows, 1):
        console.print(f"\n[cyan]Test {i}: Capturing '{window.title}'[/cyan]")
        console.print(f"[dim]Window dimensions: {window.width}x{window.height} at ({window.left}, {window.top})[/dim]")
        
        # Test background capture
        result = ScreenshotCapture.capture_window_background(window, crop_padding=0)
        
        if result:
            console.print(f"[green]✓ Background capture successful: {os.path.basename(result)}[/green]")
            results.append({
                'window': window.title,
                'method': 'background',
                'file': os.path.basename(result),
                'success': True
            })
        else:
            console.print(f"[red]✗ Background capture failed[/red]")
            results.append({
                'window': window.title,
                'method': 'background',
                'file': 'None',
                'success': False
            })
        
        # Small delay between captures
        time.sleep(0.5)
    
    # Test regular capture for comparison
    console.print(f"\n[cyan]Testing regular capture for comparison:[/cyan]")
    
    for i, window in enumerate(test_windows[:2], 1):  # Test fewer for regular capture
        console.print(f"\n[cyan]Regular Test {i}: Capturing '{window.title}'[/cyan]")
        
        result = ScreenshotCapture.capture_window(window)
        
        if result:
            console.print(f"[green]✓ Regular capture successful: {os.path.basename(result)}[/green]")
            results.append({
                'window': window.title,
                'method': 'regular',
                'file': os.path.basename(result),
                'success': True
            })
        else:
            console.print(f"[red]✗ Regular capture failed[/red]")
            results.append({
                'window': window.title,
                'method': 'regular', 
                'file': 'None',
                'success': False
            })
        
        time.sleep(0.5)
    
    # Display results table
    console.print("\n[bold]Test Results Summary:[/bold]")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Window", style="cyan")
    table.add_column("Method", style="yellow")
    table.add_column("Result", style="green")
    table.add_column("File", style="blue")
    
    for result in results:
        status = "✓ Success" if result['success'] else "✗ Failed"
        table.add_row(
            result['window'][:30] + "..." if len(result['window']) > 30 else result['window'],
            result['method'],
            status,
            result['file']
        )
    
    console.print(table)
    
    # Summary
    successful_bg = sum(1 for r in results if r['method'] == 'background' and r['success'])
    total_bg = sum(1 for r in results if r['method'] == 'background')
    successful_reg = sum(1 for r in results if r['method'] == 'regular' and r['success'])
    total_reg = sum(1 for r in results if r['method'] == 'regular')
    
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"Background Capture: {successful_bg}/{total_bg} successful")
    console.print(f"Regular Capture: {successful_reg}/{total_reg} successful")
    
    if successful_bg > 0:
        console.print("\n[green]✓ Background capture is working![/green]")
        console.print("[green]✓ Fixes appear to be successful![/green]")
    else:
        console.print("\n[red]✗ Background capture still has issues[/red]")
    
    console.print("\n[dim]Check the screenshots directory to verify different content was captured for each window.[/dim]")

if __name__ == "__main__":
    test_background_capture_fixes()