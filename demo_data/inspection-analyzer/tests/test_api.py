import unittest
from app.api import get_inspection_summary

class TestAPI(unittest.TestCase):
    def test_summary(self):
        summary = get_inspection_summary()
        self.assertEqual(summary["total_inspections"], 3)
        self.assertEqual(summary["passed"], 2)

if __name__ == "__main__":
    unittest.main()
