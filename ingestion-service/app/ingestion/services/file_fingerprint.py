import hashlib
from pathlib import Path


class FileFingerprintService:

    CHUNK_SIZE = 1024 * 1024  # 1 MB

    def calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate the SHA-256 checksum of a file.

        Reads the file in chunks so large files
        do not need to be loaded entirely into memory.
        """

        sha256 = hashlib.sha256()

        with file_path.open("rb") as file:
            while chunk := file.read(self.CHUNK_SIZE):
                sha256.update(chunk)

        return sha256.hexdigest()
