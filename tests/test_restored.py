import unittest
from crytonix.tools import ScaffoldToolbox, DocumentationToolbox
import os
import shutil

class TestRestoredTools(unittest.TestCase):
    def test_scaffold(self):
        # This test creates actual files, so we clean up
        name = "test_scaffold_project"
        res = ScaffoldToolbox.create_python_project(name)
        # Loose match for case insensitivity
        self.assertTrue(f"created at ./{name}/" in res.lower())
        if os.path.exists(name): shutil.rmtree(name)

    def test_docs(self):
        readme = DocumentationToolbox.generate_readme(".")
        # Just check it generated a markdown header
        self.assertIn("# ", readme)
        self.assertIn("## Description", readme)

if __name__ == "__main__":
    unittest.main()
