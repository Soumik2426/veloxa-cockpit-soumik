from app.discovery.file_discovery import FileDiscoveryService
from app.ingestion.services.file_fingerprint import FileFingerprintService


def main():
    discovery_service = FileDiscoveryService()
    fingerprint_service = FileFingerprintService()

    files = discovery_service.discover_files()

    print(f"\nCalculating checksums for {len(files)} files...\n")

    for file_path in files:
        checksum = fingerprint_service.calculate_checksum(file_path)

        print(f"File: {file_path.name}")
        print(f"SHA-256: {checksum}\n")


if __name__ == "__main__":
    main()
