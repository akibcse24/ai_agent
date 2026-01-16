import os
import zipfile
import csv
import json
from typing import List, Dict

class FileToolbox:
    """Tools for file manipulation (zip, csv)."""

    @staticmethod
    def zip_files(source_dir: str, output_zip: str) -> str:
        """Compress a directory into a zip file."""
        try:
            output_zip_abs = os.path.abspath(output_zip)
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Prevent recursive zipping
                        if os.path.abspath(file_path) == output_zip_abs:
                            continue

                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
            return f"Successfully created zip archive: {output_zip}"
        except Exception as e:
            return f"Error creating zip: {e}"

    @staticmethod
    def unzip_file(zip_path: str, output_dir: str) -> str:
        """Extract a zip archive."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(output_dir)
            return f"Successfully extracted {zip_path} to {output_dir}"
        except Exception as e:
            return f"Error unzipping: {e}"

    @staticmethod
    def read_csv(path: str, delimiter: str = ",") -> str:
        """Read a CSV file into a list of dicts."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                data = list(reader)
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"Error reading CSV: {e}"

    @staticmethod
    def write_csv(path: str, data: List[Dict]) -> str:
        """Write a list of dicts to a CSV file."""
        if not data:
            return "Error: No data to write."
        try:
            keys = data[0].keys()
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)
            return f"Successfully wrote CSV to {path}"
        except Exception as e:
            return f"Error writing CSV: {e}"
