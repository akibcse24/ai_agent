import os
import subprocess
import glob
import re
import json
from typing import List, Dict, Any, Optional
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
            
            # Show Diff
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
                        pass # Ignore binary/unreadable files
            
            if not results:
                return "No matches found."
            return "\n".join(results[:50]) # Limit to 50 results
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
        # Expanded allowlist for "Agentic" mode
        allowed_starts = ["ls", "grep", "find", "cat", "echo", "python", "node", "git", "npm", "pip"]
        cmd_start = command.split()[0]
        
        # if cmd_start not in allowed_starts:
        #    if not Confirm.ask(f"[red]Command '{command}' is potentially unsafe. Run anyway?[/red]", default=False):
        #        return "Command cancelled by user."

        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Command failed: {e.stderr}"

    @staticmethod
    def _show_diff(new_content: str, old_content: str, filename: str):
        """Helper to print a colorized diff."""
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

class GitHubToolbox:
    @staticmethod
    def _check_gh_installed() -> bool:
        import shutil
        return shutil.which("gh") is not None

    @staticmethod
    def list_issues(limit: int = 10) -> str:
        """Lists open issues in the current repository."""
        if not GitHubToolbox._check_gh_installed():
            return "Error: GitHub CLI (gh) is not installed."
        
        cmd = f"gh issue list --limit {limit}"
        return Toolbox.run_command(cmd)

    @staticmethod
    def get_issue(issue_number: int) -> str:
        """Gets details of a specific issue."""
        if not GitHubToolbox._check_gh_installed(): return "Error: gh not installed."
        
        # Get title and body
        cmd = f"gh issue view {issue_number} --json title,body,comments"
        return Toolbox.run_command(cmd)

    @staticmethod
    def create_pr(title: str, body: str, branch: str = "") -> str:
        """Creates a Pull Request."""
        if not GitHubToolbox._check_gh_installed(): return "Error: gh not installed."
        
        cmd = f"gh pr create --title \"{title}\" --body \"{body}\""
        if branch:
            cmd += f" --head {branch}"
            
        # Interactive? No, agent is autonomous. We assume changes are pushed.
        # But wait, we need to push first usually. 
        # The agent should use `git_operations` (run_command) to push first.
        
        return Toolbox.run_command(cmd)

    @staticmethod
    def list_prs(limit: int = 5) -> str:
        if not GitHubToolbox._check_gh_installed(): return "Error: gh not installed."
        return Toolbox.run_command(f"gh pr list --limit {limit}")

class WebToolbox:
    @staticmethod
    def search_web(query: str, max_results: int = 5) -> str:
        """Searches the web using DuckDuckGo."""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return "Error: duckduckgo-search not installed. Run `pip install duckduckgo-search`."
        
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(f"Title: {r['title']}\nLink: {r['href']}\nSnippet: {r['body']}\n")
            return "\n---\n".join(results) if results else "No results found."
        except Exception as e:
            return f"Error searching web: {e}"

    @staticmethod
    def read_url(url: str) -> str:
        """Reads and extracts text from a URL."""
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            return "Error: requests or beautifulsoup4 not installed. Run `pip install requests beautifulsoup4`."
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Kill script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.extract()
            
            text = soup.get_text()
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text[:5000] + "\n...[Truncated]" if len(text) > 5000 else text
        except Exception as e:
            return f"Error reading URL: {e}"

class ProductToolbox:
    @staticmethod
    def analyze_sentiment(text: str) -> str:
        """Analyzes sentiment of text."""
        try:
            from textblob import TextBlob
            blob = TextBlob(text)
            return f"Polarity: {blob.sentiment.polarity:.2f} ((-1=Neg, 1=Pos))\nSubjectivity: {blob.sentiment.subjectivity:.2f} ((0=Obj, 1=Subj))"
        except ImportError:
            return "Error: textblob not installed. Run `pip install textblob`."
        except Exception as e:
            return "Error analyzing sentiment: " + str(e)

    @staticmethod
    def calculate_rice_score(reach: float, impact: float, confidence: float, effort: float) -> str:
        """Calculates RICE score: (Reach * Impact * Confidence) / Effort."""
        try:
            score = (reach * impact * confidence) / effort
            return f"RICE Score: {score:.2f}"
        except ZeroDivisionError:
            return "Error: Effort cannot be zero."
        except Exception as e:
            return f"Error calculating RICE score: {e}"

    @staticmethod
    def calculate_moscow_priority(value: int, effort: int) -> str:
        """Suggests MoSCoW priority based on Value and Effort (1-10 scale)."""
        # Simple heuristic
        if value >= 8 and effort <= 5: return "Must Have"
        if value >= 6 and effort <= 8: return "Should Have"
        if value >= 4: return "Could Have"
        return "Won't Have"

class DesignToolbox:
    @staticmethod
    def check_contrast_ratio(hex1: str, hex2: str) -> str:
        """Calculates contrast ratio between two hex colors (e.g., #FFFFFF, #000000)."""
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def relative_luminance(rgb):
            def adjust(c):
                c = c / 255.0
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            r, g, b = [adjust(c) for c in rgb]
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        try:
            rgb1 = hex_to_rgb(hex1)
            rgb2 = hex_to_rgb(hex2)
            l1 = relative_luminance(rgb1)
            l2 = relative_luminance(rgb2)
            
            ratio = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
            pass_aa = "PASS" if ratio >= 4.5 else "FAIL"
            pass_aaa = "PASS" if ratio >= 7 else "FAIL"
            
            return f"Contrast Ratio: {ratio:.2f}:1\nWCAG AA: {pass_aa}\nWCAG AAA: {pass_aaa}"
        except Exception as e:
            return f"Error calculating contrast: {e}"

    @staticmethod
    def validate_hex_code(color: str) -> str:
        import re
        if re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color):
             return f"'{color}' is a VALID hex code."
        return f"'{color}' is INVALID."


class CodeAnalysisToolbox:
    """Tools for analyzing code quality and structure."""
    
    @staticmethod
    def analyze_code_complexity(path: str) -> str:
        """Analyzes cyclomatic complexity of Python code."""
        try:
            from radon.complexity import cc_visit
            from radon.raw import analyze
        except ImportError:
            return "Error: radon not installed. Run `pip install radon`."
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Cyclomatic complexity
            cc_results = cc_visit(code)
            raw_analysis = analyze(code)
            
            output = [f"=== Code Analysis: {path} ==="]
            output.append(f"LOC: {raw_analysis.loc}, SLOC: {raw_analysis.sloc}")
            output.append(f"Comments: {raw_analysis.comments}, Multi: {raw_analysis.multi}")
            output.append("\nCyclomatic Complexity:")
            
            for block in cc_results:
                grade = 'A' if block.complexity <= 5 else 'B' if block.complexity <= 10 else 'C' if block.complexity <= 20 else 'F'
                output.append(f"  {block.name} ({block.lineno}): {block.complexity} [{grade}]")
            
            return "\n".join(output)
        except Exception as e:
            return f"Error analyzing complexity: {e}"
    
    @staticmethod
    def find_dependencies(path: str = ".") -> str:
        """Extracts imports from Python files."""
        import ast
        
        imports = set()
        try:
            for root, _, files in os.walk(path):
                if ".git" in root or "__pycache__" in root or "venv" in root:
                    continue
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                tree = ast.parse(f.read())
                            
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for alias in node.names:
                                        imports.add(alias.name.split('.')[0])
                                elif isinstance(node, ast.ImportFrom):
                                    if node.module:
                                        imports.add(node.module.split('.')[0])
                        except:
                            pass
            
            # Filter stdlib
            stdlib = {'os', 'sys', 'json', 're', 'typing', 'abc', 'collections', 
                      'datetime', 'time', 'threading', 'queue', 'io', 'pathlib',
                      'functools', 'itertools', 'subprocess', 'glob', 'shutil'}
            external = sorted(imports - stdlib)
            
            return f"External Dependencies Found:\n" + "\n".join(f"  - {pkg}" for pkg in external) if external else "No external dependencies found."
        except Exception as e:
            return f"Error finding dependencies: {e}"
    
    @staticmethod
    def lint_code(path: str) -> str:
        """Runs linting on Python code using ruff or pylint."""
        import shutil
        
        if shutil.which("ruff"):
            result = Toolbox.run_command(f"ruff check {path}")
            return f"Ruff Analysis:\n{result}" if result else "No linting issues found."
        elif shutil.which("pylint"):
            result = Toolbox.run_command(f"pylint {path} --output-format=text")
            return f"Pylint Analysis:\n{result}"
        else:
            return "Error: No linter installed. Run `pip install ruff` or `pip install pylint`."
    
    @staticmethod
    def format_code(path: str, dry_run: bool = True) -> str:
        """Formats Python code using black."""
        import shutil
        
        if not shutil.which("black"):
            return "Error: black not installed. Run `pip install black`."
        
        cmd = f"black {'--diff' if dry_run else ''} {path}"
        result = Toolbox.run_command(cmd)
        return f"{'Diff (dry run):' if dry_run else 'Formatted:'}\n{result}"
    
    @staticmethod
    def detect_code_smells(path: str) -> str:
        """Detects common code smells in Python files."""
        import ast
        
        smells = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
                lines = code.split('\n')
            
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # Long functions
                if isinstance(node, ast.FunctionDef):
                    end_line = getattr(node, 'end_lineno', node.lineno + 50)
                    func_length = end_line - node.lineno
                    if func_length > 50:
                        smells.append(f"Long function '{node.name}' ({func_length} lines) at line {node.lineno}")
                    
                    # Too many arguments
                    arg_count = len(node.args.args)
                    if arg_count > 5:
                        smells.append(f"Too many arguments ({arg_count}) in '{node.name}' at line {node.lineno}")
                
                # Deeply nested code
                if isinstance(node, (ast.If, ast.For, ast.While)):
                    depth = sum(1 for _ in ast.walk(node) if isinstance(_, (ast.If, ast.For, ast.While)))
                    if depth > 4:
                        smells.append(f"Deep nesting (depth {depth}) at line {node.lineno}")
            
            # Long lines
            for i, line in enumerate(lines, 1):
                if len(line) > 120:
                    smells.append(f"Line {i} exceeds 120 characters ({len(line)})")
            
            return "\n".join(smells) if smells else "No code smells detected."
        except Exception as e:
            return f"Error detecting code smells: {e}"


