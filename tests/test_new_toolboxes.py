import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import json
from crytonix.tools import NetworkToolbox, ArchiveToolbox, CryptoToolbox, SystemInfoToolbox, ConversionToolbox

class TestNetworkToolbox(unittest.TestCase):
    @patch('subprocess.run')
    @patch('platform.system')
    def test_ping(self, mock_system, mock_run):
        mock_system.return_value = 'Linux'
        mock_run.return_value.stdout = "ping output"
        result = NetworkToolbox.ping('google.com')
        self.assertIn("ping output", result)
        mock_run.assert_called_with(['ping', '-c', '4', 'google.com'], capture_output=True, text=True, timeout=10)

    @patch('socket.create_connection')
    def test_check_port_open(self, mock_conn):
        result = NetworkToolbox.check_port('localhost', 8080)
        self.assertIn("OPEN", result)

    @patch('socket.create_connection')
    def test_check_port_closed(self, mock_conn):
        mock_conn.side_effect = Exception("Connection refused")
        result = NetworkToolbox.check_port('localhost', 8080)
        self.assertIn("CLOSED", result)

    @patch('socket.gethostbyname')
    def test_dns_lookup(self, mock_dns):
        mock_dns.return_value = '127.0.0.1'
        result = NetworkToolbox.dns_lookup('localhost')
        self.assertIn("127.0.0.1", result)

class TestArchiveToolbox(unittest.TestCase):
    @patch('zipfile.ZipFile')
    @patch('os.walk')
    def test_zip_files(self, mock_walk, mock_zip):
        mock_walk.return_value = [('/root', [], ['file.txt'])]
        mock_zip_instance = mock_zip.return_value.__enter__.return_value

        result = ArchiveToolbox.zip_files('/root', 'out.zip')

        self.assertIn("Successfully zipped", result)
        mock_zip_instance.write.assert_called()

    @patch('zipfile.ZipFile')
    def test_unzip_file(self, mock_zip):
        mock_zip_instance = mock_zip.return_value.__enter__.return_value
        result = ArchiveToolbox.unzip_file('test.zip', 'out_dir')
        self.assertIn("Successfully extracted", result)
        mock_zip_instance.extractall.assert_called_with('out_dir')

class TestCryptoToolbox(unittest.TestCase):
    def test_generate_hash(self):
        result = CryptoToolbox.generate_hash("hello")
        # sha256 of "hello"
        expected = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        self.assertEqual(result, expected)

    def test_base64(self):
        encoded = CryptoToolbox.base64_encode("hello")
        decoded = CryptoToolbox.base64_decode(encoded)
        self.assertEqual("aGVsbG8=", encoded)
        self.assertEqual("hello", decoded)

    def test_uuid(self):
        uuid_str = CryptoToolbox.generate_uuid()
        self.assertEqual(len(uuid_str), 36)

class TestSystemInfoToolbox(unittest.TestCase):
    @patch('shutil.disk_usage')
    def test_disk_usage(self, mock_disk):
        mock_disk.return_value = (100 * 2**30, 50 * 2**30, 50 * 2**30)
        result = SystemInfoToolbox.get_disk_usage()
        self.assertIn("Total: 100 GB", result)

    def test_resource_usage_no_psutil(self):
        with patch.dict(sys.modules, {'psutil': None}):
            result = SystemInfoToolbox.get_resource_usage()
            self.assertIn("psutil not installed", result)

    def test_resource_usage_with_psutil(self):
        mock_psutil = MagicMock()
        mock_psutil.cpu_percent.return_value = 10.5
        mock_memory = MagicMock()
        mock_memory.percent = 45.0
        mock_memory.used = 4000 * 2**20
        mock_memory.available = 4000 * 2**20
        mock_psutil.virtual_memory.return_value = mock_memory

        with patch.dict(sys.modules, {'psutil': mock_psutil}):
            result = SystemInfoToolbox.get_resource_usage()
            self.assertIn("CPU Usage: 10.5%", result)
            self.assertIn("Memory Usage: 45.0%", result)

class TestConversionToolbox(unittest.TestCase):
    def test_json_to_yaml(self):
        # Mock pyyaml
        mock_yaml = MagicMock()
        mock_yaml.dump.return_value = "key: value\n"

        with patch.dict(sys.modules, {'yaml': mock_yaml}):
            result = ConversionToolbox.json_to_yaml('{"key": "value"}')
            self.assertIn("key: value", result)

    def test_yaml_to_json(self):
        # Mock pyyaml
        mock_yaml = MagicMock()
        mock_yaml.safe_load.return_value = {"key": "value"}

        with patch.dict(sys.modules, {'yaml': mock_yaml}):
            result = ConversionToolbox.yaml_to_json("key: value")
            self.assertIn('"key": "value"', result)

    def test_csv_to_json(self):
        csv_content = "name,age\nAlice,30\nBob,25"
        with patch('builtins.open', mock_open(read_data=csv_content)):
             result = ConversionToolbox.csv_to_json("dummy.csv")
             self.assertIn('"name": "Alice"', result)
             self.assertIn('"age": "30"', result)

if __name__ == '__main__':
    unittest.main()
