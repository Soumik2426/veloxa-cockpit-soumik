"""Request-scoped document conversion and ingestion for the existing RAG flow."""

import json
import hashlib
import os
from email import policy
from email.parser import BytesParser
from pathlib import Path, PurePosixPath
from uuid import UUID

import pymupdf
from dotenv import load_dotenv
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.rag.chunker import chunk_markdown_file
from app.rag.embeddings import generate_embeddings
from app.rag.vector_store import get_connection, save_chunks


AI_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = AI_ROOT.parent

load_dotenv(AI_ROOT / ".env")

_input_setting = os.getenv("INPUT_DIRECTORY", "data/input")
INPUT_DIRECTORY = (AI_ROOT / _input_setting).resolve()

MARKDOWN_DIRECTORY = PROJECT_ROOT / "data" / "processed" / "markdown"

SUPPORTED_TYPES = {"PDF", "WORD", "TEXT", "EMAIL"}


def resolve_source(relative_path: str, file_type: str) -> Path:
    if (
        not relative_path
        or "\\" in relative_path
        or ":" in relative_path
    ):
        raise ValueError(
            "relative_path must be a normalized relative path"
        )

    relative = PurePosixPath(relative_path)

    if (
        relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ValueError(
            "relative_path must stay inside the configured input directory"
        )

    source = (INPUT_DIRECTORY / Path(*relative.parts)).resolve()

    if not source.is_relative_to(INPUT_DIRECTORY):
        raise ValueError(
            "Document path escapes the configured input directory"
        )

    if not source.is_file():
        raise FileNotFoundError(
            f"Document not found: {relative_path}"
        )

    expected_suffixes = {
        "PDF": {".pdf"},
        "WORD": {".doc", ".docx"},
        "TEXT": {".txt"},
        "EMAIL": {".eml"},
    }

    if (
        file_type not in SUPPORTED_TYPES
        or source.suffix.lower() not in expected_suffixes[file_type]
    ):
        raise ValueError(
            "file_type does not match a supported document extension"
        )

    return source


def _escape_cell(value: str) -> str:
    return (
        value.replace("|", "\\|")
        .replace("\n", " ")
        .replace("\r", " ")
    )


def _word_paragraph(paragraph: Paragraph) -> str:
    text = paragraph.text.strip()

    if not text:
        return ""

    style = paragraph.style.name

    if style.startswith("Heading "):
        try:
            level = max(1, min(int(style.split()[-1]), 6))
            return f"{'#' * level} {text}"
        except ValueError:
            pass

    if style == "Title":
        return f"# {text}"

    if style == "Subtitle":
        return f"### {text}"

    return text


def _word_table(table: Table) -> str:
    rows = [
        [_escape_cell(cell.text.strip()) for cell in row.cells]
        for row in table.rows
    ]

    if not rows:
        return ""

    columns = max(map(len, rows))

    rows = [
        row + [""] * (columns - len(row))
        for row in rows
    ]

    rendered = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join(["---"] * columns) + " |",
    ]

    rendered.extend(
        "| " + " | ".join(row) + " |"
        for row in rows[1:]
    )

    return "\n".join(rendered)


def _email_body(message) -> str:
    plain, html = [], []

    parts = (
        message.walk()
        if message.is_multipart()
        else [message]
    )

    for part in parts:
        if (
            part.get_content_maintype() == "multipart"
            or part.get_content_disposition() == "attachment"
        ):
            continue

        if part.get_content_type() not in {
            "text/plain",
            "text/html",
        }:
            continue

        try:
            content = part.get_content()
        except Exception:
            continue

        if isinstance(content, str):
            (
                plain
                if part.get_content_type() == "text/plain"
                else html
            ).append(content)

    return "\n\n".join(plain or html).strip()


def convert_document(document: dict, source: Path) -> str:
    file_type = document["file_type"]
    name = document["file_name"]

    body = []

    if file_type == "PDF":
        with pymupdf.open(source) as pdf:
            for number, page in enumerate(pdf, 1):
                content = page.get_text("text").strip()

                if content:
                    body.extend([
                        f"## Page {number}",
                        "",
                        content,
                        "",
                    ])

    elif file_type == "WORD":
        doc = Document(source)

        for block in doc.iter_inner_content():
            content = (
                _word_paragraph(block)
                if isinstance(block, Paragraph)
                else _word_table(block)
                if isinstance(block, Table)
                else ""
            )

            if content:
                body.extend([content, ""])

    elif file_type == "TEXT":
        try:
            content = source.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            content = source.read_text(
                encoding="cp1252",
                errors="replace",
            )

        body.extend([content, ""])

    elif file_type == "EMAIL":
        with source.open("rb") as stream:
            message = BytesParser(
                policy=policy.default
            ).parse(stream)

        subject = str(message.get("Subject", "")) or name

        attachments = []

        if message.is_multipart():
            for part in message.walk():
                if part.get_content_disposition() == "attachment":
                    payload = part.get_payload(decode=True) or b""

                    attachments.append(
                        f"- **{part.get_filename() or 'Unnamed attachment'}** "
                        f"({part.get_content_type()}, {len(payload)} bytes)"
                    )

        body.extend([
            f"# {subject}",
            "",
            "## Email Metadata",
            "",
            f"- **From:** {message.get('From', '')}",
            f"- **To:** {message.get('To', '')}",
            f"- **CC:** {message.get('Cc', '')}",
            f"- **Date:** {message.get('Date', '')}",
            f"- **Message ID:** {message.get('Message-ID', '')}",
            "",
            "## Email Body",
            "",
            _email_body(message) or "_No email body found._",
            "",
        ])

        if attachments:
            body.extend([
                "## Attachments",
                "",
                *attachments,
                "",
            ])

    # IMPORTANT:
    # Do not treat Markdown metadata or a filename heading as
    # successfully extracted document content.
    #
    # This check applies to PDF, Word and TXT documents.
    # Email metadata is retained because it can itself be useful.
    if file_type != "EMAIL" and not any(
        line.strip() for line in body
    ):
        raise ValueError(
            "Document extraction produced no usable content."
        )

    metadata = [
        "---",
        f"source_file_id: {document['file_id']}",
        f"source_file: {json.dumps(name)}",
        f"source_path: {json.dumps(document['relative_path'])}",
        f"checksum: {document['checksum']}",
        f"document_type: {file_type}",
        "---",
        "",
    ]

    if file_type != "EMAIL":
        metadata.extend([
            f"# {name}",
            "",
        ])

    return "\n".join(metadata + body)


