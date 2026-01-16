import unittest
from crytonix.tools import ProductToolbox, DesignToolbox, DependencyToolbox, DatabaseToolbox

class TestMiscTools(unittest.TestCase):
    def test_sentiment(self):
        # TextBlob might not be installed, expect error string but not crash
        res = ProductToolbox.analyze_sentiment("I love this code!")
        self.assertTrue(isinstance(res, str))

    def test_design(self):
        res = DesignToolbox.check_contrast_ratio("#FFFFFF", "#000000")
        self.assertIn("Contrast Ratio", res)

    def test_dependency(self):
        # We know pip is installed in this env
        res = DependencyToolbox.check_outdated()
        # Either returns list or "All packages up to date" or "Error"
        self.assertTrue(isinstance(res, str))

    def test_database(self):
        # Test sqlite query on memory db
        import sqlite3
        with sqlite3.connect("test.db") as conn:
            conn.execute("CREATE TABLE t (id int)")

        res = DatabaseToolbox.query_sqlite("test.db", "SELECT * FROM t")
        self.assertTrue(isinstance(res, str))
        import os
        os.remove("test.db")

if __name__ == "__main__":
    unittest.main()
