import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class FileDiscoveryService:

    def __init__(self):
        input_directory = os.getenv("INPUT_DIRECTORY")

        if not input_directory:
            raise ValueError("INPUT_DIRECTORY is not configured.")

        self.input_directory = (BASE_DIR / input_directory).resolve()

    def discover_files(self) -> list[Path]:
        """
        Recursively discover all files inside the configured
        company source directory.
        """

        if not self.input_directory.exists():
            raise FileNotFoundError(
                f"Input directory not found: {self.input_directory}"
            )

        if not self.input_directory.is_dir():
            raise NotADirectoryError(
                f"Configured input path is not a directory: "
                f"{self.input_directory}"
            )

        discovered_files = [
            path
            for path in self.input_directory.rglob("*")
            if path.is_file()
        ]

        return sorted(discovered_files)
