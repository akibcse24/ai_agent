import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import json
import ast
import tempfile
import shutil
import base64
import platform
import subprocess

# Add parent directory to path to import crytonix
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import toolboxes - some might fail if we import them before they exist,
# but we are mocking the module structure or we will just reference them via string names
# if we were strictly TDD, but here we are adding them to `crytonix.tools`.
# Since we haven't implemented them yet, importing them would fail.
# So we will mock the import or just define the test structure assuming they will exist.
# However, to run this test file *before* implementation, it would fail.
# But the plan says "Create test file" first. I will write the tests assuming the toolboxes exist.
# I will use getattr(crytonix.tools, 'HealthToolbox') pattern inside tests to avoid ImportErrors at module level
# if I run it prematurely, but strictly speaking I should implement code then test.
# But the prompt asked to "Plan new features... add the feature and build it to verify it".
# My plan follows TDD-ish approach: Write test -> Implement -> Verify.
# For now, I will just setup the imports.

try:
    from crytonix.tools import (
        HealthToolbox, NetworkToolbox, ArchiveToolbox, CryptoToolbox,
        PDFToolbox, AudioToolbox, LocalizationToolbox, SystemInfoToolbox,
        ConversionToolbox
    )
except ImportError:
    pass # Expected until implemented

class TestNewToolboxes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    # --- HealthToolbox Tests ---
    def test_health_toolbox(self):
        from crytonix.tools import HealthToolbox

        # Test hydration reminder
        msg = HealthToolbox.hydration_reminder()
        self.assertIn("hydration", msg.lower())

        # Test posture check
        msg = HealthToolbox.check_posture()
        self.assertIn("posture", msg.lower())

    # --- NetworkToolbox Tests ---
    @patch('subprocess.run')
    def test_network_ping(self, mock_run):
        from crytonix.tools import NetworkToolbox

        # Mock successful ping
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Reply from..."

        res = NetworkToolbox.ping("8.8.8.8")
        self.assertIn("successful", res.lower())

        # Mock failed ping
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Request timed out"

        res = NetworkToolbox.ping("invalid.host")
        self.assertIn("failed", res.lower())

    @patch('socket.socket')
    def test_check_port(self, mock_socket):
        from crytonix.tools import NetworkToolbox

        # Mock open port
        mock_sock_instance = MagicMock()
        mock_socket.return_value = mock_sock_instance
        mock_sock_instance.connect_ex.return_value = 0

        res = NetworkToolbox.check_port("localhost", 8080)
        self.assertIn("open", res.lower())

        # Mock closed port
        mock_sock_instance.connect_ex.return_value = 1

        res = NetworkToolbox.check_port("localhost", 8081)
        self.assertIn("closed", res.lower())

    @patch('socket.gethostbyname')
    def test_dns_lookup(self, mock_gethostbyname):
        from crytonix.tools import NetworkToolbox

        mock_gethostbyname.return_value = "1.2.3.4"
        res = NetworkToolbox.dns_lookup("example.com")
        self.assertIn("1.2.3.4", res)

    # --- ArchiveToolbox Tests ---
    def test_zip_unzip_files(self):
        from crytonix.tools import ArchiveToolbox

        # Create dummy files
        f1 = os.path.join(self.temp_dir, "file1.txt")
        f2 = os.path.join(self.temp_dir, "file2.txt")
        with open(f1, "w") as f: f.write("content1")
        with open(f2, "w") as f: f.write("content2")

        zip_path = os.path.join(self.temp_dir, "archive.zip")

        # Test Zip
        res = ArchiveToolbox.zip_files(zip_path, [f1, f2])
        self.assertTrue(os.path.exists(zip_path))
        self.assertIn("successfully", res.lower())

        # Test Unzip
        extract_dir = os.path.join(self.temp_dir, "extracted")
        res = ArchiveToolbox.unzip_file(zip_path, extract_dir)

        self.assertTrue(os.path.exists(os.path.join(extract_dir, "file1.txt")))
        self.assertTrue(os.path.exists(os.path.join(extract_dir, "file2.txt")))
        self.assertIn("extracted", res.lower())

    def test_zip_directory(self):
        from crytonix.tools import ArchiveToolbox

        # Create a directory with files
        dir_path = os.path.join(self.temp_dir, "to_zip")
        os.makedirs(dir_path)
        with open(os.path.join(dir_path, "d1.txt"), "w") as f: f.write("d1")

        zip_path = os.path.join(self.temp_dir, "dir_archive.zip")

        res = ArchiveToolbox.zip_files(zip_path, [dir_path])
        self.assertIn("successfully", res.lower())

        # Unzip and check
        extract_dir = os.path.join(self.temp_dir, "dir_extracted")
        ArchiveToolbox.unzip_file(zip_path, extract_dir)

        # Check if d1.txt exists inside the extracted folder structure
        # Structure depends on relpath logic: os.path.relpath(filepath, os.path.dirname(dir_path))
        # dirname(dir_path) is self.temp_dir.
        # filepath is self.temp_dir/to_zip/d1.txt.
        # relpath is to_zip/d1.txt.
        # So it should be extracted to extract_dir/to_zip/d1.txt

        self.assertTrue(os.path.exists(os.path.join(extract_dir, "to_zip", "d1.txt")))

    # --- CryptoToolbox Tests ---
    def test_crypto_toolbox(self):
        from crytonix.tools import CryptoToolbox

        # Test Hash
        h = CryptoToolbox.generate_hash("hello", "sha256")
        self.assertEqual(len(h), 64)

        # Test File Hash
        f_path = os.path.join(self.temp_dir, "hash_test.txt")
        with open(f_path, "w") as f: f.write("content")
        fh = CryptoToolbox.generate_file_hash(f_path)
        self.assertTrue(len(fh) > 0)

        # Test Base64
        enc = CryptoToolbox.base64_encode("hello")
        self.assertEqual(enc, "aGVsbG8=")
        dec = CryptoToolbox.base64_decode("aGVsbG8=")
        self.assertEqual(dec, "hello")

        # Test UUID
        uid = CryptoToolbox.generate_uuid()
        self.assertEqual(len(uid.split("-")), 5)

    # --- LocalizationToolbox Tests ---
    def test_localization_toolbox(self):
        from crytonix.tools import LocalizationToolbox

        # Test finding strings
        py_file = os.path.join(self.temp_dir, "test_loc.py")
        with open(py_file, "w") as f: f.write("x = 'Hello World'")

        res = LocalizationToolbox.find_hardcoded_strings(self.temp_dir)
        self.assertIn("Hello World", res)

        # Test Sync Keys
        json1 = os.path.join(self.temp_dir, "en.json")
        json2 = os.path.join(self.temp_dir, "fr.json")
        with open(json1, "w") as f: json.dump({"hello": "world"}, f)
        with open(json2, "w") as f: json.dump({"hello": "monde", "extra": "missing"}, f)

        res = LocalizationToolbox.verify_keys_sync([json1, json2])
        self.assertIn("extra", res)

    # --- SystemInfoToolbox Tests ---
    @patch('platform.uname')
    @patch('psutil.virtual_memory')
    def test_system_info(self, mock_mem, mock_uname):
        # Mock psutil not installed handled in implementation, but here we assume it is or mocked
        from crytonix.tools import SystemInfoToolbox

        mock_uname_res = MagicMock()
        mock_uname_res.system = "TestOS"
        mock_uname.return_value = mock_uname_res

        mock_mem_res = MagicMock()
        mock_mem_res.total = 1000
        mock_mem_res.available = 500
        mock_mem_res.percent = 50.0
        mock_mem.return_value = mock_mem_res

        res = SystemInfoToolbox.get_system_info()
        self.assertIn("TestOS", res)

        # If psutil is mocked successfully
        res_usage = SystemInfoToolbox.get_resource_usage()
        # Depending on implementation, it might check if psutil is imported.
        # Since we are mocking psutil in the test, we need to ensure the module picks it up.
        # But SystemInfoToolbox does `import psutil` inside the method usually.
        # We might need `sys.modules` patching for `psutil`.

    @patch.dict(sys.modules, {'psutil': MagicMock()})
    def test_system_info_with_psutil_mock(self):
        from crytonix.tools import SystemInfoToolbox
        # Setup the mock
        mock_mem = MagicMock()
        mock_mem.percent = 50.0
        mock_mem.total = 8 * 1024**3
        mock_mem.available = 4 * 1024**3

        sys.modules['psutil'].virtual_memory.return_value = mock_mem
        sys.modules['psutil'].cpu_percent.return_value = 10.0

        res = SystemInfoToolbox.get_resource_usage()
        self.assertIn("50.0", res)

    # --- PDFToolbox Tests ---
    @patch.dict(sys.modules, {'pypdf': MagicMock(), 'reportlab': MagicMock(), 'reportlab.pdfgen': MagicMock(), 'reportlab.lib.pagesizes': MagicMock()})
    def test_pdf_toolbox(self):
        from crytonix.tools import PDFToolbox

        # Test Create PDF
        # We need to mock canvas class properly
        mock_canvas_instance = MagicMock()

        # Mocking the import hierarchy
        # from reportlab.pdfgen import canvas -> canvas is a module
        # c = canvas.Canvas(...)

        mock_canvas_module = MagicMock()
        mock_canvas_module.Canvas.return_value = mock_canvas_instance
        sys.modules['reportlab.pdfgen'].canvas = mock_canvas_module

        # Also ensure 'letter' is available
        sys.modules['reportlab.lib.pagesizes'].letter = (612, 792)

        pdf_path = os.path.join(self.temp_dir, "test.pdf")
        res = PDFToolbox.create_pdf("Content", pdf_path)

        # Verify
        mock_canvas_instance.save.assert_called()
        self.assertIn("created", res.lower())

        # Test Extract Text
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock()]
        mock_reader.pages[0].extract_text.return_value = "Extracted Content"
        sys.modules['pypdf'].PdfReader.return_value = mock_reader

        res = PDFToolbox.extract_text(pdf_path)
        self.assertIn("Extracted Content", res)

    # --- AudioToolbox Tests ---
    @patch.dict(sys.modules, {'pyttsx3': MagicMock(), 'mutagen': MagicMock()})
    def test_audio_toolbox(self):
        from crytonix.tools import AudioToolbox

        # Test TTS
        mock_engine = MagicMock()
        sys.modules['pyttsx3'].init.return_value = mock_engine

        audio_path = os.path.join(self.temp_dir, "test.mp3")
        res = AudioToolbox.text_to_speech("Hello", audio_path)
        mock_engine.save_to_file.assert_called()
        mock_engine.runAndWait.assert_called()
        self.assertIn("saved", res.lower())

        # Test Metadata
        # Fix: mock mutagen.File to avoid TypeError
        sys.modules['mutagen'].File.return_value = {"artist": ["Me"], "title": ["Test"]}

        res = AudioToolbox.get_audio_metadata(audio_path)
        self.assertIn("Me", res)

    # --- ConversionToolbox Tests ---
    @patch.dict(sys.modules, {'pyyaml': MagicMock()})
    def test_conversion_toolbox(self):
        from crytonix.tools import ConversionToolbox

        # Test JSON to YAML (Mocking pyyaml)
        # We also need to mock built-in open but we have temp files, so we can use real files for reading/writing if libraries support it.
        # But yaml is mocked.

        json_file = os.path.join(self.temp_dir, "data.json")
        yaml_file = os.path.join(self.temp_dir, "data.yaml")

        with open(json_file, "w") as f: json.dump({"key": "value"}, f)

        # yaml.dump is called
        sys.modules['pyyaml'].dump.return_value = "key: value"

        # We need to make sure ConversionToolbox imports yaml properly.
        # If it does `import yaml`, we mocked `yaml` (since pyyaml installs as yaml).
        # Actually `import yaml` works if `pyyaml` is installed. We should patch `yaml` in sys.modules.
        sys.modules['yaml'] = sys.modules['pyyaml'] # Alias

        res = ConversionToolbox.json_to_yaml(json_file, yaml_file)
        # It should call yaml.dump
        self.assertTrue(sys.modules['yaml'].dump.called)
        self.assertIn("converted", res.lower())

        # Test CSV to JSON
        csv_file = os.path.join(self.temp_dir, "data.csv")
        json_out = os.path.join(self.temp_dir, "from_csv.json")

        with open(csv_file, "w") as f: f.write("name,age\nAlice,30")

        res = ConversionToolbox.csv_to_json(csv_file, json_out)
        self.assertTrue(os.path.exists(json_out))
        with open(json_out) as f:
            data = json.load(f)
            self.assertEqual(data[0]['name'], 'Alice')

if __name__ == "__main__":
    unittest.main()
