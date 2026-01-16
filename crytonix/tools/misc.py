from crytonix.tools.core import Toolbox
import os
import glob
import re
import json
from typing import List, Dict

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
        if value >= 8 and effort <= 5: return "Must Have"
        if value >= 6 and effort <= 8: return "Should Have"
        if value >= 4: return "Could Have"
        return "Won't Have"

class DesignToolbox:
    @staticmethod
    def check_contrast_ratio(hex1: str, hex2: str) -> str:
        """Calculates contrast ratio between two hex colors."""
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

class DependencyToolbox:
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
                        except: pass

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
            packages = [import_to_package.get(imp, imp) for imp in external]

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
                elif in1: results.append(f"➖ {pkg}: only in {file1}")
                else: results.append(f"➕ {pkg}: only in {file2}")
            return "\n".join(results) if len(results) > 2 else "Requirements are identical."
        except Exception as e: return f"Error comparing requirements: {e}"

    @staticmethod
    def find_unused_deps(requirements_file: str = "requirements.txt", path: str = ".") -> str:
        """Find dependencies in requirements.txt that aren't imported."""
        import ast
        imports = set()
        import_to_package = {'pillow': 'PIL', 'opencv-python': 'cv2', 'scikit-learn': 'sklearn', 'pyyaml': 'yaml', 'beautifulsoup4': 'bs4'}
        try:
            for root, _, files in os.walk(path):
                if ".git" in root or "__pycache__" in root or "venv" in root: continue
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                tree = ast.parse(f.read())
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for alias in node.names: imports.add(alias.name.split('.')[0].lower())
                                elif isinstance(node, ast.ImportFrom):
                                    if node.module: imports.add(node.module.split('.')[0].lower())
                        except: pass
            unused = []
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        match = re.match(r'([a-zA-Z0-9_-]+)', line)
                        if match:
                            pkg = match.group(1).lower()
                            import_name = import_to_package.get(pkg, pkg).lower()
                            if import_name not in imports and pkg not in imports:
                                unused.append(pkg)
            if unused: return "Potentially unused dependencies:\n" + "\n".join(f"  ⚠️ {pkg}" for pkg in unused)
            return "All dependencies appear to be used."
        except Exception as e: return f"Error analyzing dependencies: {e}"

class TestingToolbox:
    @staticmethod
    def run_tests(path: str = ".", verbose: bool = True) -> str:
        import shutil
        if not shutil.which("pytest"): return "Error: pytest not installed. Run `pip install pytest`."
        cmd = f"python -m pytest {path} {'-v' if verbose else ''} --tb=short"
        return Toolbox.run_command(cmd)

    @staticmethod
    def run_specific_test(test_path: str) -> str:
        import shutil
        if not shutil.which("pytest"): return "Error: pytest not installed."
        return Toolbox.run_command(f"python -m pytest {test_path} -v")

    @staticmethod
    def check_test_coverage(path: str = ".") -> str:
        import shutil
        if not shutil.which("coverage"): return "Error: coverage not installed. Run `pip install coverage`."
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
        except Exception as e: return f"Error generating test skeleton: {e}"

class DatabaseToolbox:
    @staticmethod
    def query_sqlite(db_path: str, query: str) -> str:
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
                if len(rows) > 50: result.append(f"... ({len(rows) - 50} more rows)")
                conn.close()
                return "\n".join(result)
            else:
                conn.commit()
                affected = cursor.rowcount
                conn.close()
                return f"Query executed. Rows affected: {affected}"
        except Exception as e: return f"Database error: {e}"

    @staticmethod
    def make_api_request(url: str, method: str = "GET", data: dict = None, headers: dict = None) -> str:
        try:
            import requests
        except ImportError: return "Error: requests not installed."
        try:
            method = method.upper()
            kwargs = {'timeout': 10}
            if headers: kwargs['headers'] = headers
            if data: kwargs['json'] = data
            if method == "GET": response = requests.get(url, **kwargs)
            elif method == "POST": response = requests.post(url, **kwargs)
            elif method == "PUT": response = requests.put(url, **kwargs)
            elif method == "DELETE": response = requests.delete(url, **kwargs)
            else: return f"Unsupported method: {method}"
            return f"Status: {response.status_code}\nBody:\n{response.text[:3000]}"
        except Exception as e: return f"API request error: {e}"

    @staticmethod
    def parse_json_response(json_string: str, path: str = "") -> str:
        import json as json_lib
        try:
            data = json_lib.loads(json_string)
            if path:
                parts = re.split(r'\.|\[|\]', path)
                parts = [p for p in parts if p]
                for part in parts:
                    if part.isdigit(): data = data[int(part)]
                    else: data = data[part]
            return json_lib.dumps(data, indent=2)
        except Exception as e: return f"JSON parsing error: {e}"

