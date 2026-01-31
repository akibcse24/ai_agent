import os
import subprocess
import glob
from rich.console import Console
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.panel import Panel

console = Console()

class Toolbox:
    @staticmethod
    def list_files(path: str = ".") -> str:
        """Lists files in the directory."""
        try:
            # Simple list, ignoring hidden files unless specified
            files = glob.glob(os.path.join(path, "*"))
            return "\n".join([os.path.basename(f) for f in files])
        except Exception as e:
            return f"Error listing files: {e}"

    @staticmethod
    def read_file(path: str) -> str:
        """Reads the content of a file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    @staticmethod
    def write_file(path: str, content: str) -> str:
        """Writes content to a file. Creates directories if needed."""
        try:
            # Safety Check: Confirm overwrite if file exists
            if os.path.exists(path):
                old_content = Toolbox.read_file(path)
                Toolbox._show_diff(new_content=content, old_content=old_content, filename=path)
                # In GUI/Agent mode, we might assume approval or handle this differently.
                # For now, we keep the prompt behavior but it might block automation.
                if not Confirm.ask(f"[yellow]Overwrite {path}?[/yellow]", default=True):
                     return f"Action cancelled by user: Write to {path}"

            directory = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {e}"

    @staticmethod
    def replace_in_file(path: str, old_string: str, new_string: str) -> str:
        """Replaces a string in a file with a new one."""
        try:
            content = Toolbox.read_file(path)
            if old_string not in content:
                return f"Error: String '{old_string}' not found in {path}"

            new_content = content.replace(old_string, new_string)

            Toolbox._show_diff(new_content=new_content, old_content=content, filename=path)

            if not Confirm.ask(f"[yellow]Apply replacement in {path}?[/yellow]", default=True):
                 return f"Action cancelled by user: Replace in {path}"

            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return f"Successfully replaced occurrences in {path}"
        except Exception as e:
            return f"Error replacing in file: {e}"

    @staticmethod
    def search_code(pattern: str, path: str = ".") -> str:
        """Searches for a regex pattern in files."""
        import re
        results = []
        try:
            for root, _, files in os.walk(path):
                if ".git" in root or "__pycache__" in root:
                    continue
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8", errors='ignore') as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines):
                                if re.search(pattern, line):
                                    results.append(f"{file_path}:{i+1}: {line.strip()}")
                    except:
                        pass

            if not results:
                return "No matches found."
            return "\n".join(results[:50])
        except Exception as e:
            return f"Error searching code: {e}"

    @staticmethod
    def create_directory(path: str) -> str:
        try:
            os.makedirs(path, exist_ok=True)
            return f"Directory created: {path}"
        except Exception as e:
            return f"Error creating directory: {e}"

    @staticmethod
    def run_command(command: str) -> str:
        """Runs a shell command."""
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Command failed: {e.stderr}"

    @staticmethod
    def _show_diff(new_content: str, old_content: str, filename: str):
        import difflib
        diff = list(difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}"
        ))

        diff_text = "".join(diff)
        if not diff_text:
            console.print(f"[dim]No changes detected for {filename}[/dim]")
            return

        syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title=f"Preview: {filename}", border_style="yellow"))
