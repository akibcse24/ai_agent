from crytonix.tools.core import Toolbox
import shutil
import os

class DevOpsToolbox:
    @staticmethod
    def _check_docker() -> bool: return shutil.which("docker") is not None

    @staticmethod
    def docker_build(tag: str, dockerfile: str = ".") -> str:
        if not DevOpsToolbox._check_docker(): return "Error: Docker not installed."
        return Toolbox.run_command(f"docker build -t {tag} {dockerfile}")

    @staticmethod
    def docker_run(image: str, ports: str = "") -> str:
        if not DevOpsToolbox._check_docker(): return "Error: Docker not installed."
        p = f"-p {ports}" if ports else ""
        return Toolbox.run_command(f"docker run -d {p} {image}")

    @staticmethod
    def list_containers() -> str:
        if not DevOpsToolbox._check_docker(): return "Error: Docker not installed."
        return Toolbox.run_command("docker ps -a")

    @staticmethod
    def read_logs(container: str) -> str:
        if not DevOpsToolbox._check_docker(): return "Error: Docker not installed."
        return Toolbox.run_command(f"docker logs --tail 50 {container}")

class EnvironmentToolbox:
    @staticmethod
    def check_env_vars(required: list) -> str:
        missing = [v for v in required if not os.environ.get(v)]
        return f"Missing: {missing}" if missing else "All present."

    @staticmethod
    def validate_json_config(path: str) -> str:
        try:
            import json
            with open(path) as f: json.load(f)
            return "Valid JSON"
        except Exception as e: return f"Invalid: {e}"
