from app.discovery.file_discovery import FileDiscoveryService


def main():
    discovery_service = FileDiscoveryService()

    files = discovery_service.discover_files()

    print(f"\nTotal files discovered: {len(files)}")

    print("\nDiscovered files:")

    for file in files:
        print(file)


if __name__ == "__main__":
    main()
