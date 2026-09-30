from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from setup import copy_env_file_if_missing


class CopyEnvFileTests(unittest.TestCase):
    def test_copies_example_when_env_file_is_missing(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            env_example = directory / ".env.example"
            env_file = directory / ".env"
            env_example.write_text("OPENAI_API_KEY=\n", encoding="utf-8")

            copy_env_file_if_missing(env_example, env_file)

            self.assertEqual(env_file.read_text(encoding="utf-8"), "OPENAI_API_KEY=\n")

    def test_does_not_overwrite_existing_env_file(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            env_example = directory / ".env.example"
            env_file = directory / ".env"
            env_example.write_text("OPENAI_API_KEY=example\n", encoding="utf-8")
            env_file.write_text("OPENAI_API_KEY=secret\n", encoding="utf-8")

            copy_env_file_if_missing(env_example, env_file)

            self.assertEqual(env_file.read_text(encoding="utf-8"), "OPENAI_API_KEY=secret\n")


if __name__ == "__main__":
    unittest.main()
