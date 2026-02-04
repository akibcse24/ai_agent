import unittest
from unittest.mock import patch, MagicMock
import sys
import json
import os

# Ensure the package is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crytonix.tools import SystemInfoToolbox, ConversionToolbox

class TestSystemInfoToolbox(unittest.TestCase):
    def test_get_system_info(self):
        info = SystemInfoToolbox.get_system_info()
        self.assertIn("System:", info)
        self.assertIn("Python Version:", info)

    def test_get_resource_usage_with_psutil(self):
        # Mock psutil
        mock_psutil = MagicMock()
        mock_psutil.cpu_percent.return_value = 15.5
        mock_memory = MagicMock()
        mock_memory.percent = 45.0
        mock_memory.used = 4000 * 1024 * 1024
        mock_memory.total = 8000 * 1024 * 1024
        mock_psutil.virtual_memory.return_value = mock_memory

        # We need to ensure import psutil works inside the method
        # patching sys.modules is safer for local imports
        with patch.dict(sys.modules, {'psutil': mock_psutil}):
            usage = SystemInfoToolbox.get_resource_usage()
            self.assertIn("CPU Usage: 15.5%", usage)
            self.assertIn("Memory Usage: 45.0%", usage)

    def test_get_resource_usage_without_psutil(self):
        # Simulate psutil missing
        with patch.dict(sys.modules, {'psutil': None}):
             # We need to force ImportError when 'import psutil' happens
             # Using side_effect on __import__ is tricky.
             # Easier way: The method does import psutil inside try/except.
             # If sys.modules['psutil'] is None, it might raise ModuleNotFoundError or return None.
             # If we remove it from sys.modules?
             with patch.dict(sys.modules):
                 if 'psutil' in sys.modules:
                     del sys.modules['psutil']
                 # We also need to ensure it can't be found
                 # Creating a mock import that fails
                 orig_import = __import__
                 def import_mock(name, *args, **kwargs):
                     if name == 'psutil':
                         raise ImportError("No module named 'psutil'")
                     return orig_import(name, *args, **kwargs)

                 with patch('builtins.__import__', side_effect=import_mock):
                     usage = SystemInfoToolbox.get_resource_usage()
                     self.assertIn("Error: psutil not installed", usage)

    def test_get_disk_usage(self):
        usage = SystemInfoToolbox.get_disk_usage(".")
        self.assertIn("Disk Usage", usage)
        self.assertIn("Total:", usage)
        self.assertIn("Used:", usage)
        self.assertIn("Free:", usage)


class TestConversionToolbox(unittest.TestCase):
    def test_json_to_yaml(self):
        json_str = '{"name": "test", "value": 123}'
        # Mock yaml
        mock_yaml = MagicMock()
        mock_yaml.dump.return_value = "name: test\nvalue: 123\n"

        with patch.dict(sys.modules, {'yaml': mock_yaml}):
            yaml_output = ConversionToolbox.json_to_yaml(json_str)
            self.assertIn("name: test", yaml_output)
            self.assertIn("value: 123", yaml_output)

    def test_yaml_to_json(self):
        yaml_str = "name: test\nvalue: 123"
        # Mock yaml
        mock_yaml = MagicMock()
        mock_yaml.safe_load.return_value = {"name": "test", "value": 123}

        with patch.dict(sys.modules, {'yaml': mock_yaml}):
            json_output = ConversionToolbox.yaml_to_json(yaml_str)
            self.assertIn('"name": "test"', json_output)
            self.assertIn('"value": 123', json_output)

    def test_csv_to_json(self):
        # Create a temporary CSV file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp.write("name,age\nAlice,30\nBob,25")
            tmp_path = tmp.name

        try:
            json_output = ConversionToolbox.csv_to_json(tmp_path)
            data = json.loads(json_output)
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]['name'], 'Alice')
            self.assertEqual(data[0]['age'], '30')
        finally:
            os.remove(tmp_path)

if __name__ == '__main__':
    unittest.main()
