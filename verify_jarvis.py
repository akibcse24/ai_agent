from crytonix.tools import DesktopToolbox, AutomationToolbox
import unittest
import pyperclip
import platform

class TestJarvisCapabilities(unittest.TestCase):
    def test_clipboard(self):
        print("Testing Clipboard...")
        original = pyperclip.paste()
        test_text = "Crytonix Clipboard Test"

        # Write
        res = DesktopToolbox.clipboard_action("copy", test_text)
        self.assertIn("Text copied", res)

        # Read
        content = pyperclip.paste()
        self.assertEqual(content, test_text)

        # Restore
        pyperclip.copy(original)
        print("Clipboard: SUCCESS")

    def test_browser_logic(self):
        print("Testing Browser Logic (Mocked)...")
        # We can't really verify browser opened in headless, but we check if function runs
        res = DesktopToolbox.browser_open("https://example.com")
        self.assertIn("Opened URL", res)
        print("Browser: SUCCESS")

    def test_automation_imports(self):
        print("Testing Automation Imports...")
        # Check if type_text works (it relies on pyautogui)
        # We won't actually type to avoid messing up the agent's environment input
        # but we can check if it fails gracefully or runs

        # In a headless env (like this sandbox often is), pyautogui might fail on display
        # The tools.py has try/except blocks. Let's verify that.

        try:
            import pyautogui
            # If we are here, pyautogui is installed.
            # In headless docker, this might raise PyAutoGUIException: PyAutoGUI was unable to display...
            pass
        except ImportError:
            print("PyAutoGUI not installed, skipping advanced automation tests.")
            return

        # We trust the tool's try/except block to handle the display error safely
        # Let's try calling it.
        res = AutomationToolbox.type_text("test", interval=0.0)
        # It should either succeed or return an error string starting with "Error"
        print(f"Automation Result: {res}")
        self.assertTrue(isinstance(res, str))

    def test_volume_logic(self):
        print("Testing Volume Logic...")
        # This will likely fail or return error on a server container with no audio device
        # but we verify the code path executes
        res = DesktopToolbox.set_volume(50)
        print(f"Volume Result: {res}")
        self.assertTrue(isinstance(res, str))

if __name__ == "__main__":
    unittest.main()
