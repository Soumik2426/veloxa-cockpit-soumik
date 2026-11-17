import re
from pathlib import Path


# Initial chunking configuration
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

# Markdown heading pattern
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")


def parse_frontmatter(markdown_text: str) -> tuple[dict, str]:
    """
    Extract metadata from the YAML-style frontmatter
    at the beginning of a Markdown document.

    Returns:
        metadata: Document metadata
        content: Markdown content without frontmatter
    """

    metadata = {}

    if not markdown_text.startswith("---"):
        return metadata, markdown_text

    parts = markdown_text.split("---", 2)

    if len(parts) != 3:
        return metadata, markdown_text

    frontmatter = parts[1]
    content = parts[2].strip()

    for line in frontmatter.strip().splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)

        metadata[key.strip()] = value.strip().strip('"').strip("'")

    return metadata, content


def extract_sections(markdown_text: str) -> list[dict]:
    """
    Divide Markdown content into sections using headings.

    Each section retains its heading hierarchy and content.
    """

    sections = []

    heading_stack = []
    current_content = []

    def save_section():
        content = "\n".join(current_content).strip()

        if content:
            sections.append({
                "heading": " > ".join(heading_stack),
                "content": content
            })

    for line in markdown_text.splitlines():

        match = HEADING_PATTERN.match(line)

        if match:
            save_section()
            current_content.clear()

            heading_level = len(match.group(1))
            heading_text = match.group(2).strip()

            heading_stack[:] = heading_stack[:heading_level - 1]
            heading_stack.append(heading_text)

        else:
            current_content.append(line)

    save_section()

    return sections


def create_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """
    Split text into word-based chunks with overlapping words.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size."
        )

    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):

        end = min(start + chunk_size, len(words))

        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        if end == len(words):
            break

        start = end - overlap

    return chunks


def chunk_markdown_file(
    file_path: Path,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> list[dict]:
    """
    Process one Markdown file and return chunks
    with their source metadata.
    """

    markdown_text = file_path.read_text(encoding="utf-8")

    document_metadata, content = parse_frontmatter(markdown_text)

    sections = extract_sections(content)

    document_chunks = []

    chunk_index = 0

    for section in sections:

        heading = section["heading"]
        section_content = section["content"]

        # Include the heading in every chunk for context.
        text_to_chunk = (
            f"{heading}\n\n{section_content}"
            if heading
            else section_content
        )

        chunks = create_chunks(
            text_to_chunk,
            chunk_size,
            overlap
        )

        for chunk in chunks:

            document_chunks.append({
                "chunk_index": chunk_index,
                "content": chunk,
                "word_count": len(chunk.split()),

                "metadata": {
                    "source_file_id": document_metadata.get(
                        "source_file_id"
                    ),
                    "source_file": document_metadata.get(
                        "source_file",
                        file_path.name
                    ),
                    "source_path": document_metadata.get(
                        "source_path",
                        str(file_path)
                    ),
                    "checksum": document_metadata.get("checksum"),
                    "document_type": document_metadata.get(
                        "document_type"
                    ),
                    "section": heading
                }
            })

            chunk_index += 1

    return document_chunks


def chunk_markdown_directory(
    directory: Path,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> list[dict]:
    """
    Process all Markdown files inside a directory recursively.
    """

    if not directory.exists():
        raise FileNotFoundError(
            f"Markdown directory not found: {directory}"
        )

    all_chunks = []

    markdown_files = sorted(directory.rglob("*.md"))

    for file_path in markdown_files:

        chunks = chunk_markdown_file(
            file_path,
            chunk_size,
            overlap
        )

        all_chunks.extend(chunks)

        print(
            f"Processed: {file_path.name} | "
            f"Chunks: {len(chunks)}"
        )

    return all_chunks


if __name__ == "__main__":

    # Resolve the project root.
    project_root = Path(__file__).resolve().parents[3]

    markdown_directory = (
        project_root / "data" / "processed" / "markdown"
    )

    chunks = chunk_markdown_directory(markdown_directory)

    print("\n========== CHUNKING SUMMARY ==========")
    print(f"Total chunks generated: {len(chunks)}")

    if chunks:

        print("\n========== SAMPLE CHUNK ==========")

        sample = chunks[0]

        print(f"Chunk Index: {sample['chunk_index']}")
        print(f"Word Count: {sample['word_count']}")
        print(f"Content:\n{sample['content']}")
        print(f"Metadata:\n{sample['metadata']}")
