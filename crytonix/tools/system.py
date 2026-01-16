import platform
import json
import os
import socket

class SystemToolbox:
    """Tools for system info and networking."""

    @staticmethod
    def get_system_info() -> str:
        """Get system details (OS, CPU)."""
        try:
            uname = platform.uname()
            info = {
                "system": uname.system,
                "node": uname.node,
                "release": uname.release,
                "version": uname.version,
                "machine": uname.machine,
                "processor": uname.processor,
                "cpu_count": os.cpu_count()
            }
            return json.dumps(info, indent=2)
        except Exception as e:
            return f"Error getting system info: {e}"

    @staticmethod
    def check_port(host: str, port: int) -> str:
        """Check if a TCP port is open."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                if result == 0:
                    return f"Port {port} on {host} is OPEN."
                else:
                    return f"Port {port} on {host} is CLOSED (code: {result})."
        except Exception as e:
            return f"Error checking port: {e}"