class DocumentationToolbox:
    @staticmethod
    def generate_readme(path: str = ".") -> str:
        try:
            project_name = os.path.basename(os.path.abspath(path))
            files = os.listdir(path)
            has_python = any(f.endswith('.py') for f in files)
            has_package_json = 'package.json' in files
            has_requirements = 'requirements.txt' in files

            readme = [f"# {project_name.title()}", "", "## Description", "TODO: Add project description", "", "## Installation"]
            if has_python:
                readme.append("```bash")
                if has_requirements: readme.append("pip install -r requirements.txt")
                else: readme.append("pip install .")
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
        except Exception as e: return f"Error generating README: {e}"

    @staticmethod
    def extract_api_docs(source_file: str) -> str:
        import ast
        try:
            with open(source_file, 'r', encoding='utf-8') as f: tree = ast.parse(f.read())
            docs = [f"# API Documentation: {os.path.basename(source_file)}", ""]
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    docs.append(f"## class `{node.name}`")
                    if ast.get_docstring(node): docs.append(ast.get_docstring(node))
                    docs.append("")
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            args = [a.arg for a in item.args.args if a.arg != 'self']
                            docs.append(f"### `{item.name}({', '.join(args)})`")
                            if ast.get_docstring(item): docs.append(ast.get_docstring(item))
                            docs.append("")
                elif isinstance(node, ast.FunctionDef):
                    args = [a.arg for a in node.args.args]
                    docs.append(f"## `{node.name}({', '.join(args)})`")
                    if ast.get_docstring(node): docs.append(ast.get_docstring(node))
                    docs.append("")
            return "\n".join(docs)
        except Exception as e: return f"Error extracting docs: {e}"

    @staticmethod
    def create_changelog(commits: int = 20) -> str:
        result = Toolbox.run_command(f"git log --oneline -n {commits}")
        changelog = ["# Changelog", ""]
        for line in result.strip().split('\n'):
            if line:
                parts = line.split(' ', 1)
                if len(parts) == 2: changelog.append(f"- {parts[1]} ({parts[0][:7]})")
        return "\n".join(changelog)

    @staticmethod
    def generate_mermaid_diagram(source_file: str) -> str:
        import ast
        try:
            with open(source_file, 'r', encoding='utf-8') as f: tree = ast.parse(f.read())
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
                    for base in node.bases:
                        if isinstance(base, ast.Name): lines.append(f"    {base.id} <|-- {node.name}")
            lines.append("```")
            return "\n".join(lines)
        except Exception as e: return f"Error generating diagram: {e}"