def has_unchanged_chunks(file_id: UUID, checksum: str) -> bool:
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM document_chunks
                WHERE ingestion_file_id = %s
                  AND metadata->>'checksum' = %s
                LIMIT 1
                """,
                (file_id, checksum),
            )

            return cursor.fetchone() is not None

    finally:
        connection.close()


def process_document(document: dict) -> dict:
    file_id = UUID(document["file_id"])

    source = resolve_source(
        document["relative_path"],
        document["file_type"],
    )

    actual_checksum = hashlib.sha256(
        source.read_bytes()
    ).hexdigest()

    if actual_checksum.lower() != document["checksum"].lower():
        raise ValueError(
            "Document checksum does not match the registered reference"
        )

    if has_unchanged_chunks(file_id, document["checksum"]):
        return {
            "file_id": str(file_id),
            "status": "skipped_unchanged",
            "chunks": 0,
            "embeddings": 0,
        }

    markdown = convert_document(document, source)

    relative_output = Path(
        *PurePosixPath(document["relative_path"]).parts
    ).with_suffix(".md")

    output = (
        MARKDOWN_DIRECTORY / relative_output
    ).resolve()

    if not output.is_relative_to(MARKDOWN_DIRECTORY.resolve()):
        raise ValueError(
            "Markdown output path escapes the configured output directory"
        )

    output.parent.mkdir(parents=True, exist_ok=True)

    temp_output = output.with_name(output.name + ".tmp")

    temp_output.write_text(
        markdown,
        encoding="utf-8",
    )

    try:
        chunks = chunk_markdown_file(temp_output)

        # -----------------------------------------------------
        # SAFEGUARD 1:
        # Remove empty or invalid chunk content.
        # -----------------------------------------------------

        chunks = [
            chunk
            for chunk in chunks
            if isinstance(chunk.get("content"), str)
            and chunk["content"].strip()
        ]

        # -----------------------------------------------------
        # SAFEGUARD 2:
        # Never replace existing chunks with an empty extraction.
        # -----------------------------------------------------

        if not chunks:
            raise ValueError(
                "Document extraction produced no usable chunks. "
                "Existing document chunks were preserved."
            )

        for chunk in chunks:
            chunk["metadata"]["source_path"] = (
                document["relative_path"]
            )

            chunk["metadata"]["source_file"] = (
                document["file_name"]
            )

            chunk["metadata"]["source_file_id"] = str(file_id)

            chunk["metadata"]["checksum"] = (
                document["checksum"]
            )

            chunk["metadata"]["document_type"] = (
                document["file_type"]
            )

        # -----------------------------------------------------
        # Generate embeddings in batches of 10.
        # -----------------------------------------------------

        processed = []

        for start in range(0, len(chunks), 10):
            batch = chunks[start:start + 10]

            embeddings = generate_embeddings([
                chunk["content"]
                for chunk in batch
            ])

            if (
                len(embeddings) != len(batch)
                or any(
                    len(vector) != 768
                    for vector in embeddings
                )
            ):
                raise ValueError(
                    "Embedding count or dimension did not match generated chunks"
                )

            processed.extend(
                {
                    **chunk,
                    "embedding": vector,
                }
                for chunk, vector in zip(batch, embeddings)
            )

        # -----------------------------------------------------
        # SAFEGUARD 3:
        # Do not save an empty embedding result.
        # -----------------------------------------------------

        if not processed:
            raise ValueError(
                "No embeddings were generated. "
                "Existing document chunks were preserved."
            )

        # save_chunks performs the existing transactional replacement.
        save_chunks(processed)

        temp_output.replace(output)

        return {
            "file_id": str(file_id),
            "status": "processed",
            "chunks": len(chunks),
            "embeddings": len(processed),
        }

    finally:
        if temp_output.exists():
            temp_output.unlink()


def clear_document_chunks(file_id: UUID, source_path: str) -> None:
    """
    Explicitly clear chunks for a document.

    This function is retained for existing callers.
    It is intentionally not called during normal document processing.
    """

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM document_chunks
                WHERE ingestion_file_id = %s
                   OR metadata->>'source_path' = %s
                """,
                (file_id, source_path),
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