class TestingToolbox:
    """Tools for testing and test coverage."""
    
    @staticmethod
    def run_tests(path: str = ".", verbose: bool = True) -> str:
        """Runs pytest on the specified path."""
        import shutil
        
        if not shutil.which("pytest"):
            return "Error: pytest not installed. Run `pip install pytest`."
        
        cmd = f"python -m pytest {path} {'-v' if verbose else ''} --tb=short"
        return Toolbox.run_command(cmd)
    
    @staticmethod
    def run_specific_test(test_path: str) -> str:
        """Runs a specific test file or function."""
        import shutil
        
        if not shutil.which("pytest"):
            return "Error: pytest not installed."
        
        return Toolbox.run_command(f"python -m pytest {test_path} -v")
    
    @staticmethod
    def check_test_coverage(path: str = ".") -> str:
        """Checks test coverage using coverage.py."""
        import shutil
        
        if not shutil.which("coverage"):
            return "Error: coverage not installed. Run `pip install coverage`."
        
        Toolbox.run_command(f"coverage run -m pytest {path} -q")
        result = Toolbox.run_command("coverage report -m")
        return f"Coverage Report:\n{result}"
    
    @staticmethod
    def generate_test_skeleton(source_file: str) -> str:
        """Generates a test skeleton for a Python file."""
        import ast
        
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            test_code = ['import unittest', f'# Tests for {source_file}', '']
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    test_code.append(f'class Test{node.name}(unittest.TestCase):')
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                            test_code.append(f'    def test_{item.name}(self):')
                            test_code.append('        # TODO: Implement test')
                            test_code.append('        pass')
                            test_code.append('')
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    if not node.name.startswith('_'):
                        test_code.append(f'def test_{node.name}():')
                        test_code.append('    # TODO: Implement test')
                        test_code.append('    pass')
                        test_code.append('')
            
            test_code.append("\nif __name__ == '__main__':")
            test_code.append("    unittest.main()")
            
            return "\n".join(test_code)
        except Exception as e:
            return f"Error generating test skeleton: {e}"


class DatabaseToolbox:
    """Tools for database and API operations."""
    
    @staticmethod
    def query_sqlite(db_path: str, query: str) -> str:
        """Executes a query on a SQLite database."""
        import sqlite3
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                result = [" | ".join(columns)]
                result.append("-" * len(result[0]))
                for row in rows[:50]:
                    result.append(" | ".join(str(cell) for cell in row))
                if len(rows) > 50:
                    result.append(f"... ({len(rows) - 50} more rows)")
                conn.close()
                return "\n".join(result)
            else:
                conn.commit()
                affected = cursor.rowcount
                conn.close()
                return f"Query executed. Rows affected: {affected}"
        except Exception as e:
            return f"Database error: {e}"
    
    @staticmethod
    def make_api_request(url: str, method: str = "GET", data: dict = None, headers: dict = None) -> str:
        """Makes an HTTP request to an API."""
        try:
            import requests
        except ImportError:
            return "Error: requests not installed. Run `pip install requests`."
        
        try:
            method = method.upper()
            kwargs = {'timeout': 10}
            if headers:
                kwargs['headers'] = headers
            if data:
                kwargs['json'] = data
            
            if method == "GET":
                response = requests.get(url, **kwargs)
            elif method == "POST":
                response = requests.post(url, **kwargs)
            elif method == "PUT":
                response = requests.put(url, **kwargs)
            elif method == "DELETE":
                response = requests.delete(url, **kwargs)
            else:
                return f"Unsupported method: {method}"
            
            return f"Status: {response.status_code}\nBody:\n{response.text[:3000]}"
        except Exception as e:
            return f"API request error: {e}"
    
    @staticmethod
    def parse_json_response(json_string: str, path: str = "") -> str:
        """Parses JSON and optionally extracts a path (e.g., 'data.items[0].name')."""
        import json as json_lib
        
        try:
            data = json_lib.loads(json_string)
            
            if path:
                parts = re.split(r'\.|\[|\]', path)
                parts = [p for p in parts if p]
                for part in parts:
                    if part.isdigit():
                        data = data[int(part)]
                    else:
                        data = data[part]
            
            return json_lib.dumps(data, indent=2)
        except Exception as e:
            return f"JSON parsing error: {e}"


class DevOpsToolbox:
    """Tools for Docker and deployment operations."""
    
    @staticmethod
    def _check_docker() -> bool:
        import shutil
        return shutil.which("docker") is not None
    
    @staticmethod
    def docker_build(tag: str, dockerfile: str = ".", context: str = ".") -> str:
        """Builds a Docker image."""
        if not DevOpsToolbox._check_docker():
            return "Error: Docker is not installed or not in PATH."
        
        cmd = f"docker build -t {tag} -f {dockerfile} {context}"
        return Toolbox.run_command(cmd)
    
    @staticmethod
    def docker_run(image: str, name: str = "", ports: str = "", env: dict = None, detach: bool = True) -> str:
        """Runs a Docker container."""
        if not DevOpsToolbox._check_docker():
            return "Error: Docker is not installed."
        
        cmd = f"docker run {'-d' if detach else ''}"
        if name:
            cmd += f" --name {name}"
        if ports:
            cmd += f" -p {ports}"
        if env:
            for k, v in env.items():
                cmd += f" -e {k}={v}"
        cmd += f" {image}"
        
        return Toolbox.run_command(cmd)
    
    @staticmethod
    def list_containers(all_containers: bool = False) -> str:
        """Lists Docker containers."""
        if not DevOpsToolbox._check_docker():
            return "Error: Docker is not installed."
        
        cmd = f"docker ps {'-a' if all_containers else ''}"
        return Toolbox.run_command(cmd)
    
    @staticmethod
    def read_logs(container: str, tail: int = 100) -> str:
        """Reads logs from a Docker container."""
        if not DevOpsToolbox._check_docker():
            return "Error: Docker is not installed."
        
        return Toolbox.run_command(f"docker logs {container} --tail {tail}")


class DocumentationToolbox:
    """Tools for generating and managing documentation."""
    
    @staticmethod
    def generate_readme(path: str = ".") -> str:
        """Generates a README.md template based on project structure."""
        try:
            project_name = os.path.basename(os.path.abspath(path))
            
            # Detect project type
            files = os.listdir(path)
            has_python = any(f.endswith('.py') for f in files)
            has_package_json = 'package.json' in files
            has_requirements = 'requirements.txt' in files
            
            readme = [f"# {project_name.title()}", ""]
            readme.append("## Description")
            readme.append("TODO: Add project description")
            readme.append("")
            readme.append("## Installation")
            
            if has_python:
                readme.append("```bash")
                if has_requirements:
                    readme.append("pip install -r requirements.txt")
                else:
                    readme.append("pip install .")
                readme.append("```")
            elif has_package_json:
                readme.append("```bash")
                readme.append("npm install")
                readme.append("```")
            
            readme.append("")
            readme.append("## Usage")
            readme.append("```bash")
            readme.append(f"# TODO: Add usage example")
            readme.append("```")
            readme.append("")
            readme.append("## License")
            readme.append("MIT")
            
            return "\n".join(readme)
        except Exception as e:
            return f"Error generating README: {e}"
    
    @staticmethod
    def extract_api_docs(source_file: str) -> str:
        """Extracts docstrings from a Python file into markdown."""
        import ast
        
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            docs = [f"# API Documentation: {os.path.basename(source_file)}", ""]
            
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    docs.append(f"## class `{node.name}`")
                    if ast.get_docstring(node):
                        docs.append(ast.get_docstring(node))
                    docs.append("")
                    
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            args = [a.arg for a in item.args.args if a.arg != 'self']
                            docs.append(f"### `{item.name}({', '.join(args)})`")
                            if ast.get_docstring(item):
                                docs.append(ast.get_docstring(item))
                            docs.append("")
                
                elif isinstance(node, ast.FunctionDef):
                    args = [a.arg for a in node.args.args]
                    docs.append(f"## `{node.name}({', '.join(args)})`")
                    if ast.get_docstring(node):
                        docs.append(ast.get_docstring(node))
                    docs.append("")
            
            return "\n".join(docs)
        except Exception as e:
            return f"Error extracting docs: {e}"
    
    @staticmethod
    def create_changelog(commits: int = 20) -> str:
        """Creates a changelog from recent git commits."""
        result = Toolbox.run_command(f"git log --oneline -n {commits}")
        
        changelog = ["# Changelog", ""]
        for line in result.strip().split('\n'):
            if line:
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    changelog.append(f"- {parts[1]} ({parts[0][:7]})")
        
        return "\n".join(changelog)
    
    @staticmethod
    def generate_mermaid_diagram(source_file: str) -> str:
        """Generates a Mermaid class diagram from Python code."""
        import ast
        
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            lines = ["```mermaid", "classDiagram"]
            
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    lines.append(f"    class {node.name} {{")
                    
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            prefix = "-" if item.name.startswith('_') else "+"
                            lines.append(f"        {prefix}{item.name}()")
                        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            lines.append(f"        +{item.target.id}")
                    
                    lines.append("    }")
                    
                    # Check for base classes
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            lines.append(f"    {base.id} <|-- {node.name}")
            
            lines.append("```")
            return "\n".join(lines)
        except Exception as e:
            return f"Error generating diagram: {e}"


