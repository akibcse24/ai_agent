import unittest
import os
import shutil
import csv
import zipfile
import json
from crytonix.tools import FileToolbox, SystemToolbox

class TestFileToolbox(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_files"
        os.makedirs(self.test_dir, exist_ok=True)
        self.csv_path = os.path.join(self.test_dir, "test.csv")
        self.zip_path = os.path.join(self.test_dir, "test.zip")
        self.unzip_dir = os.path.join(self.test_dir, "unzip")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_csv_ops(self):
        data = [{"name": "A", "val": "1"}, {"name": "B", "val": "2"}]
        res = FileToolbox.write_csv(self.csv_path, data)
        self.assertIn("Successfully", res)

        read_json = FileToolbox.read_csv(self.csv_path)
        read_data = json.loads(read_json)
        self.assertEqual(len(read_data), 2)
        self.assertEqual(read_data[0]["name"], "A")

    def test_zip_ops(self):
        with open(os.path.join(self.test_dir, "file.txt"), "w") as f:
            f.write("content")

        res = FileToolbox.zip_files(self.test_dir, self.zip_path)
        self.assertIn("Successfully", res)

        os.makedirs(self.unzip_dir, exist_ok=True)
        res = FileToolbox.unzip_file(self.zip_path, self.unzip_dir)
        self.assertIn("Successfully", res)

        # Check if file exists inside structure (zip preserves paths relative)
        # Our zip implementation zips relpaths, so verify logic needs to match
        # It creates zip with relpaths from source_dir.
        # file.txt inside
        self.assertTrue(os.path.exists(os.path.join(self.unzip_dir, "file.txt")))

class TestSystemToolbox(unittest.TestCase):
    def test_system_info(self):
        info_json = SystemToolbox.get_system_info()
        info = json.loads(info_json)
        self.assertIn("system", info)
        self.assertIn("cpu_count", info)

    def test_port_check(self):
        # Just ensure it returns a string and doesn't crash
        res = SystemToolbox.check_port("localhost", 12345)
        self.assertIsInstance(res, str)
        self.assertIn("Port", res)

if __name__ == "__main__":
    unittest.main()
