import unittest
import os
from crytonix.dashboard import ProjectDashboard

class TestDashboard(unittest.TestCase):
    def test_stats(self):
        dash = ProjectDashboard()
        stats = dash.get_project_stats()
        self.assertIn("files", stats)
        self.assertIn("lines", stats)
        self.assertTrue(stats["files"] > 0)

    def test_git_status(self):
        dash = ProjectDashboard()
        status = dash.get_git_status()
        # It might be active or not depending on env, but should return dict
        self.assertIn("active", status)

if __name__ == "__main__":
    unittest.main()