class SecurityToolbox:
    """Tools for security scanning and auditing."""
    
    @staticmethod
    def scan_vulnerabilities(path: str = ".") -> str:
        """Scans Python code for security vulnerabilities using bandit."""
        import shutil
        
        if not shutil.which("bandit"):
            return "Error: bandit not installed. Run `pip install bandit`."
        
        result = Toolbox.run_command(f"bandit -r {path} -f txt -ll")
        return f"Security Scan Results:\n{result}" if result else "No vulnerabilities found."
    
    @staticmethod
    def check_secrets(path: str = ".") -> str:
        """Scans for potential leaked secrets in code."""
        patterns = {
            'AWS Key': r'AKIA[0-9A-Z]{16}',
            'GitHub Token': r'ghp_[a-zA-Z0-9]{36}',
            'Generic API Key': r'[aA][pP][iI][-_]?[kK][eE][yY][\s]*[=:]\s*["\']?[a-zA-Z0-9]{20,}',
            'Private Key': r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----',
            'Password in Code': r'[pP]assword[\s]*[=:]\s*["\'][^"\']{8,}["\']',
            'JWT Token': r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
        }
        
        findings = []
        try:
            for root, _, files in os.walk(path):
                if ".git" in root or "node_modules" in root:
                    continue
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.json', '.yaml', '.yml', '.env')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                for secret_type, pattern in patterns.items():
                                    if re.search(pattern, content):
                                        findings.append(f"[{secret_type}] Found in {file_path}")
                        except:
                            pass
            
            return "\n".join(findings) if findings else "No secrets detected."
        except Exception as e:
            return f"Error scanning for secrets: {e}"
    
    @staticmethod
    def validate_dependencies() -> str:
        """Checks installed packages for known vulnerabilities."""
        import shutil
        
        if shutil.which("safety"):
            result = Toolbox.run_command("safety check --output text")
            return f"Dependency Audit:\n{result}"
        elif shutil.which("pip-audit"):
            result = Toolbox.run_command("pip-audit")
            return f"Dependency Audit:\n{result}"
        else:
            return "Error: No audit tool installed. Run `pip install safety` or `pip install pip-audit`."


