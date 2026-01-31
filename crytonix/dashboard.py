import os
import time
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.align import Align

from crytonix.tools import Toolbox, CodeAnalysisToolbox, DependencyToolbox

class ProjectDashboard:
    IGNORE_DIRS = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build', 'egg-info'}

    def __init__(self):
        self.console = Console()
        self.root_dir = os.getcwd()
        self.project_name = os.path.basename(self.root_dir)

    def _walk(self):
        """Helper to walk directory with consistent ignore rules."""
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS and not d.endswith('.egg-info')]
            yield root, dirs, files

    def get_project_stats(self):
        """Gather basic project statistics."""
        stats = {
            "files": 0,
            "lines": 0,
            "languages": {}
        }

        for root, _, files in self._walk():
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if not ext: continue

                stats["files"] += 1
                stats["languages"][ext] = stats["languages"].get(ext, 0) + 1

                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        stats["lines"] += sum(1 for _ in f)
                except:
                    pass

        return stats

    def get_git_status(self):
        """Get current git status."""
        if not os.path.exists(os.path.join(self.root_dir, ".git")):
            return {"active": False}

        branch = Toolbox.run_command("git branch --show-current").strip()
        status = Toolbox.run_command("git status --short")
        last_commit = Toolbox.run_command("git log -1 --format='%h - %s (%cr)'").strip()

        return {
            "active": True,
            "branch": branch,
            "changed_files": len(status.splitlines()) if status else 0,
            "last_commit": last_commit
        }

    def scan_tasks(self):
        """Scan for TODOs and FIXMEs."""
        tasks = []
        pattern = r"(TODO|FIXME):"
        import re

        for root, _, files in self._walk():
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.md', '.html', '.css')):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            for i, line in enumerate(f, 1):
                                if match := re.search(pattern, line):
                                    tasks.append({
                                        "type": match.group(1),
                                        "file": file,
                                        "line": i,
                                        "content": line.strip()
                                    })
                    except:
                        pass
        return tasks

    def check_health(self):
        """Perform health checks."""
        # Dependency check
        outdated = DependencyToolbox.check_outdated()
        has_outdated = "Outdated Packages" in outdated

        # Complexity check
        complexity_warnings = []
        radon_installed = True

        for root, _, files in self._walk():
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    report = CodeAnalysisToolbox.analyze_code_complexity(path)

                    if "radon not installed" in report:
                        radon_installed = False
                        break

                    if "Error" not in report:
                        # Simple check for high complexity grades [C] or [F]
                        if "[C]" in report or "[F]" in report:
                            complexity_warnings.append(f"{file} has high complexity")
            if not radon_installed:
                break

        return {
            "outdated_deps": has_outdated,
            "outdated_summary": outdated if has_outdated else "All good",
            "complexity_warnings": complexity_warnings,
            "radon_missing": not radon_installed
        }

    def render(self):
        """Render the dashboard."""

        # 1. Gather Data with Progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task1 = progress.add_task("Analyzing project structure...", total=1)
            stats = self.get_project_stats()
            progress.advance(task1)

            task2 = progress.add_task("Checking Git status...", total=1)
            git_data = self.get_git_status()
            progress.advance(task2)

            task3 = progress.add_task("Scanning for tasks...", total=1)
            tasks = self.scan_tasks()
            progress.advance(task3)

            task4 = progress.add_task("Performing health checks...", total=1)
            health = self.check_health()
            progress.advance(task4)

        # 2. Build Layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        layout["left"].split_column(
            Layout(name="overview"),
            Layout(name="git")
        )
        layout["right"].split_column(
            Layout(name="tasks"),
            Layout(name="health")
        )

        # Header
        header = Panel(
            Align.center(f"[bold cyan]🚀 {self.project_name} Dashboard[/bold cyan] | {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
            style="cyan"
        )
        layout["header"].update(header)

        # Overview Panel
        overview_table = Table(show_header=False, expand=True, box=None)
        overview_table.add_row("📂 Total Files", str(stats["files"]))
        overview_table.add_row("📝 Lines of Code", f"{stats['lines']:,}")

        lang_tree = Tree("Languages")
        sorted_langs = sorted(stats["languages"].items(), key=lambda x: x[1], reverse=True)[:5]
        for ext, count in sorted_langs:
            lang_tree.add(f"{ext}: {count}")

        overview_content = Table.grid(expand=True)
        overview_content.add_row(overview_table)
        overview_content.add_row(Text("\nTop Languages:", style="bold"))
        for ext, count in sorted_langs:
            overview_content.add_row(f"  {ext}: {count}")

        layout["overview"].update(Panel(overview_content, title="Overview", border_style="blue"))

        # Git Status Panel
        if git_data["active"]:
            git_text = Text()
            git_text.append(f"🌿 Branch: {git_data['branch']}\n", style="green")
            git_text.append(f"📦 Uncommitted Changes: {git_data['changed_files']}\n", style="yellow" if git_data['changed_files'] > 0 else "dim")
            git_text.append(f"🕒 Last Commit: {git_data['last_commit']}", style="dim")

            layout["git"].update(Panel(git_text, title="Git Status", border_style="green"))
        else:
            layout["git"].update(Panel("Not a git repository", title="Git Status", border_style="dim"))

        # Tasks Panel
        task_table = Table(show_header=True, header_style="bold magenta", expand=True)
        task_table.add_column("Type", width=6)
        task_table.add_column("Location")
        task_table.add_column("Content")

        for t in tasks[:10]: # Limit to top 10
            task_table.add_row(
                t["type"],
                f"{t['file']}:{t['line']}",
                t["content"].replace(t["type"]+":", "").strip()[:40] + "..."
            )

        if not tasks:
            task_content = Align.center("[italic]No TODOs found! 🎉[/italic]")
        else:
            task_content = task_table

        layout["tasks"].update(Panel(task_content, title=f"Tasks ({len(tasks)})", border_style="magenta"))

        # Health Panel
        health_text = Text()
        if health["outdated_deps"]:
            health_text.append("⚠️ Outdated Dependencies Found\n", style="bold red")
        else:
            health_text.append("✅ Dependencies Up-to-date\n", style="green")

        if health["radon_missing"]:
            health_text.append("ℹ️ Install 'radon' for code complexity analysis.\n", style="dim")
        elif health["complexity_warnings"]:
             health_text.append("\n⚠️ High Complexity Detected:\n", style="bold yellow")
             for warning in health["complexity_warnings"][:5]:
                 health_text.append(f"  - {warning}\n", style="yellow")
             if len(health["complexity_warnings"]) > 5:
                 health_text.append(f"  ...and {len(health['complexity_warnings']) - 5} more\n", style="dim")
        else:
             health_text.append("✅ Code Complexity Looks Good\n", style="green")

        layout["health"].update(Panel(health_text, title="Health Check", border_style="red" if health["outdated_deps"] or health["complexity_warnings"] else "green"))

        self.console.print(layout)

if __name__ == "__main__":
    dashboard = ProjectDashboard()
    dashboard.render()
