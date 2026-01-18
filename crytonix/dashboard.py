import os
import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from crytonix.tools import SystemToolbox, NetworkToolbox, Toolbox

console = Console()

def get_system_panel():
    sys_info = SystemToolbox.get_system_info()
    resource_usage = SystemToolbox.get_resource_usage()
    return Panel(f"{sys_info}\n\n{resource_usage}", title="System Health", border_style="cyan")

def get_network_panel():
    local_ip = NetworkToolbox.get_local_ip()
    # Public IP might be slow, so we skip or cache it? For now, let's include it but handle timeout/error gracefully in the toolbox
    public_ip = NetworkToolbox.get_public_ip()
    return Panel(f"Local IP: {local_ip}\nPublic IP: {public_ip}", title="Network Status", border_style="blue")

def get_processes_panel():
    processes = SystemToolbox.list_processes(limit=10)
    return Panel(processes, title="Top Processes", border_style="magenta")

def get_project_stats_panel():
    files = Toolbox.list_files(".")
    file_list = files.splitlines() if files else []
    file_count = len(file_list)

    py_files = sum(1 for f in file_list if f.strip().endswith('.py'))
    md_files = sum(1 for f in file_list if f.strip().endswith('.md'))

    return Panel(
        f"Total Files in Root: {file_count}\n"
        f"Python Files: {py_files}\n"
        f"Markdown Files: {md_files}",
        title="Project Stats",
        border_style="green"
    )

def run_dashboard():
    layout = Layout()

    # Split into Top and Bottom
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )

    # Header
    layout["header"].update(Panel(Text("Crytonix Project Health Dashboard", justify="center", style="bold white"), style="on blue"))

    # Body split into left (System) and right (Project)
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )

    # Left column: System Info, Resources, Network
    layout["left"].split_column(
        Layout(get_system_panel(), name="system"),
        Layout(get_network_panel(), name="network")
    )

    # Right column: Processes, Project Stats
    layout["right"].split_column(
        Layout(get_processes_panel(), name="processes"),
        Layout(get_project_stats_panel(), name="stats")
    )

    # Footer
    layout["footer"].update(Panel(Text(f"Generated at {datetime.datetime.now()}", justify="right"), style="dim"))

    console.print(layout)

if __name__ == "__main__":
    run_dashboard()
