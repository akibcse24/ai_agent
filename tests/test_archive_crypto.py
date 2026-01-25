import unittest
import os
import shutil
import zipfile
import tarfile
import hashlib
import base64
import uuid
from crytonix.tools import ArchiveToolbox, CryptoToolbox

class TestArchiveToolbox(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_archive_data"
        os.makedirs(self.test_dir, exist_ok=True)
        self.files = []
        for i in range(3):
            filename = os.path.join(self.test_dir, f"file{i}.txt")
            with open(filename, "w") as f:
                f.write(f"Content of file {i}")
            self.files.append(filename)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        if os.path.exists("test_archive.zip"):
            os.remove("test_archive.zip")
        if os.path.exists("test_archive.tar.gz"):
            os.remove("test_archive.tar.gz")
        if os.path.exists("test_extract_zip"):
            shutil.rmtree("test_extract_zip")
        if os.path.exists("test_extract_tar"):
            shutil.rmtree("test_extract_tar")

    def test_zip_unzip(self):
        # Create Zip
        result = ArchiveToolbox.zip_files(self.files, "test_archive.zip")
        self.assertIn("Successfully created", result)
        self.assertTrue(os.path.exists("test_archive.zip"))

        # Unzip
        result = ArchiveToolbox.unzip_file("test_archive.zip", "test_extract_zip")
        self.assertIn("Successfully extracted", result)
        self.assertTrue(os.path.exists(os.path.join("test_extract_zip", "file0.txt")))

        # Verify content
        with open(os.path.join("test_extract_zip", "file0.txt"), "r") as f:
            self.assertEqual(f.read(), "Content of file 0")

    def test_tar_untar(self):
        # Create Tar
        result = ArchiveToolbox.create_tarball(self.files, "test_archive.tar.gz")
        self.assertIn("Successfully created", result)
        self.assertTrue(os.path.exists("test_archive.tar.gz"))

        # Untar
        result = ArchiveToolbox.extract_tarball("test_archive.tar.gz", "test_extract_tar")
        self.assertIn("Successfully extracted", result)
        self.assertTrue(os.path.exists(os.path.join("test_extract_tar", "file0.txt")))

class TestCryptoToolbox(unittest.TestCase):
    def test_hash(self):
        text = "hello world"
        expected_sha256 = hashlib.sha256(text.encode()).hexdigest()
        self.assertEqual(CryptoToolbox.generate_hash(text), expected_sha256)

        expected_md5 = hashlib.md5(text.encode()).hexdigest()
        self.assertEqual(CryptoToolbox.generate_hash(text, "md5"), expected_md5)

    def test_file_hash(self):
        filename = "test_hash.txt"
        content = b"hello file"
        with open(filename, "wb") as f:
            f.write(content)

        try:
            expected = hashlib.sha256(content).hexdigest()
            self.assertEqual(CryptoToolbox.generate_file_hash(filename), expected)
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    def test_base64(self):
        text = "hello world"
        encoded = CryptoToolbox.base64_encode(text)
        decoded = CryptoToolbox.base64_decode(encoded)
        self.assertEqual(decoded, text)

    def test_uuid(self):
        uid = CryptoToolbox.generate_uuid()
        try:
            val = uuid.UUID(uid, version=4)
        except ValueError:
            self.fail("Invalid UUID generated")

if __name__ == "__main__":
    unittest.main()
