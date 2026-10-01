import sqlite3
import unittest

from src.utils.database.sqlite import dict_factory


class RowFactoryTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = dict_factory
        self.addCleanup(self.connection.close)

    def test_preserves_plain_text_starting_with_json_delimiters(self):
        for value in ("[Draft] project notes", "{unfinished", "[1,", "normal text"):
            with self.subTest(value=value):
                row = self.connection.execute("SELECT ? AS content", (value,)).fetchone()
                self.assertEqual(row["content"], value)

    def test_still_decodes_serialized_collections(self):
        row = self.connection.execute(
            "SELECT ? AS ids, ? AS metadata", ('["a", "b"]', '{"enabled": true}')
        ).fetchone()
        self.assertEqual(row, {"ids": ["a", "b"], "metadata": {"enabled": True}})

    def test_preserves_non_text_values(self):
        row = self.connection.execute("SELECT NULL AS missing, 42 AS count").fetchone()
        self.assertEqual(row, {"missing": None, "count": 42})


if __name__ == "__main__":
    unittest.main()
