import os
import pytest
import csv
import zipfile
from crytonix.tools import SystemToolbox, FileToolbox, NetworkToolbox

class TestSystemToolbox:
    def test_get_system_info(self):
        info = SystemToolbox.get_system_info()
        assert "System" in info
        assert "Node Name" in info

    def test_get_resource_usage(self):
        # This requires psutil which we installed
        usage = SystemToolbox.get_resource_usage()
        assert "CPU Usage" in usage
        assert "Memory Usage" in usage

    def test_list_processes(self):
        # This requires psutil
        procs = SystemToolbox.list_processes(limit=1)
        assert "PID" in procs
        assert "Name" in procs

class TestFileToolbox:
    def test_read_write_csv(self, tmp_path):
        file_path = tmp_path / "test.csv"
        data = [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]

        # Write
        result = FileToolbox.write_csv(str(file_path), data)
        assert "Successfully wrote" in result

        # Read
        content = FileToolbox.read_csv(str(file_path))
        assert "Alice" in content
        assert "Bob" in content

    def test_zip_unzip(self, tmp_path):
        # Create some files
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1", encoding="utf-8")

        zip_path = tmp_path / "archive.zip"

        # Zip
        result = FileToolbox.zip_files(str(source_dir), str(zip_path))
        assert "Successfully created archive" in result
        assert zip_path.exists()

        # Unzip
        extract_dir = tmp_path / "extracted"
        result = FileToolbox.unzip_file(str(zip_path), str(extract_dir))
        assert "Successfully extracted" in result
        assert (extract_dir / "file1.txt").exists()
        assert (extract_dir / "file1.txt").read_text(encoding="utf-8") == "content1"

    def test_get_file_info(self, tmp_path):
        file_path = tmp_path / "info.txt"
        file_path.write_text("info", encoding="utf-8")

        info = FileToolbox.get_file_info(str(file_path))
        assert "Size" in info
        assert "Created" in info

class TestNetworkToolbox:
    def test_get_local_ip(self):
        ip = NetworkToolbox.get_local_ip()
        assert ip  # Just check if it returns something
        assert "." in ip

    def test_get_public_ip(self):
        # This makes an external request, might fail without internet
        # We can try it, or mock it. The environment seems to have internet access
        # based on previous successful apt/pip calls.
        ip = NetworkToolbox.get_public_ip()
        assert "Error" not in ip or "requests not installed" in ip

    def test_check_port(self):
        # We can check a port that is likely closed or open (like self)
        # Check port 80 on google.com (likely open)
        result = NetworkToolbox.check_port("google.com", 80)
        assert "OPEN" in result or "CLOSED" in result

    def test_dns_lookup(self):
        result = NetworkToolbox.dns_lookup("google.com")
        assert "DNS Lookup for google.com" in result