class MemoryToolbox:
    """Tools for persistent memory and snippet management."""
    
    MEMORY_PATH = os.path.expanduser("~/.crytonix/memory.json")
    
    @staticmethod
    def _load_memory() -> dict:
        if os.path.exists(MemoryToolbox.MEMORY_PATH):
            try:
                with open(MemoryToolbox.MEMORY_PATH, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except (json.JSONDecodeError, IOError):
                pass  # Return default if file is corrupted
        return {"snippets": {}, "notes": []}
    
    @staticmethod
    def _save_memory(data: dict):
        os.makedirs(os.path.dirname(MemoryToolbox.MEMORY_PATH), exist_ok=True)
        with open(MemoryToolbox.MEMORY_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def save_snippet(name: str, content: str, tags: str = "") -> str:
        """Saves a code snippet for later reuse."""
        memory = MemoryToolbox._load_memory()
        memory["snippets"][name] = {
            "content": content,
            "tags": tags.split(",") if tags else [],
            "created": __import__('datetime').datetime.now().isoformat()
        }
        MemoryToolbox._save_memory(memory)
        return f"Snippet '{name}' saved successfully."
    
    @staticmethod
    def recall_snippet(name: str = "", tag: str = "") -> str:
        """Retrieves a saved snippet by name or tag."""
        memory = MemoryToolbox._load_memory()
        snippets = memory.get("snippets", {})
        
        if name:
            if name in snippets:
                return f"=== {name} ===\n{snippets[name]['content']}"
            return f"Snippet '{name}' not found."
        
        if tag:
            matches = [(k, v) for k, v in snippets.items() if tag in v.get('tags', [])]
            if matches:
                return "\n\n".join(f"=== {k} ===\n{v['content']}" for k, v in matches)
            return f"No snippets found with tag '{tag}'."
        
        # List all
        if snippets:
            return "Saved Snippets:\n" + "\n".join(f"  - {k} (tags: {','.join(v.get('tags', []))})" for k, v in snippets.items())
        return "No snippets saved yet."
    
    @staticmethod
    def summarize_conversation(messages: list, max_length: int = 500) -> str:
        """Summarizes a conversation for context compression."""
        text = "\n".join(m.get('content', '')[:200] for m in messages if isinstance(m.get('content'), str))
        
        # Simple extractive summary: Take first and last parts
        if len(text) <= max_length:
            return text
        
        half = max_length // 2
        return text[:half] + "\n...[summarized]...\n" + text[-half:]


class AssetToolbox:
    """Tools for image and asset manipulation."""
    
    @staticmethod
    def optimize_image(path: str, quality: int = 85, max_size: int = 1024) -> str:
        """Optimizes an image by resizing and compressing."""
        try:
            from PIL import Image
        except ImportError:
            return "Error: Pillow not installed. Run `pip install Pillow`."
        
        try:
            img = Image.open(path)
            original_size = os.path.getsize(path)
            
            # Resize if too large
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save optimized
            output_path = path.rsplit('.', 1)[0] + '_optimized.' + path.rsplit('.', 1)[1]
            img.save(output_path, quality=quality, optimize=True)
            new_size = os.path.getsize(output_path)
            
            reduction = (1 - new_size / original_size) * 100
            return f"Optimized: {output_path}\nSize: {original_size}B -> {new_size}B ({reduction:.1f}% reduction)"
        except Exception as e:
            return f"Error optimizing image: {e}"
    
    @staticmethod
    def extract_colors(path: str, num_colors: int = 5) -> str:
        """Extracts dominant colors from an image."""
        try:
            from PIL import Image
            from collections import Counter
        except ImportError:
            return "Error: Pillow not installed. Run `pip install Pillow`."
        
        try:
            img = Image.open(path)
            img = img.convert('RGB')
            img = img.resize((100, 100))  # Reduce for speed
            
            pixels = list(img.getdata())
            # Quantize to reduce colors
            quantized = [(r // 32 * 32, g // 32 * 32, b // 32 * 32) for r, g, b in pixels]
            counter = Counter(quantized)
            
            results = ["Dominant Colors:"]
            for color, count in counter.most_common(num_colors):
                hex_color = "#{:02x}{:02x}{:02x}".format(*color)
                pct = count / len(pixels) * 100
                results.append(f"  {hex_color} ({pct:.1f}%)")
            
            return "\n".join(results)
        except Exception as e:
            return f"Error extracting colors: {e}"
    
    @staticmethod
    def convert_image_format(path: str, target_format: str) -> str:
        """Converts an image to a different format (png, jpg, webp)."""
        try:
            from PIL import Image
        except ImportError:
            return "Error: Pillow not installed. Run `pip install Pillow`."
        
        try:
            img = Image.open(path)
            output_path = path.rsplit('.', 1)[0] + '.' + target_format.lower()
            
            if target_format.lower() in ('jpg', 'jpeg'):
                img = img.convert('RGB')
            
            img.save(output_path)
            return f"Converted: {output_path}"
        except Exception as e:
            return f"Error converting image: {e}"


class ScaffoldToolbox:
    """Tools for project scaffolding and templates."""
    
    @staticmethod
    def create_python_project(name: str, style: str = "basic") -> str:
        """Creates a Python project structure."""
        try:
            base = os.path.join(".", name)
            os.makedirs(base, exist_ok=True)
            os.makedirs(os.path.join(base, name.replace("-", "_")), exist_ok=True)
            os.makedirs(os.path.join(base, "tests"), exist_ok=True)
            
            # __init__.py
            init_path = os.path.join(base, name.replace("-", "_"), "__init__.py")
            with open(init_path, 'w') as f:
                f.write(f'"""{ name} package."""\n__version__ = "0.1.0"\n')
            
            # pyproject.toml
            pyproject = f'''[project]
name = "{name}"
version = "0.1.0"
description = "A Python project"
requires-python = ">=3.9"
dependencies = []

[project.optional-dependencies]
dev = ["pytest", "black", "ruff"]
'''
            with open(os.path.join(base, "pyproject.toml"), 'w') as f:
                f.write(pyproject)
            
            # README
            with open(os.path.join(base, "README.md"), 'w') as f:
                f.write(f"# {name}\n\nA Python project.\n")
            
            # .gitignore
            with open(os.path.join(base, ".gitignore"), 'w') as f:
                f.write("__pycache__/\n*.pyc\n.venv/\ndist/\n*.egg-info/\n")
            
            return f"Python project '{name}' created at ./{name}/"
        except Exception as e:
            return f"Error creating project: {e}"
    
    @staticmethod
    def create_react_app(name: str, template: str = "vite") -> str:
        """Creates a React app using Vite or Create React App."""
        import shutil
        
        if not shutil.which("npm"):
            return "Error: npm not installed."
        
        if template == "vite":
            return Toolbox.run_command(f"npm create vite@latest {name} -- --template react")
        else:
            return Toolbox.run_command(f"npx create-react-app {name}")
    
    @staticmethod
    def add_ci_pipeline(ci_type: str = "github") -> str:
        """Adds a CI pipeline configuration."""
        if ci_type == "github":
            os.makedirs(".github/workflows", exist_ok=True)
            
            workflow = '''name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest
'''
            with open(".github/workflows/ci.yml", 'w') as f:
                f.write(workflow)
            
            return "GitHub Actions CI pipeline created at .github/workflows/ci.yml"
        
        return f"Unknown CI type: {ci_type}"
    
    @staticmethod
    def generate_gitignore(language: str = "python") -> str:
        """Generates a .gitignore file for the specified language."""
        templates = {
            "python": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.venv/
venv/
ENV/
.env
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
""",
            "node": """# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.eslintcache
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
dist/
build/
coverage/
""",
            "react": """# React/Node
node_modules/
build/
dist/
.env
.env.local
npm-debug.log*
.DS_Store
coverage/
"""
        }
        
        content = templates.get(language.lower(), templates["python"])
        return content


class PerformanceToolbox:
    """Tools for performance profiling and benchmarking."""
    
    @staticmethod
    def profile_code(path: str) -> str:
        """Profile Python code execution time using cProfile."""
        import cProfile
        import pstats
        from io import StringIO
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            profiler = cProfile.Profile()
            profiler.enable()
            
            try:
                exec(compile(code, path, 'exec'), {'__name__': '__main__'})
            except Exception as e:
                pass  # Code may have errors, but we want profiling data
            
            profiler.disable()
            
            stream = StringIO()
            stats = pstats.Stats(profiler, stream=stream)
            stats.sort_stats('cumulative')
            stats.print_stats(20)
            
            return f"Profile Results for {path}:\n{stream.getvalue()}"
        except Exception as e:
            return f"Error profiling code: {e}"
    
    @staticmethod
    def memory_profiler(path: str) -> str:
        """Analyze memory usage of a Python file."""
        try:
            import tracemalloc
        except ImportError:
            return "Error: tracemalloc not available."
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tracemalloc.start()
            
            try:
                exec(compile(code, path, 'exec'), {'__name__': '__main__'})
            except:
                pass
            
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')[:10]
            
            results = [f"Memory Profile for {path}:", "Top 10 memory allocations:"]
            for stat in top_stats:
                results.append(f"  {stat}")
            
            tracemalloc.stop()
            return "\n".join(results)
        except Exception as e:
            return f"Error analyzing memory: {e}"
    
    @staticmethod
    def benchmark_function(code: str, iterations: int = 1000) -> str:
        """Benchmark a code snippet with multiple iterations."""
        import timeit
        
        try:
            timer = timeit.Timer(code)
            times = timer.repeat(repeat=3, number=iterations)
            
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            return f"""Benchmark Results ({iterations} iterations):
  Average: {avg_time:.6f}s
  Min: {min_time:.6f}s
  Max: {max_time:.6f}s
  Per iteration: {avg_time/iterations*1000:.4f}ms"""
        except Exception as e:
            return f"Error benchmarking: {e}"
    
    @staticmethod
    def find_slow_operations(log_path: str, threshold_ms: float = 100) -> str:
        """Parse logs to find slow operations."""
        try:
            slow_ops = []
            pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(?:ms|milliseconds?)', re.IGNORECASE)
            
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    matches = pattern.findall(line)
                    for match in matches:
                        if float(match) >= threshold_ms:
                            slow_ops.append(f"Line {i}: {line.strip()[:100]}")
            
            if slow_ops:
                return f"Slow operations (>={threshold_ms}ms):\n" + "\n".join(slow_ops[:20])
            return f"No operations slower than {threshold_ms}ms found."
        except Exception as e:
            return f"Error parsing logs: {e}"


class AIToolbox:
    """Tools for AI/LLM integration."""
    
    @staticmethod
    def count_tokens(text: str, model: str = "gpt-4") -> str:
        """Count tokens in text for LLM context estimation."""
        try:
            import tiktoken
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")
            
            tokens = encoding.encode(text)
            return f"Token count: {len(tokens)} (model: {model})"
        except ImportError:
            # Fallback: rough estimation
            words = len(text.split())
            chars = len(text)
            estimated = max(words * 1.3, chars / 4)
            return f"Estimated tokens: ~{int(estimated)} (install tiktoken for accuracy)"
    
    @staticmethod
    def explain_code(code: str) -> str:
        """Generate a basic explanation of code structure."""
        import ast
        
        try:
            tree = ast.parse(code)
            
            explanation = ["Code Structure Analysis:"]
            
            imports = []
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(f"{node.module}")
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append(f"{node.name} ({len(methods)} methods)")
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                    args = [a.arg for a in node.args.args]
                    functions.append(f"{node.name}({', '.join(args)})")
            
            if imports:
                explanation.append(f"\n📦 Imports: {', '.join(set(imports)[:10])}")
            if classes:
                explanation.append(f"\n🏗️ Classes: {', '.join(classes)}")
            if functions:
                explanation.append(f"\n⚡ Functions: {', '.join(functions)}")
            
            return "\n".join(explanation)
        except Exception as e:
            return f"Error analyzing code: {e}"
    
    @staticmethod
    def suggest_refactoring(path: str) -> str:
        """Suggest refactoring improvements for code."""
        import ast
        
        suggestions = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check function length
                    end_line = getattr(node, 'end_lineno', node.lineno + 50)
                    length = end_line - node.lineno
                    if length > 30:
                        suggestions.append(f"📏 Function '{node.name}' is {length} lines - consider breaking it up")
                    
                    # Check argument count
                    arg_count = len(node.args.args)
                    if arg_count > 5:
                        suggestions.append(f"🔢 Function '{node.name}' has {arg_count} arguments - consider using a data class")
                    
                    # Check for nested functions
                    nested = [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef) and n != node]
                    if len(nested) > 2:
                        suggestions.append(f"🪆 Function '{node.name}' has {len(nested)} nested functions - consider extracting")
                
                # Check for bare except
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    suggestions.append(f"⚠️ Line {node.lineno}: Bare 'except:' - specify exception type")
            
            return "\n".join(suggestions) if suggestions else "✅ No major refactoring suggestions."
        except Exception as e:
            return f"Error analyzing code: {e}"


class EnvironmentToolbox:
    """Tools for environment and configuration management."""
    
    @staticmethod
    def check_env_vars(required: List[str]) -> str:
        """Validate that required environment variables are set."""
        missing = []
        present = []
        
        for var in required:
            if os.environ.get(var):
                present.append(f"✅ {var}")
            else:
                missing.append(f"❌ {var}")
        
        result = []
        if present:
            result.append("Present:\n" + "\n".join(present))
        if missing:
            result.append("Missing:\n" + "\n".join(missing))
        
        return "\n\n".join(result) if result else "No variables to check."
    
    @staticmethod
    def compare_env_files(file1: str, file2: str) -> str:
        """Compare two .env files and show differences."""
        def parse_env(path):
            env = {}
            if os.path.exists(path):
                with open(path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            env[key.strip()] = value.strip()
            return env
        
        try:
            env1 = parse_env(file1)
            env2 = parse_env(file2)
            
            all_keys = set(env1.keys()) | set(env2.keys())
            
            results = []
            for key in sorted(all_keys):
                in1 = key in env1
                in2 = key in env2
                
                if in1 and in2:
                    if env1[key] != env2[key]:
                        results.append(f"⚡ {key}: differs")
                elif in1:
                    results.append(f"➖ {key}: only in {file1}")
                else:
                    results.append(f"➕ {key}: only in {file2}")
            
            return "\n".join(results) if results else "Files are identical."
        except Exception as e:
            return f"Error comparing files: {e}"
    
    @staticmethod
    def generate_env_template(env_file: str = ".env") -> str:
        """Generate .env.example from .env file (values replaced with placeholders)."""
        try:
            if not os.path.exists(env_file):
                return f"Error: {env_file} not found."
            
            template = []
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        template.append(line)
                    elif '=' in line:
                        key = line.split('=', 1)[0].strip()
                        template.append(f"{key}=your_{key.lower()}_here")
                    else:
                        template.append(line)
            
            return "\n".join(template)
        except Exception as e:
            return f"Error generating template: {e}"
    
    @staticmethod
    def validate_json_config(config_path: str, schema_path: str = "") -> str:
        """Validate a JSON config file, optionally against a schema."""
        import json as json_lib
        
        try:
            with open(config_path, 'r') as f:
                config = json_lib.load(f)
            
            if schema_path:
                try:
                    from jsonschema import validate, ValidationError
                    with open(schema_path, 'r') as f:
                        schema = json_lib.load(f)
                    validate(instance=config, schema=schema)
                    return f"✅ {config_path} is valid against schema."
                except ImportError:
                    return "Warning: jsonschema not installed. Run `pip install jsonschema`."
                except ValidationError as e:
                    return f"❌ Validation error: {e.message}"
            
            return f"✅ {config_path} is valid JSON with {len(config)} top-level keys."
        except json_lib.JSONDecodeError as e:
            return f"❌ Invalid JSON: {e}"
        except Exception as e:
            return f"Error validating config: {e}"


class MonitoringToolbox:
    """Tools for log parsing and observability."""
    
    @staticmethod
    def parse_logs(path: str, pattern: str, limit: int = 50) -> str:
        """Parse and filter log files by pattern."""
        try:
            matches = []
            regex = re.compile(pattern, re.IGNORECASE)
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if regex.search(line):
                        matches.append(f"{i}: {line.strip()[:150]}")
                        if len(matches) >= limit:
                            break
            
            if matches:
                return f"Found {len(matches)} matches:\n" + "\n".join(matches)
            return "No matches found."
        except Exception as e:
            return f"Error parsing logs: {e}"
    
    @staticmethod
    def analyze_error_frequency(log_path: str) -> str:
        """Find most common errors in logs."""
        from collections import Counter
        
        error_patterns = [
            r'error[:\s](.{0,50})',
            r'exception[:\s](.{0,50})',
            r'failed[:\s](.{0,50})',
            r'traceback',
        ]
        
        try:
            errors = []
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line_lower = line.lower()
                    for pattern in error_patterns:
                        if re.search(pattern, line_lower):
                            # Extract error type
                            errors.append(line.strip()[:80])
                            break
            
            counter = Counter(errors)
            
            if counter:
                results = ["Error Frequency Analysis:", ""]
                for error, count in counter.most_common(10):
                    results.append(f"  [{count}x] {error}")
                return "\n".join(results)
            return "No errors found in log."
        except Exception as e:
            return f"Error analyzing logs: {e}"
    
    @staticmethod
    def health_check(endpoints: List[str]) -> str:
        """Check health of multiple endpoints."""
        try:
            import requests
        except ImportError:
            return "Error: requests not installed."
        
        results = ["Health Check Results:", ""]
        
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                status = "✅" if response.status_code < 400 else "⚠️"
                results.append(f"{status} {endpoint} - {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
            except requests.Timeout:
                results.append(f"⏱️ {endpoint} - Timeout")
            except requests.RequestException as e:
                results.append(f"❌ {endpoint} - {str(e)[:50]}")
        
        return "\n".join(results)
    
    @staticmethod
    def tail_log(path: str, lines: int = 50) -> str:
        """Get the last N lines of a log file."""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
            
            tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return f"Last {len(tail)} lines of {path}:\n" + "".join(tail)
        except Exception as e:
            return f"Error reading log: {e}"


class MigrationToolbox:
    """Tools for database migration management."""
    
    @staticmethod
    def generate_migration(table_name: str, columns: Dict[str, str]) -> str:
        """Generate a database migration file."""
        import datetime
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"migrations/{timestamp}_create_{table_name}.sql"
        
        column_defs = []
        for col_name, col_type in columns.items():
            column_defs.append(f"    {col_name} {col_type}")
        
        migration = f"""-- Migration: Create {table_name}
-- Generated: {datetime.datetime.now().isoformat()}

-- UP
CREATE TABLE IF NOT EXISTS {table_name} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
{','.join(column_defs)},
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DOWN
DROP TABLE IF EXISTS {table_name};
"""
        
        try:
            os.makedirs("migrations", exist_ok=True)
            with open(filename, 'w') as f:
                f.write(migration)
            return f"Migration created: {filename}"
        except Exception as e:
            return f"Error creating migration: {e}"
    
    @staticmethod
    def list_migrations(migrations_dir: str = "migrations") -> str:
        """List all migration files."""
        try:
            if not os.path.exists(migrations_dir):
                return f"No migrations directory found at {migrations_dir}"
            
            files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
            
            if not files:
                return "No migrations found."
            
            results = ["Migrations:", ""]
            for f in files:
                results.append(f"  📄 {os.path.basename(f)}")
            
            return "\n".join(results)
        except Exception as e:
            return f"Error listing migrations: {e}"
    
    @staticmethod
    def compare_schemas(db1_path: str, db2_path: str) -> str:
        """Compare schemas of two SQLite databases."""
        import sqlite3
        
        def get_schema(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name")
            schema = {row[0].split('(')[0].split()[-1]: row[0] for row in cursor.fetchall() if row[0]}
            conn.close()
            return schema
        
        try:
            schema1 = get_schema(db1_path)
            schema2 = get_schema(db2_path)
            
            all_tables = set(schema1.keys()) | set(schema2.keys())
            
            results = ["Schema Comparison:", ""]
            for table in sorted(all_tables):
                in1 = table in schema1
                in2 = table in schema2
                
                if in1 and in2:
                    if schema1[table] != schema2[table]:
                        results.append(f"⚡ {table}: schema differs")
                elif in1:
                    results.append(f"➖ {table}: only in {db1_path}")
                else:
                    results.append(f"➕ {table}: only in {db2_path}")
            
            return "\n".join(results) if len(results) > 2 else "Schemas are identical."
        except Exception as e:
            return f"Error comparing schemas: {e}"


class CollaborationToolbox:
    """Enhanced tools for GitHub collaboration."""
    
    @staticmethod
    def _check_gh() -> bool:
        import shutil
        return shutil.which("gh") is not None
    
    @staticmethod
    def review_pr(pr_number: int) -> str:
        """Get PR files, comments, and review status."""
        if not CollaborationToolbox._check_gh():
            return "Error: gh CLI not installed."
        
        return Toolbox.run_command(f"gh pr view {pr_number} --json title,body,files,reviews,comments")
    
    @staticmethod
    def add_pr_comment(pr_number: int, comment: str) -> str:
        """Add a comment to a PR."""
        if not CollaborationToolbox._check_gh():
            return "Error: gh CLI not installed."
        
        return Toolbox.run_command(f'gh pr comment {pr_number} --body "{comment}"')
    
    @staticmethod
    def check_ci_status(branch: str = "") -> str:
        """Check CI/CD pipeline status."""
        if not CollaborationToolbox._check_gh():
            return "Error: gh CLI not installed."
        
        cmd = "gh run list --limit 5"
        if branch:
            cmd += f" --branch {branch}"
        
        return Toolbox.run_command(cmd)
    
    @staticmethod
    def merge_pr(pr_number: int, method: str = "squash") -> str:
        """Merge a PR with specified method (merge, squash, rebase)."""
        if not CollaborationToolbox._check_gh():
            return "Error: gh CLI not installed."
        
        return Toolbox.run_command(f"gh pr merge {pr_number} --{method}")
    
    @staticmethod
    def create_release(tag: str, title: str, notes: str = "") -> str:
        """Create a GitHub release."""
        if not CollaborationToolbox._check_gh():
            return "Error: gh CLI not installed."
        
        cmd = f'gh release create {tag} --title "{title}"'
        if notes:
            cmd += f' --notes "{notes}"'
        else:
            cmd += " --generate-notes"
        
        return Toolbox.run_command(cmd)
    
    @staticmethod
    def sync_fork() -> str:
        """Sync forked repository with upstream."""
        if not CollaborationToolbox._check_gh():
            return "Error: gh CLI not installed."
        
        return Toolbox.run_command("gh repo sync")
    
    @staticmethod
    def list_workflows() -> str:
        """List GitHub Actions workflows."""
        if not CollaborationToolbox._check_gh():
            return "Error: gh CLI not installed."
        
        return Toolbox.run_command("gh workflow list")


class RefactoringToolbox:
    """Tools for code refactoring operations."""
    
    @staticmethod
    def rename_symbol(path: str, old_name: str, new_name: str) -> str:
        """Rename a symbol across a file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(old_name) + r'\b'
            count = len(re.findall(pattern, content))
            
            if count == 0:
                return f"Symbol '{old_name}' not found in {path}"
            
            new_content = re.sub(pattern, new_name, content)
            
            Toolbox._show_diff(new_content, content, path)
            
            from rich.prompt import Confirm
            if not Confirm.ask(f"Rename {count} occurrences of '{old_name}' to '{new_name}'?", default=True):
                return "Rename cancelled."
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return f"Renamed {count} occurrences of '{old_name}' to '{new_name}' in {path}"
        except Exception as e:
            return f"Error renaming symbol: {e}"
    
    @staticmethod
    def find_dead_code(path: str = ".") -> str:
        """Detect potentially unused functions and imports."""
        import ast
        
        definitions = {}  # name -> file:line
        usages = set()
        
        try:
            for root, _, files in os.walk(path):
                if ".git" in root or "__pycache__" in root or "venv" in root:
                    continue
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                code = f.read()
                            
                            tree = ast.parse(code)
                            
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    if not node.name.startswith('_'):
                                        definitions[node.name] = f"{file_path}:{node.lineno}"
                                elif isinstance(node, ast.Name):
                                    usages.add(node.id)
                                elif isinstance(node, ast.Call):
                                    if isinstance(node.func, ast.Name):
                                        usages.add(node.func.id)
                        except:
                            pass
            
            unused = set(definitions.keys()) - usages
            
            if unused:
                results = ["Potentially unused code:", ""]
                for name in sorted(unused):
                    results.append(f"  ⚠️ {name} ({definitions[name]})")
                return "\n".join(results)
            return "No potentially dead code found."
        except Exception as e:
            return f"Error analyzing code: {e}"
    
    @staticmethod
    def find_duplicate_code(path: str = ".", min_lines: int = 5) -> str:
        """Find duplicate code blocks."""
        from collections import defaultdict
        
        code_blocks = defaultdict(list)
        
        try:
            for root, _, files in os.walk(path):
                if ".git" in root or "__pycache__" in root:
                    continue
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                            
                            # Sliding window for code blocks
                            for i in range(len(lines) - min_lines + 1):
                                block = "".join(lines[i:i+min_lines]).strip()
                                if block and not block.startswith('#'):
                                    code_blocks[block].append(f"{file_path}:{i+1}")
                        except:
                            pass
            
            duplicates = [(block, locs) for block, locs in code_blocks.items() if len(locs) > 1]
            
            if duplicates:
                results = ["Duplicate code blocks found:", ""]
                for block, locations in duplicates[:10]:
                    results.append(f"  📋 Block found at: {', '.join(locations)}")
                    results.append(f"     Preview: {block[:60]}...")
                return "\n".join(results)
            return "No duplicate code blocks found."
        except Exception as e:
            return f"Error finding duplicates: {e}"
    
    @staticmethod
    def extract_function(path: str, start_line: int, end_line: int, func_name: str) -> str:
        """Extract lines of code into a new function."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Extract the code block
            extracted = lines[start_line-1:end_line]
            
            # Determine indentation
            base_indent = len(extracted[0]) - len(extracted[0].lstrip())
            
            # Create new function
            new_func = [f"def {func_name}():\n"]
            for line in extracted:
                new_func.append("    " + line[base_indent:] if line.strip() else line)
            new_func.append("\n")
            
            # Replace extracted code with function call
            new_lines = lines[:start_line-1]
            new_lines.append(" " * base_indent + f"{func_name}()\n")
            new_lines.extend(lines[end_line:])
            
            # Insert function definition before the usage
            insert_point = 0
            for i, line in enumerate(new_lines):
                if line.startswith('def ') or line.startswith('class '):
                    insert_point = i
                    break
            
            final_lines = new_lines[:insert_point] + new_func + new_lines[insert_point:]
            
            new_content = "".join(final_lines)
            old_content = "".join(lines)
            
            Toolbox._show_diff(new_content, old_content, path)
            
            return f"Preview of extracting lines {start_line}-{end_line} to function '{func_name}'"
        except Exception as e:
            return f"Error extracting function: {e}"


class FrontendToolbox:
    """Tools for frontend development and CSS validation."""
    
    @staticmethod
    def validate_css(path: str) -> str:
        """Validate CSS syntax."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                css = f.read()
            
            issues = []
            
            # Check for unclosed braces
            open_braces = css.count('{')
            close_braces = css.count('}')
            if open_braces != close_braces:
                issues.append(f"⚠️ Mismatched braces: {open_braces} open, {close_braces} close")
            
            # Check for missing semicolons (basic check)
            lines = css.split('\n')
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.endswith(('{', '}', ';', '/*', '*/', ',')) and ':' in line:
                    if not line.startswith(('/*', '*', '//')):
                        issues.append(f"⚠️ Line {i}: Possible missing semicolon")
            
            # Check for vendor prefix consistency
            prefixes = ['-webkit-', '-moz-', '-ms-', '-o-']
            for prefix in prefixes:
                if prefix in css and not all(p in css or p == prefix for p in prefixes):
                    issues.append(f"💡 Consider adding all vendor prefixes (found {prefix})")
                    break
            
            if issues:
                return "\n".join(issues)
            return f"✅ {path} appears valid."
        except Exception as e:
            return f"Error validating CSS: {e}"
    
    @staticmethod
    def extract_css_colors(path: str) -> str:
        """Extract all colors from CSS file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                css = f.read()
            
            colors = set()
            
            # Hex colors
            hex_colors = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}\b', css)
            colors.update(hex_colors)
            
            # RGB/RGBA
            rgb_colors = re.findall(r'rgba?\([^)]+\)', css)
            colors.update(rgb_colors)
            
            # HSL/HSLA
            hsl_colors = re.findall(r'hsla?\([^)]+\)', css)
            colors.update(hsl_colors)
            
            # Named colors (common ones)
            named = re.findall(r'\b(red|blue|green|white|black|gray|grey|yellow|orange|purple|pink)\b', css, re.IGNORECASE)
            colors.update(named)
            
            if colors:
                return "Colors found:\n" + "\n".join(f"  🎨 {c}" for c in sorted(colors))
            return "No colors found."
        except Exception as e:
            return f"Error extracting colors: {e}"
    
    @staticmethod
    def minify_css(path: str) -> str:
        """Minify CSS file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                css = f.read()
            
            original_size = len(css)
            
            # Remove comments
            css = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)
            # Remove whitespace
            css = re.sub(r'\s+', ' ', css)
            # Remove space around special chars
            css = re.sub(r'\s*([{}:;,])\s*', r'\1', css)
            css = css.strip()
            
            new_size = len(css)
            reduction = (1 - new_size / original_size) * 100
            
            output_path = path.replace('.css', '.min.css')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(css)
            
            return f"Minified: {output_path}\n{original_size}B → {new_size}B ({reduction:.1f}% reduction)"
        except Exception as e:
            return f"Error minifying CSS: {e}"
    
    @staticmethod
    def audit_html_accessibility(path: str) -> str:
        """Basic accessibility audit for HTML."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            issues = []
            
            # Check for alt attributes on images
            img_without_alt = re.findall(r'<img(?![^>]*alt=)[^>]*>', html, re.IGNORECASE)
            if img_without_alt:
                issues.append(f"❌ {len(img_without_alt)} images missing alt attribute")
            
            # Check for form labels
            inputs = len(re.findall(r'<input[^>]*>', html, re.IGNORECASE))
            labels = len(re.findall(r'<label[^>]*>', html, re.IGNORECASE))
            if inputs > labels:
                issues.append(f"⚠️ {inputs} inputs but only {labels} labels")
            
            # Check for heading hierarchy
            headings = re.findall(r'<h([1-6])', html, re.IGNORECASE)
            if headings and headings[0] != '1':
                issues.append("⚠️ Page doesn't start with h1")
            
            # Check for language attribute
            if '<html' in html.lower() and 'lang=' not in html.lower():
                issues.append("❌ Missing lang attribute on <html>")
            
            # Check for skip link
            if 'skip' not in html.lower():
                issues.append("💡 Consider adding a 'skip to content' link")
            
            if issues:
                return "Accessibility Issues:\n" + "\n".join(issues)
            return "✅ No major accessibility issues found."
        except Exception as e:
            return f"Error auditing accessibility: {e}"


class TextToolbox:
    """Tools for text processing and NLP."""
    
    @staticmethod
    def summarize_text(text: str, sentences: int = 3) -> str:
        """Extract key sentences from text."""
        try:
            # Simple extractive summarization
            import re
            
            # Split into sentences
            sent_list = re.split(r'(?<=[.!?])\s+', text)
            
            if len(sent_list) <= sentences:
                return text
            
            # Score sentences by position and length
            scored = []
            for i, sent in enumerate(sent_list):
                score = 0
                # First and last sentences often important
                if i == 0 or i == len(sent_list) - 1:
                    score += 2
                # Medium length sentences preferred
                words = len(sent.split())
                if 10 <= words <= 30:
                    score += 1
                scored.append((score, i, sent))
            
            # Get top sentences, maintain order
            top = sorted(scored, key=lambda x: x[0], reverse=True)[:sentences]
            top = sorted(top, key=lambda x: x[1])
            
            return " ".join(s[2] for s in top)
        except Exception as e:
            return f"Error summarizing: {e}"
    
    @staticmethod
    def extract_keywords(text: str, top_n: int = 10) -> str:
        """Extract keywords from text."""
        from collections import Counter
        
        # Common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                      'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                      'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                      'should', 'may', 'might', 'must', 'it', 'its', 'this', 'that', 'these',
                      'those', 'i', 'you', 'he', 'she', 'we', 'they', 'what', 'which', 'who',
                      'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
                      'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
                      'own', 'same', 'so', 'than', 'too', 'very', 'can', 'just', 'into'}
        
        # Clean and tokenize
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        words = [w for w in words if w not in stop_words]
        
        counter = Counter(words)
        
        results = ["Keywords:", ""]
        for word, count in counter.most_common(top_n):
            results.append(f"  🔑 {word} ({count})")
        
        return "\n".join(results)
    
    @staticmethod
    def count_text_stats(text: str) -> str:
        """Count various text statistics."""
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        paragraphs = text.split('\n\n')
        
        chars = len(text)
        chars_no_space = len(text.replace(' ', '').replace('\n', ''))
        word_count = len(words)
        sentence_count = len([s for s in sentences if s.strip()])
        paragraph_count = len([p for p in paragraphs if p.strip()])
        
        avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Estimate reading time (200 words per minute)
        reading_time = word_count / 200
        
        return f"""Text Statistics:
  📝 Characters: {chars:,} ({chars_no_space:,} without spaces)
  📖 Words: {word_count:,}
  📄 Sentences: {sentence_count}
  📑 Paragraphs: {paragraph_count}
  📏 Avg word length: {avg_word_length:.1f} chars
  📐 Avg sentence length: {avg_sentence_length:.1f} words
  ⏱️ Reading time: ~{reading_time:.1f} minutes"""
    
    @staticmethod
    def grammar_check(text: str) -> str:
        """Basic grammar and style checks."""
        issues = []
        
        # Check for common issues
        patterns = [
            (r'\b(its|it\'s)\b', "Check its/it's usage"),
            (r'\b(their|there|they\'re)\b', "Check their/there/they're usage"),
            (r'\b(your|you\'re)\b', "Check your/you're usage"),
            (r'\s{2,}', "Multiple consecutive spaces"),
            (r'[.!?]{2,}', "Multiple punctuation marks"),
            (r'\bi\b', "Lowercase 'i' should be capitalized"),
            (r'\.\s*[a-z]', "Sentence starting with lowercase after period"),
        ]
        
        for pattern, description in patterns:
            matches = list(re.finditer(pattern, text))
            if matches:
                issues.append(f"⚠️ {description} ({len(matches)} occurrences)")
        
        # Check sentence length
        sentences = re.split(r'[.!?]+', text)
        long_sentences = [s for s in sentences if len(s.split()) > 35]
        if long_sentences:
            issues.append(f"📏 {len(long_sentences)} sentences over 35 words")
        
        # Passive voice detection (basic)
        passive = re.findall(r'\b(was|were|is|are|been|being)\s+\w+ed\b', text, re.IGNORECASE)
        if passive:
            issues.append(f"📝 Possible passive voice ({len(passive)} instances)")
        
        if issues:
            return "Grammar/Style Issues:\n" + "\n".join(issues)
        return "✅ No obvious grammar issues detected."


class NotificationToolbox:
    """Tools for sending notifications and webhooks."""
    
    @staticmethod
    def send_slack_message(webhook_url: str, message: str, channel: str = "") -> str:
        """Send a message to Slack via webhook."""
        try:
            import requests
        except ImportError:
            return "Error: requests not installed."
        
        try:
            payload = {"text": message}
            if channel:
                payload["channel"] = channel
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return "✅ Message sent to Slack successfully."
            return f"❌ Slack error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error sending to Slack: {e}"
    
    @staticmethod
    def send_discord_message(webhook_url: str, message: str, username: str = "Crytonix") -> str:
        """Send a message to Discord via webhook."""
        try:
            import requests
        except ImportError:
            return "Error: requests not installed."
        
        try:
            payload = {
                "content": message,
                "username": username
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code in (200, 204):
                return "✅ Message sent to Discord successfully."
            return f"❌ Discord error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error sending to Discord: {e}"
    
    @staticmethod
    def trigger_webhook(url: str, payload: Dict = None, method: str = "POST") -> str:
        """Trigger a generic webhook."""
        try:
            import requests
        except ImportError:
            return "Error: requests not installed."
        
        try:
            if method.upper() == "POST":
                response = requests.post(url, json=payload or {}, timeout=10)
            elif method.upper() == "GET":
                response = requests.get(url, params=payload or {}, timeout=10)
            else:
                return f"Unsupported method: {method}"
            
            return f"Webhook response: {response.status_code}\n{response.text[:500]}"
        except Exception as e:
            return f"Error triggering webhook: {e}"
    
    @staticmethod
    def send_desktop_notification(title: str, message: str) -> str:
        """Send a desktop notification (Windows/Mac/Linux)."""
        import platform
        
        system = platform.system()
        
        try:
            if system == "Windows":
                try:
                    from win10toast import ToastNotifier
                    toast = ToastNotifier()
                    toast.show_toast(title, message, duration=5)
                    return "✅ Notification sent."
                except ImportError:
                    return Toolbox.run_command(f'powershell -Command "New-BurntToastNotification -Text \\"{title}\\", \\"{message}\\""')
            elif system == "Darwin":  # macOS
                return Toolbox.run_command(f'osascript -e \'display notification "{message}" with title "{title}"\'')
            else:  # Linux
                return Toolbox.run_command(f'notify-send "{title}" "{message}"')
        except Exception as e:
            return f"Error sending notification: {e}"


class TimeTrackingToolbox:
    """Tools for time tracking and task management."""
    
    TRACKING_PATH = os.path.expanduser("~/.crytonix/time_tracking.json")
    
    @staticmethod
    def _load_tracking() -> dict:
        if os.path.exists(TimeTrackingToolbox.TRACKING_PATH):
            with open(TimeTrackingToolbox.TRACKING_PATH, 'r') as f:
                return json.load(f)
        return {"current": None, "sessions": [], "todos": []}
    
    @staticmethod
    def _save_tracking(data: dict):
        os.makedirs(os.path.dirname(TimeTrackingToolbox.TRACKING_PATH), exist_ok=True)
        with open(TimeTrackingToolbox.TRACKING_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def start_timer(task_name: str) -> str:
        """Start tracking time for a task."""
        import datetime
        
        tracking = TimeTrackingToolbox._load_tracking()
        
        if tracking["current"]:
            return f"Timer already running for '{tracking['current']['task']}'. Stop it first."
        
        tracking["current"] = {
            "task": task_name,
            "started": datetime.datetime.now().isoformat()
        }
        
        TimeTrackingToolbox._save_tracking(tracking)
        return f"⏱️ Timer started for '{task_name}'"
    
    @staticmethod
    def stop_timer() -> str:
        """Stop the current timer and log time."""
        import datetime
        
        tracking = TimeTrackingToolbox._load_tracking()
        
        if not tracking["current"]:
            return "No timer is currently running."
        
        start = datetime.datetime.fromisoformat(tracking["current"]["started"])
        end = datetime.datetime.now()
        duration = (end - start).total_seconds() / 60  # minutes
        
        session = {
            "task": tracking["current"]["task"],
            "started": tracking["current"]["started"],
            "ended": end.isoformat(),
            "duration_minutes": round(duration, 2)
        }
        
        tracking["sessions"].append(session)
        task_name = tracking["current"]["task"]
        tracking["current"] = None
        
        TimeTrackingToolbox._save_tracking(tracking)
        return f"⏹️ Timer stopped for '{task_name}'\n   Duration: {duration:.1f} minutes"
    
    @staticmethod
    def get_time_report(days: int = 7) -> str:
        """Get time tracking report for the past N days."""
        import datetime
        from collections import defaultdict
        
        tracking = TimeTrackingToolbox._load_tracking()
        
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        
        by_task = defaultdict(float)
        by_day = defaultdict(float)
        
        for session in tracking["sessions"]:
            started = datetime.datetime.fromisoformat(session["started"])
            if started >= cutoff:
                by_task[session["task"]] += session["duration_minutes"]
                day = started.strftime("%Y-%m-%d")
                by_day[day] += session["duration_minutes"]
        
        results = [f"Time Report (Last {days} days):", ""]
        
        if by_task:
            results.append("By Task:")
            for task, minutes in sorted(by_task.items(), key=lambda x: x[1], reverse=True):
                hours = minutes / 60
                results.append(f"  📋 {task}: {hours:.1f}h ({minutes:.0f}m)")
            
            results.append("\nBy Day:")
            for day, minutes in sorted(by_day.items()):
                hours = minutes / 60
                results.append(f"  📅 {day}: {hours:.1f}h")
            
            total_hours = sum(by_task.values()) / 60
            results.append(f"\nTotal: {total_hours:.1f} hours")
        else:
            results.append("No time tracked in this period.")
        
        return "\n".join(results)
    
    @staticmethod
    def create_todo(task: str, priority: str = "medium") -> str:
        """Add a task to the todo list."""
        import datetime
        
        tracking = TimeTrackingToolbox._load_tracking()
        
        todo = {
            "task": task,
            "priority": priority,
            "created": datetime.datetime.now().isoformat(),
            "completed": False
        }
        
        tracking["todos"].append(todo)
        TimeTrackingToolbox._save_tracking(tracking)
        
        return f"✅ Added todo: {task} (priority: {priority})"
    
    @staticmethod
    def list_todos(show_completed: bool = False) -> str:
        """List all todos."""
        tracking = TimeTrackingToolbox._load_tracking()
        
        todos = tracking.get("todos", [])
        
        if not show_completed:
            todos = [t for t in todos if not t.get("completed")]
        
        if not todos:
            return "No pending todos."
        
        priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        
        results = ["Todo List:", ""]
        for i, todo in enumerate(todos):
            icon = priority_icons.get(todo.get("priority", "medium"), "⚪")
            status = "✅" if todo.get("completed") else "⬜"
            results.append(f"  {status} {icon} [{i}] {todo['task']}")
        
        return "\n".join(results)
    
    @staticmethod
    def complete_todo(index: int) -> str:
        """Mark a todo as completed."""
        tracking = TimeTrackingToolbox._load_tracking()
        
        if 0 <= index < len(tracking.get("todos", [])):
            tracking["todos"][index]["completed"] = True
            task = tracking["todos"][index]["task"]
            TimeTrackingToolbox._save_tracking(tracking)
            return f"✅ Completed: {task}"
        
        return f"Invalid todo index: {index}"


class DependencyToolbox:
    """Tools for dependency management."""
    
    @staticmethod
    def check_outdated() -> str:
        """List outdated Python packages."""
        import shutil
        
        if not shutil.which("pip"):
            return "Error: pip not found."
        
        result = Toolbox.run_command("pip list --outdated --format=columns")
        return f"Outdated Packages:\n{result}" if result.strip() else "All packages are up to date."
    
    @staticmethod
    def update_package(name: str) -> str:
        """Update a specific package."""
        return Toolbox.run_command(f"pip install --upgrade {name}")
    
    @staticmethod
    def generate_requirements(path: str = ".") -> str:
        """Generate requirements.txt from imports in codebase."""
        import ast
        
        imports = set()
        
        # Common mapping of import names to package names
        import_to_package = {
            'PIL': 'Pillow',
            'cv2': 'opencv-python',
            'sklearn': 'scikit-learn',
            'yaml': 'PyYAML',
            'bs4': 'beautifulsoup4',
        }
        
        try:
            for root, _, files in os.walk(path):
                if ".git" in root or "__pycache__" in root or "venv" in root:
                    continue
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                tree = ast.parse(f.read())
                            
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for alias in node.names:
                                        imports.add(alias.name.split('.')[0])
                                elif isinstance(node, ast.ImportFrom):
                                    if node.module:
                                        imports.add(node.module.split('.')[0])
                        except:
                            pass
            
            # Filter stdlib
            stdlib = {'os', 'sys', 'json', 're', 'typing', 'abc', 'collections', 
                      'datetime', 'time', 'threading', 'queue', 'io', 'pathlib',
                      'functools', 'itertools', 'subprocess', 'glob', 'shutil',
                      'unittest', 'argparse', 'logging', 'random', 'math', 'string',
                      'hashlib', 'base64', 'struct', 'copy', 'operator', 'contextlib',
                      'tempfile', 'platform', 'traceback', 'warnings', 'importlib',
                      'ast', 'difflib', 'textwrap', 'html', 'xml', 'email', 'http',
                      'urllib', 'socket', 'sqlite3', 'csv', 'pickle', 'shelve',
                      'gzip', 'zipfile', 'tarfile', 'configparser', 'secrets',
                      'concurrent', 'asyncio', 'multiprocessing', 'ctypes', 'array',
                      'dataclasses', 'enum', 'numbers', 'decimal', 'fractions',
                      'statistics', 'calendar', 'locale', 'gettext', 'codecs'}
            
            external = sorted(imports - stdlib)
            
            # Map to package names
            packages = []
            for imp in external:
                pkg = import_to_package.get(imp, imp)
                packages.append(pkg)
            
            if packages:
                return "# Auto-generated requirements\n" + "\n".join(packages)
            return "No external dependencies found."
        except Exception as e:
            return f"Error generating requirements: {e}"
    
    @staticmethod
    def compare_requirements(file1: str, file2: str) -> str:
        """Compare two requirements files."""
        def parse_reqs(path):
            reqs = {}
            if os.path.exists(path):
                with open(path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Parse package==version or package>=version etc.
                            match = re.match(r'([a-zA-Z0-9_-]+)([<>=!]+)?(.+)?', line)
                            if match:
                                reqs[match.group(1).lower()] = line
            return reqs
        
        try:
            reqs1 = parse_reqs(file1)
            reqs2 = parse_reqs(file2)
            
            all_packages = set(reqs1.keys()) | set(reqs2.keys())
            
            results = ["Requirements Comparison:", ""]
            for pkg in sorted(all_packages):
                in1 = pkg in reqs1
                in2 = pkg in reqs2
                
                if in1 and in2:
                    if reqs1[pkg] != reqs2[pkg]:
                        results.append(f"⚡ {pkg}: {reqs1[pkg]} vs {reqs2[pkg]}")
                elif in1:
                    results.append(f"➖ {pkg}: only in {file1}")
                else:
                    results.append(f"➕ {pkg}: only in {file2}")
            
            return "\n".join(results) if len(results) > 2 else "Requirements are identical."
        except Exception as e:
            return f"Error comparing requirements: {e}"
    
    @staticmethod
    def find_unused_deps(requirements_file: str = "requirements.txt", path: str = ".") -> str:
        """Find dependencies in requirements.txt that aren't imported."""
        import ast
        
        # Get all imports
        imports = set()
        
        import_to_package = {
            'pillow': 'PIL',
            'opencv-python': 'cv2',
            'scikit-learn': 'sklearn',
            'pyyaml': 'yaml',
            'beautifulsoup4': 'bs4',
        }
        
        try:
            for root, _, files in os.walk(path):
                if ".git" in root or "__pycache__" in root or "venv" in root:
                    continue
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                tree = ast.parse(f.read())
                            
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for alias in node.names:
                                        imports.add(alias.name.split('.')[0].lower())
                                elif isinstance(node, ast.ImportFrom):
                                    if node.module:
                                        imports.add(node.module.split('.')[0].lower())
                        except:
                            pass
            
            # Parse requirements
            unused = []
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        match = re.match(r'([a-zA-Z0-9_-]+)', line)
                        if match:
                            pkg = match.group(1).lower()
                            # Check if imported
                            import_name = import_to_package.get(pkg, pkg).lower()
                            if import_name not in imports and pkg not in imports:
                                unused.append(pkg)
            
            if unused:
                return "Potentially unused dependencies:\n" + "\n".join(f"  ⚠️ {pkg}" for pkg in unused)
            return "All dependencies appear to be used."
        except Exception as e:
            return f"Error analyzing dependencies: {e}"



class HealthToolbox:
    """Tools for developer health and wellness."""

    @staticmethod
    def check_posture() -> str:
        """Reminds the user to check their posture."""
        return "🧘 check_posture: Sit up straight! Shoulders back, feet flat on the floor. Your future self will thank you."

    @staticmethod
    def stretch_exercise() -> str:
        """Suggests a quick stretching exercise."""
        import random
        stretches = [
            "Neck Roll: Gently roll your head in a circle.",
            "Shoulder Shrug: Lift shoulders to ears, hold, drop.",
            "Wrist Flex: Extend arm, pull fingers back gently.",
            "Spinal Twist: Turn your torso to the left, then right.",
            "Hamstring Stretch: Reach for your toes (carefully!)."
        ]
        return f"🤸 stretch_exercise: {random.choice(stretches)}"

    @staticmethod
    def hydration_reminder() -> str:
        """Reminds the user to drink water."""
        return "💧 hydration_reminder: Time to hydrate! Grab a glass of water."

    @staticmethod
    def take_break(duration_minutes: int = 5) -> str:
        """Suggests taking a break."""
        return f"☕ take_break: You've been working hard. Take a {duration_minutes}-minute break to rest your eyes and mind."


class NetworkToolbox:
    """Tools for network diagnostics."""

    @staticmethod
    def ping(host: str, count: int = 4) -> str:
        """Pings a host."""
        import platform
        import subprocess

        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, str(count), host]

        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, shell=False)
            return result.stdout
        except subprocess.CalledProcessError as e:
            return f"Ping failed: {e.stderr}"
        except Exception as e:
            return f"Error pinging {host}: {e}"

    @staticmethod
    def check_port(host: str, port: int, timeout: int = 3) -> str:
        """Checks if a TCP port is open."""
        import socket

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                if result == 0:
                    return f"✅ Port {port} on {host} is OPEN."
                else:
                    return f"❌ Port {port} on {host} is CLOSED (Code: {result})."
        except Exception as e:
            return f"Error checking port: {e}"

    @staticmethod
    def dns_lookup(host: str) -> str:
        """Performs a DNS lookup."""
        import socket

        try:
            ip = socket.gethostbyname(host)
            return f"🌐 DNS Lookup: {host} -> {ip}"
        except Exception as e:
            return f"Error resolving {host}: {e}"
