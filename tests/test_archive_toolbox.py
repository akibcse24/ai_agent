import unittest
import os
import shutil
import tempfile
from crytonix.tools import ArchiveToolbox

class TestArchiveToolbox(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.source_dir = os.path.join(self.test_dir, "source")
        self.output_dir = os.path.join(self.test_dir, "output")
        self.extract_dir = os.path.join(self.test_dir, "extract")

        os.makedirs(self.source_dir)
        os.makedirs(self.output_dir)
        os.makedirs(self.extract_dir)

        # Create some dummy files
        with open(os.path.join(self.source_dir, "file1.txt"), "w") as f:
            f.write("Content of file 1")
        with open(os.path.join(self.source_dir, "file2.txt"), "w") as f:
            f.write("Content of file 2")

        self.single_file = os.path.join(self.source_dir, "file1.txt")

    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_compress_directory_zip(self):
        output_zip = os.path.join(self.output_dir, "archive")
        result = ArchiveToolbox.compress(self.source_dir, output_zip, archive_format='zip')
        self.assertIn("Compressed to", result)
        self.assertTrue(os.path.exists(output_zip + ".zip"))

        # Verify content list
        content = ArchiveToolbox.list_archive_content(output_zip + ".zip")
        self.assertIn("file1.txt", content)
        self.assertIn("file2.txt", content)

    def test_compress_directory_tar_gz(self):
        output_tar = os.path.join(self.output_dir, "archive")
        result = ArchiveToolbox.compress(self.source_dir, output_tar, archive_format='tar.gz')
        self.assertIn("Compressed to", result)
        self.assertTrue(os.path.exists(output_tar + ".tar.gz"))

        # Verify content list
        content = ArchiveToolbox.list_archive_content(output_tar + ".tar.gz")
        self.assertIn("file1.txt", content)

    def test_compress_file_zip(self):
        output_zip = os.path.join(self.output_dir, "single_file.zip")
        result = ArchiveToolbox.compress(self.single_file, output_zip, archive_format='zip')
        self.assertIn("Compressed to", result)
        self.assertTrue(os.path.exists(output_zip))

        content = ArchiveToolbox.list_archive_content(output_zip)
        self.assertIn("file1.txt", content)

    def test_extract_zip(self):
        # First compress
        output_zip = os.path.join(self.output_dir, "archive.zip")
        ArchiveToolbox.compress(self.source_dir, output_zip, archive_format='zip')

        # Then extract
        result = ArchiveToolbox.extract(output_zip, self.extract_dir)
        self.assertIn("Extracted to", result)

        self.assertTrue(os.path.exists(os.path.join(self.extract_dir, "file1.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.extract_dir, "file2.txt")))

    def test_extract_tar_gz(self):
        # First compress
        output_tar = os.path.join(self.output_dir, "archive.tar.gz")
        ArchiveToolbox.compress(self.source_dir, output_tar, archive_format='tar.gz')

        # Then extract
        result = ArchiveToolbox.extract(output_tar, self.extract_dir)
        self.assertIn("Extracted to", result)

        self.assertTrue(os.path.exists(os.path.join(self.extract_dir, "file1.txt")))

if __name__ == '__main__':
    unittest.main()
