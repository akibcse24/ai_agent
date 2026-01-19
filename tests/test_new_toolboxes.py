import os
import json
import pytest
from crytonix.tools import SystemToolbox, FileToolbox

def test_system_toolbox():
    # Test get_system_info
    info = SystemToolbox.get_system_info()
    print(f"System Info: {info}")
    assert "OS:" in info
    assert "Python:" in info

    # Test get_resource_usage
    usage = SystemToolbox.get_resource_usage()
    print(f"Resource Usage: {usage}")
    assert "CPU Usage:" in usage
    assert "Memory Usage:" in usage

    # Test list_processes
    procs = SystemToolbox.list_processes()
    print(f"Processes: {procs[:100]}...") # Print preview
    assert isinstance(procs, str)
    assert len(procs) > 0

def test_file_toolbox_csv(tmp_path):
    csv_file = tmp_path / "test.csv"
    data = [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
    json_data = json.dumps(data)

    # Test write_csv
    result = FileToolbox.write_csv(str(csv_file), json_data)
    assert "Successfully wrote" in result
    assert csv_file.exists()

    # Test read_csv
    read_result = FileToolbox.read_csv(str(csv_file))
    read_data = json.loads(read_result)
    assert len(read_data) == 2
    assert read_data[0]["name"] == "Alice"

def test_file_toolbox_zip(tmp_path):
    # Create dummy files
    file1 = tmp_path / "file1.txt"
    file1.write_text("Hello World", encoding='utf-8')
    file2 = tmp_path / "file2.txt"
    file2.write_text("Another File", encoding='utf-8')

    zip_file = tmp_path / "archive.zip"

    # Test zip_files
    # Note: zip_files in tools.py uses os.path.basename, so it will flatten the structure inside the zip
    # which is fine for this test.
    result = FileToolbox.zip_files(str(zip_file), [str(file1), str(file2)])
    assert "Created zip archive" in result
    assert zip_file.exists()

    # Test unzip_file
    extract_dir = tmp_path / "extracted"
    # tools.py unzip_file extractall handles directory creation if needed?
    # zipfile.extractall creates the target directory? Yes.
    # But let's create it just in case or pass a path.

    result = FileToolbox.unzip_file(str(zip_file), str(extract_dir))
    assert "Extracted" in result
    assert (extract_dir / "file1.txt").exists()
    assert (extract_dir / "file2.txt").exists()
    assert (extract_dir / "file1.txt").read_text(encoding='utf-8') == "Hello World"