class SecurityToolbox:
    @staticmethod
    def scan_vulnerabilities(path: str = ".") -> str:
        import shutil
        if not shutil.which("bandit"): return "Error: bandit not installed."
        result = Toolbox.run_command(f"bandit -r {path} -f txt -ll")
        return f"Security Scan Results:\n{result}" if result else "No vulnerabilities found."

    @staticmethod
    def check_secrets(path: str = ".") -> str:
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
                if ".git" in root or "node_modules" in root: continue
                for file in files:
                    if file.endswith(('.py', '.js', '.ts', '.json', '.yaml', '.yml', '.env')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                for secret_type, pattern in patterns.items():
                                    if re.search(pattern, content):
                                        findings.append(f"[{secret_type}] Found in {file_path}")
                        except: pass
            return "\n".join(findings) if findings else "No secrets detected."
        except Exception as e: return f"Error scanning for secrets: {e}"

class MemoryToolbox:
    MEMORY_PATH = os.path.expanduser("~/.crytonix/memory.json")

    @staticmethod
    def _load_memory() -> dict:
        if os.path.exists(MemoryToolbox.MEMORY_PATH):
            try:
                with open(MemoryToolbox.MEMORY_PATH, 'r') as f:
                    content = f.read().strip()
                    if content: return json.loads(content)
            except (json.JSONDecodeError, IOError): pass
        return {"snippets": {}, "notes": []}

    @staticmethod
    def _save_memory(data: dict):
        os.makedirs(os.path.dirname(MemoryToolbox.MEMORY_PATH), exist_ok=True)
        with open(MemoryToolbox.MEMORY_PATH, 'w') as f: json.dump(data, f, indent=2)

    @staticmethod
    def save_snippet(name: str, content: str, tags: str = "") -> str:
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
        memory = MemoryToolbox._load_memory()
        snippets = memory.get("snippets", {})
        if name:
            if name in snippets: return f"=== {name} ===\n{snippets[name]['content']}"
            return f"Snippet '{name}' not found."
        if tag:
            matches = [(k, v) for k, v in snippets.items() if tag in v.get('tags', [])]
            if matches: return "\n\n".join(f"=== {k} ===\n{v['content']}" for k, v in matches)
            return f"No snippets found with tag '{tag}'."
        if snippets:
            return "Saved Snippets:\n" + "\n".join(f"  - {k} (tags: {','.join(v.get('tags', []))})" for k, v in snippets.items())
        return "No snippets saved yet."

class AssetToolbox:
    @staticmethod
    def optimize_image(path: str, quality: int = 85, max_size: int = 1024) -> str:
        try:
            from PIL import Image
        except ImportError: return "Error: Pillow not installed."
        try:
            img = Image.open(path)
            original_size = os.path.getsize(path)
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            output_path = path.rsplit('.', 1)[0] + '_optimized.' + path.rsplit('.', 1)[1]
            img.save(output_path, quality=quality, optimize=True)
            new_size = os.path.getsize(output_path)
            reduction = (1 - new_size / original_size) * 100
            return f"Optimized: {output_path}\nSize: {original_size}B -> {new_size}B ({reduction:.1f}% reduction)"
        except Exception as e: return f"Error optimizing image: {e}"

class ScaffoldToolbox:
    @staticmethod
    def create_python_project(name: str, style: str = "basic") -> str:
        try:
            base = os.path.join(".", name)
            os.makedirs(base, exist_ok=True)
            os.makedirs(os.path.join(base, name.replace("-", "_")), exist_ok=True)
            os.makedirs(os.path.join(base, "tests"), exist_ok=True)
            init_path = os.path.join(base, name.replace("-", "_"), "__init__.py")
            with open(init_path, 'w') as f:
                f.write(f'"""{ name} package."""\n__version__ = "0.1.0"\n')
            pyproject = f'''[project]\nname = "{name}"\nversion = "0.1.0"\ndescription = "A Python project"\nrequires-python = ">=3.9"\ndependencies = []\n\n[project.optional-dependencies]\ndev = ["pytest", "black", "ruff"]\n'''
            with open(os.path.join(base, "pyproject.toml"), 'w') as f: f.write(pyproject)
            with open(os.path.join(base, "README.md"), 'w') as f: f.write(f"# {name}\n\nA Python project.\n")
            with open(os.path.join(base, ".gitignore"), 'w') as f: f.write("__pycache__/\n*.pyc\n.venv/\ndist/\n*.egg-info/\n")
            return f"Python project '{name}' created at ./{name}/"
        except Exception as e: return f"Error creating project: {e}"

class MonitoringToolbox:
    @staticmethod
    def parse_logs(path: str, pattern: str, limit: int = 50) -> str:
        try:
            matches = []
            regex = re.compile(pattern, re.IGNORECASE)
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if regex.search(line):
                        matches.append(f"{i}: {line.strip()[:150]}")
                        if len(matches) >= limit: break
            if matches: return f"Found {len(matches)} matches:\n" + "\n".join(matches)
            return "No matches found."
        except Exception as e: return f"Error parsing logs: {e}"

class TimeTrackingToolbox:
    TRACKING_PATH = os.path.expanduser("~/.crytonix/time_tracking.json")
    @staticmethod
    def _load_tracking() -> dict:
        if os.path.exists(TimeTrackingToolbox.TRACKING_PATH):
            with open(TimeTrackingToolbox.TRACKING_PATH, 'r') as f: return json.load(f)
        return {"current": None, "sessions": [], "todos": []}

    @staticmethod
    def _save_tracking(data: dict):
        os.makedirs(os.path.dirname(TimeTrackingToolbox.TRACKING_PATH), exist_ok=True)
        with open(TimeTrackingToolbox.TRACKING_PATH, 'w') as f: json.dump(data, f, indent=2)

    @staticmethod
    def start_timer(task_name: str) -> str:
        import datetime
        tracking = TimeTrackingToolbox._load_tracking()
        if tracking["current"]: return f"Timer already running for '{tracking['current']['task']}'."
        tracking["current"] = {"task": task_name, "started": datetime.datetime.now().isoformat()}
        TimeTrackingToolbox._save_tracking(tracking)
        return f"⏱️ Timer started for '{task_name}'"

class MigrationToolbox:
    @staticmethod
    def list_migrations(migrations_dir: str = "migrations") -> str:
        try:
            if not os.path.exists(migrations_dir): return f"No migrations directory found at {migrations_dir}"
            files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
            if not files: return "No migrations found."
            results = ["Migrations:", ""]
            for f in files: results.append(f"  📄 {os.path.basename(f)}")
            return "\n".join(results)
        except Exception as e: return f"Error listing migrations: {e}"

class AIToolbox:
    @staticmethod
    def count_tokens(text: str, model: str = "gpt-4") -> str:
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(model)
            tokens = encoding.encode(text)
            return f"Token count: {len(tokens)} (model: {model})"
        except ImportError:
            words = len(text.split())
            estimated = max(words * 1.3, len(text) / 4)
            return f"Estimated tokens: ~{int(estimated)} (install tiktoken for accuracy)"

class PerformanceToolbox:
    @staticmethod
    def profile_code(path: str) -> str:
        import cProfile, pstats
        from io import StringIO
        try:
            with open(path, 'r', encoding='utf-8') as f: code = f.read()
            profiler = cProfile.Profile()
            profiler.enable()
            try: exec(compile(code, path, 'exec'), {'__name__': '__main__'})
            except Exception as e: pass
            profiler.disable()
            stream = StringIO()
            stats = pstats.Stats(profiler, stream=stream)
            stats.sort_stats('cumulative')
            stats.print_stats(20)
            return f"Profile Results for {path}:\n{stream.getvalue()}"
        except Exception as e: return f"Error profiling code: {e}"

class FrontendToolbox:
    @staticmethod
    def validate_css(path: str) -> str:
        try:
            with open(path, 'r', encoding='utf-8') as f: css = f.read()
            issues = []
            if css.count('{') != css.count('}'): issues.append("⚠️ Mismatched braces")
            if issues: return "\n".join(issues)
            return f"✅ {path} appears valid."
        except Exception as e: return f"Error validating CSS: {e}"

class NotificationToolbox:
    @staticmethod
    def send_slack_message(webhook_url: str, message: str) -> str:
        try:
            import requests
            response = requests.post(webhook_url, json={"text": message}, timeout=10)
            if response.status_code == 200: return "✅ Message sent to Slack."
            return f"❌ Slack error: {response.status_code}"
        except Exception as e: return f"Error sending to Slack: {e}"

class TextToolbox:
    @staticmethod
    def summarize_text(text: str, sentences: int = 3) -> str:
        return text[:500] + "..." # Simplified logic as placeholder for now, original was regex based
