import os
import shutil
import re
import ast
from crytonix.tools.core import Toolbox

class CodeAnalysisToolbox:
    @staticmethod
    def analyze_code_complexity(path: str) -> str:
        try:
            from radon.complexity import cc_visit
            from radon.raw import analyze
        except ImportError:
            return "Error: radon not installed."

        try:
            with open(path, 'r', encoding='utf-8') as f: code = f.read()
            cc_results = cc_visit(code)
            raw_analysis = analyze(code)
            output = [f"=== Code Analysis: {path} ===", f"LOC: {raw_analysis.loc}, SLOC: {raw_analysis.sloc}"]
            for block in cc_results:
                output.append(f"{block.name} ({block.lineno}): {block.complexity}")
            return "\n".join(output)
        except Exception as e:
            return f"Error analyzing complexity: {e}"

    @staticmethod
    def find_dependencies(path: str = ".") -> str:
        imports = set()
        for root, _, files in os.walk(path):
            if ".git" in root or "venv" in root: continue
            for file in files:
                if file.endswith('.py'):
                    try:
                        with open(os.path.join(root, file), 'r') as f:
                            tree = ast.parse(f.read())
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for n in node.names: imports.add(n.name.split('.')[0])
                                elif isinstance(node, ast.ImportFrom):
                                    if node.module: imports.add(node.module.split('.')[0])
                    except: pass
        return f"Found: {', '.join(sorted(imports))}"

    @staticmethod
    def lint_code(path: str) -> str:
        if shutil.which("ruff"): return Toolbox.run_command(f"ruff check {path}")
        if shutil.which("pylint"): return Toolbox.run_command(f"pylint {path}")
        return "Error: No linter installed."

    @staticmethod
    def detect_code_smells(path: str) -> str:
        smells = []
        try:
            with open(path, 'r') as f: code = f.read()
            lines = code.splitlines()
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if (node.end_lineno - node.lineno) > 50:
                        smells.append(f"Long function: {node.name}")
                    if len(node.args.args) > 5:
                        smells.append(f"Too many args: {node.name}")
            return "\n".join(smells) if smells else "No smells."
        except Exception as e: return f"Error: {e}"

class RefactoringToolbox:
    @staticmethod
    def rename_symbol(path: str, old: str, new: str) -> str:
        try:
            with open(path, 'r') as f: content = f.read()
            if old not in content: return f"Symbol {old} not found."
            new_content = content.replace(old, new)
            Toolbox._show_diff(new_content, content, path)
            # Non-interactive for safety in this refactor
            return "Refactor preview shown. Use write_file to apply."
        except Exception as e: return f"Error: {e}"
