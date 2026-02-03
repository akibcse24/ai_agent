import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
from crytonix.tools import (HealthToolbox, NetworkToolbox, ArchiveToolbox, CryptoToolbox, LocalizationToolbox)

class TestNewToolboxes(unittest.TestCase):

    # --- HealthToolbox ---
    def test_health_check_posture(self):
        result = HealthToolbox.check_posture()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_health_hydration(self):
        result = HealthToolbox.hydration_reminder()
        self.assertIsInstance(result, str)
        # Check if result is one of expected strings or just check length
        self.assertTrue(len(result) > 5)

    # --- NetworkToolbox ---
    @patch('subprocess.run')
    def test_network_ping(self, mock_run):
        mock_run.return_value.stdout = "Reply from..."
        result = NetworkToolbox.ping("google.com")
        self.assertIn("Reply from", result)

    @patch('socket.socket')
    def test_network_check_port_open(self, mock_socket):
        mock_inst = MagicMock()
        mock_socket.return_value = mock_inst
        mock_inst.connect_ex.return_value = 0 # Open
        result = NetworkToolbox.check_port("localhost", 80)
        self.assertIn("OPEN", result)

    @patch('socket.gethostbyname')
    def test_network_dns(self, mock_dns):
        mock_dns.return_value = "1.2.3.4"
        result = NetworkToolbox.dns_lookup("example.com")
        self.assertIn("1.2.3.4", result)

    @patch('requests.get')
    def test_network_my_ip(self, mock_get):
        mock_get.return_value.text = "100.100.100.100"
        result = NetworkToolbox.my_ip()
        self.assertIn("100.100.100.100", result)

    # --- ArchiveToolbox ---
    @patch('zipfile.ZipFile')
    @patch('os.path.exists')
    def test_archive_zip(self, mock_exists, mock_zip):
        mock_exists.return_value = True
        result = ArchiveToolbox.zip_files("test.zip", ["file1.txt"])
        self.assertIn("Successfully created", result)

    # --- CryptoToolbox ---
    def test_crypto_hash(self):
        result = CryptoToolbox.generate_hash("hello")
        self.assertIn("SHA256:", result)
        # sha256 of "hello" ends in 5d53...

    def test_crypto_base64(self):
        encoded = CryptoToolbox.base64_encode("hello")
        decoded = CryptoToolbox.base64_decode(encoded)
        self.assertEqual(decoded, "hello")

    def test_crypto_uuid(self):
        result = CryptoToolbox.generate_uuid()
        self.assertEqual(len(result), 36) # UUID length

    # --- LocalizationToolbox ---
    def test_localization_find_strings(self):
        # Create a temp file
        test_file = "temp_test_loc.py"
        with open(test_file, 'w') as f:
            f.write('print("Hello World")\nx = "Another String"')

        try:
            result = LocalizationToolbox.find_hardcoded_strings(".")
            self.assertIn("Hello World", result)
            self.assertIn("Another String", result)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_localization_verify_sync(self):
        src = "src.json"
        tgt = "tgt.json"
        with open(src, 'w') as f: json.dump({"key1": "val1", "key2": "val2"}, f)
        with open(tgt, 'w') as f: json.dump({"key1": "val1"}, f) # Missing key2

        try:
            result = LocalizationToolbox.verify_keys_sync(src, tgt)
            self.assertIn("Missing keys", result)
            self.assertIn("key2", result)
        finally:
            if os.path.exists(src): os.remove(src)
            if os.path.exists(tgt): os.remove(tgt)

if __name__ == '__main__':
    unittest.main()
