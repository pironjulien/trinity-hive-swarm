import os
import subprocess
import glob

class Toolkit:
    """Standard Tool Library for Antigravity V2 Workers. Gives 'Hands' to the AI Brain."""

    def read_file(self, path):
        try:
            if not os.path.exists(path):
                return "File not found."
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {path}: {e}"

    def write_file(self, path, content):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file {path}: {e}"

    def list_dir(self, path="."):
        try:
            return str(os.listdir(path))
        except Exception as e:
            return f"Error listing directory {path}: {e}"

    def run_command(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except Exception as e:
            return f"Error executing command: {e}"

    def project_tree(self, path="."):
        tree = []
        exclude = {'.git', '__pycache__', '.venv', 'node_modules', 'dist'}
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in exclude]
            level = root.replace(path, '').count(os.sep)
            indent = ' ' * 4 * (level)
            tree.append(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                tree.append(f"{subindent}{f}")
        return "\n".join(tree)
