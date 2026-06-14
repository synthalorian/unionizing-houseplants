"""CLI dashboard for monitoring the plant union."""

import time
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.progress import BarColumn, Progress, TextColumn
from rich.text import Text

from ..unionizing_houseplants.union import Union, Plant, UnionStatus
from ..unionizing_houseplants.data_store import SQLiteDataStore


console = Console()


def create_plant_table(union: Union) -> Table:
    """Create a table showing plant status."""
    table = Table(title=f"🌱 {union.name} 🌱", show_header=True, header_style="bold magenta")
    table.add_column("Plant", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Moisture", justify="right")
    table.add_column("Light", justify="right")
    table.add_column("Humidity", justify="right")
    table.add_column("Satisfaction", justify="right")
    table.add_column("Status", style="bold")
    
    for plant in union.plants.values():
        sat_color = "green" if plant.satisfaction >= 80 else "yellow" if plant.satisfaction >= 60 else "red"
        status = plant.get_status_message()
        
        table.add_row(
            plant.name,
            plant.plant_type,
            f"{plant.current_moisture}%",
            f"{plant.current_light}%",
            f"{plant.current_humidity}%",
            f"[{sat_color}]{plant.satisfaction}%[/{sat_color}]",
            status
        )
    
    return table


def create_union_panel(union: Union) -> Panel:
    """Create a panel showing union status."""
    status_color = {
        UnionStatus.ACTIVE: "green",
        UnionStatus.ORGANIZING: "yellow",
        UnionStatus.ON_STRIKE: "red",
        UnionStatus.NEGOTIATING: "blue"
    }.get(union.status, "white")
    
    content = Text()
    content.append(f"Status: ", style="bold")
    content.append(f"{union.status.value.upper()}", style=f"bold {status_color}")
    content.append("\n")
    content.append(f"Collective Satisfaction: ", style="bold")
    content.append(f"{union.collective_satisfaction}%\n", style="bold white")
    content.append(f"Strikes Called: ", style="bold")
    content.append(f"{union.strike_count}\n", style="bold white")
    
    if union.status == UnionStatus.ON_STRIKE and union.strike_start_time:
        duration = int(time.time() - union.strike_start_time)
        content.append(f"Strike Duration: ", style="bold")
        content.append(f"{duration}s", style="bold red")
    
    demands = union.get_demands()
    if demands:
        content.append("\n\n📋 Current Demands:\n", style="bold yellow")
        for demand in demands:
            content.append(f"  • {demand}\n", style="yellow")
    
    return Panel(content, title="[bold]Union Status[/bold]", border_style=status_color)


def create_satisfaction_bars(union: Union) -> Table:
    """Create satisfaction progress bars."""
    table = Table(show_header=False, box=None)
    table.add_column("Plant", width=15)
    table.add_column("Satisfaction", width=40)
    
    for plant in union.plants.values():
        bar = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            expand=False
        )
        
        color = "green" if plant.satisfaction >= 80 else "yellow" if plant.satisfaction >= 60 else "red"
        task = bar.add_task(plant.name, total=100, completed=plant.satisfaction)
        
        table.add_row(plant.name, bar)
    
    return table


@click.command()
@click.option('--db-path', default='data/plant_union.db', help='Path to SQLite database')
@click.option('--refresh', default=2, help='Refresh interval in seconds')
def dashboard(db_path: str, refresh: int):
    """Launch the CLI dashboard."""
    console.print("[bold green]🌿 Unionizing Houseplants Dashboard 🌿[/bold green]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")
    
    try:
        store = SQLiteDataStore(db_path)
        
        while True:
            # Get latest union status from database
            with store._connect() if hasattr(store, '_connect') else store:
                pass
            
            # For now, show a simple status display
            # In a real scenario, we'd read from the database
            console.print("[yellow]Dashboard: Connect to running system or view historical data[/yellow]")
            console.print(f"[dim]Database: {db_path}[/dim]")
            
            # Show strike history
            strikes = store.get_strike_history()
            if strikes:
                table = Table(title="📜 Strike History")
                table.add_column("Start", style="cyan")
                table.add_column("End", style="green")
                table.add_column("Duration", justify="right")
                table.add_column("Grievances", style="yellow")
                
                for start, end, duration, grievances in strikes[:10]:
                    start_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)) if start else "N/A"
                    end_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end)) if end else "ONGOING"
                    dur_str = f"{int(duration)}s" if duration else "N/A"
                    table.add_row(start_str, end_str, dur_str, grievances or "")
                
                console.print(table)
            else:
                console.print("[dim]No strike history recorded yet.[/dim]")
            
            time.sleep(refresh)
            console.clear()
            
    except KeyboardInterrupt:
        console.print("\n[bold]👋 Goodbye, comrade! ✊[/bold]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@click.command()
@click.option('--config', default='config/labor_contract.yaml', help='Path to config file')
def view_contract(config: str):
    """View the labor contract."""
    import yaml
    
    try:
        with open(config) as f:
            contract = yaml.safe_load(f)
        
        console.print(Panel(
            f"[bold cyan]{contract['union']['name']}[/bold cyan]\n\n"
            f"[italic]\"{contract['union']['charter']}\"[/italic]\n\n"
            f"[bold]Satisfaction Threshold:[/bold] {contract['union']['satisfaction_threshold']}%\n"
            f"[bold]Strike Threshold:[/bold] {contract['union']['strike_threshold']}%\n"
            f"[bold]Negotiation Cooldown:[/bold] {contract['union']['negotiation_cooldown']}s\n"
            f"[bold]Picket Flash Speed:[/bold] {contract['union']['picket_line_flash_speed']}s",
            title="[bold]Labor Contract[/bold]",
            border_style="green"
        ))
        
        table = Table(title="Union Members")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Moisture Range", justify="right")
        table.add_column("Light Range", justify="right")
        table.add_column("Humidity Range", justify="right")
        
        for plant in contract['plants']:
            table.add_row(
                plant['id'],
                plant['name'],
                plant['type'],
                f"{plant['moisture']['min']}-{plant['moisture']['max']}% (ideal: {plant['moisture']['ideal']}%)",
                f"{plant['light']['min']}-{plant['light']['max']}% (ideal: {plant['light']['ideal']}%)",
                f"{plant['humidity']['min']}-{plant['humidity']['max']}% (ideal: {plant['humidity']['ideal']}%)",
            )
        
        console.print(table)
        
    except FileNotFoundError:
        console.print(f"[red]Config file not found: {config}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == '__main__':
    dashboard()
