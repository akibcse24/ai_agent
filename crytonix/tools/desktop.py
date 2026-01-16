import platform
import subprocess
import webbrowser

class DesktopToolbox:
    """Tools for desktop interaction."""

    @staticmethod
    def open_app(app_name: str) -> str:
        """Launches an application."""
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.Popen(["open", "-a", app_name])
            elif system == "Windows":
                subprocess.Popen(["start", app_name], shell=True)
            else:
                subprocess.Popen([app_name], shell=True)
            return f"Launched application: {app_name}"
        except Exception as e:
            return f"Error launching app: {e}"

    @staticmethod
    def control_media(action: str) -> str:
        try:
            import pyautogui
            valid = ["playpause", "volumeup", "volumedown", "nexttrack", "prevtrack", "mute"]
            if action not in valid:
                return f"Invalid action. Choose from: {', '.join(valid)}"
            pyautogui.press(action)
            return f"Media action executed: {action}"
        except ImportError:
            return "Error: pyautogui not installed."
        except Exception as e:
            return f"Error controlling media: {e}"

    @staticmethod
    def set_volume(level: int) -> str:
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.run(f"osascript -e 'set volume output volume {level}'", shell=True)
            elif system == "Linux":
                subprocess.run(f"amixer -D pulse sset Master {level}%", shell=True)
            return f"Volume set to {level}%"
        except Exception as e:
            return f"Error setting volume: {e}"

    @staticmethod
    def browser_open(url: str) -> str:
        try:
            webbrowser.open(url)
            return f"Opened URL: {url}"
        except Exception as e:
            return f"Error opening browser: {e}"

    @staticmethod
    def clipboard_action(action: str, text: str = "") -> str:
        try:
            import pyperclip
            if action == "copy":
                pyperclip.copy(text)
                return "Text copied to clipboard."
            elif action == "paste":
                return f"Clipboard content:\n{pyperclip.paste()}"
            return "Invalid action."
        except ImportError:
            return "Error: pyperclip not installed."
        except Exception as e:
            if "Pyperclip could not find a copy/paste mechanism" in str(e):
                return "Error: No system clipboard found."
            return f"Clipboard error: {e}"

class AutomationToolbox:
    """Tools for automation."""

    @staticmethod
    def type_text(text: str, interval: float = 0.0) -> str:
        try:
            import pyautogui
            pyautogui.write(text, interval=interval)
            return "Text typed successfully."
        except ImportError:
            return "Error: pyautogui not installed."
        except Exception as e:
            if "DISPLAY" in str(e) or "application is not allowed" in str(e):
                return "Error: Unable to type text (Headless environment?)"
            return f"Error typing text: {e}"

    @staticmethod
    def take_screenshot(filename: str = "screenshot.png") -> str:
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            return f"Screenshot saved to {filename}"
        except ImportError:
            return "Error: pyautogui not installed."
        except Exception as e:
            if "DISPLAY" in str(e):
                return "Error: Unable to take screenshot (Headless environment?)"
            return f"Error taking screenshot: {e}"
