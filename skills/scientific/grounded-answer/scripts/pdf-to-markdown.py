#!/usr/bin/env python3
"""Convert a local PDF with GPU VLM, enriched Docling, and a text fallback."""

from __future__ import annotations

import argparse
import importlib.util
import os
import shlex
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path


class ConversionError(Exception):
    """Raised when a converter cannot produce usable Markdown."""


def status(message: str) -> None:
    print(message, file=sys.stderr)


def install_command(package: str) -> str:
    """Return a pip command bound to the running Python interpreter."""
    return f"{shlex.quote(sys.executable)} -m pip install {shlex.quote(package)}"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a local PDF with GPU VLM, Docling, and a pypdf fallback."
    )
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the input PDF file.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path for the output Markdown file.",
    )
    return parser.parse_args(argv)


def validate_paths(input_path: Path, output_path: Path) -> tuple[Path, Path]:
    input_path = input_path.expanduser().resolve()
    output_path = output_path.expanduser().resolve()

    if not input_path.is_file():
        raise ConversionError(
            f"Input PDF does not exist or is not a file: {input_path}"
        )
    if input_path == output_path:
        raise ConversionError("Input and output paths must be different.")
    if output_path.exists() and output_path.is_dir():
        raise ConversionError(f"Output path is a directory: {output_path}")

    return input_path, output_path


def validate_pdf(input_path: Path) -> None:
    """Reject unreadable or encrypted input when pypdf is available."""
    if importlib.util.find_spec("pypdf") is None:
        return

    try:
        from pypdf import PdfReader

        reader = PdfReader(str(input_path))
    except Exception as error:
        raise ConversionError(f"Input is not a readable PDF: {error}") from error

    if reader.is_encrypted:
        raise ConversionError(
            "Input PDF is encrypted. Password-protected PDFs are not supported."
        )


def select_accelerator() -> str:
    """Return the best supported accelerator in CUDA, MPS, CPU priority order."""
    try:
        import torch
    except ImportError:
        return "cpu"

    if torch.cuda.is_available():
        return "cuda"

    mps = getattr(torch.backends, "mps", None)
    if mps is not None and mps.is_available():
        return "mps"

    return "cpu"


def convert_with_docling(input_path: Path, device: str) -> str:
    """Convert a PDF with OCR plus code and formula enrichment enabled."""
    from docling.datamodel.accelerator_options import AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    pipeline_options = PdfPipelineOptions(
        accelerator_options=AcceleratorOptions(device=device),
        do_code_enrichment=True,
        do_formula_enrichment=True,
    )
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    markdown = converter.convert(input_path).document.export_to_markdown()
    if not markdown.strip():
        raise ConversionError("Docling produced no Markdown content.")

    return markdown


def convert_with_vlm(input_path: Path, device: str) -> str:
    """Convert a PDF with the SmolDocling VLM on a GPU accelerator."""
    from docling.datamodel.accelerator_options import AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.pipeline.vlm_pipeline import VlmPipeline

    pipeline_options = VlmPipelineOptions(
        accelerator_options=AcceleratorOptions(device=device),
        vlm_options=VlmConvertOptions.from_preset("smoldocling"),
    )
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline,
                pipeline_options=pipeline_options,
            )
        }
    )
    markdown = converter.convert(input_path).document.export_to_markdown()
    if not markdown.strip():
        raise ConversionError("Docling VLM produced no Markdown content.")

    return markdown


def convert_with_pypdf(input_path: Path) -> str:
    """Extract text to page-delimited Markdown when Docling cannot convert."""
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise ConversionError(
            "pypdf is unavailable to the Python interpreter running this script: "
            f"{sys.executable}\nInstall it with: {install_command('pypdf')}"
        ) from error

    try:
        reader = PdfReader(str(input_path))
    except Exception as error:
        raise ConversionError(f"pypdf could not read the PDF: {error}") from error

    if reader.is_encrypted:
        raise ConversionError(
            "Input PDF is encrypted. Password-protected PDFs are not supported."
        )

    try:
        pages = list(reader.pages)
    except Exception as error:
        raise ConversionError(f"pypdf could not read the PDF pages: {error}") from error

    sections: list[str] = []
    found_text = False
    for page_number, page in enumerate(pages, start=1):
        try:
            text = (
                (page.extract_text() or "")
                .replace("\r\n", "\n")
                .replace("\r", "\n")
                .strip()
            )
        except Exception as error:
            raise ConversionError(
                f"pypdf could not extract text from page {page_number}: {error}"
            ) from error

        found_text = found_text or bool(text)
        sections.append(f"## Page {page_number}\n\n{text}")

    if not found_text:
        raise ConversionError("pypdf extracted no usable text from the PDF.")

    return "\n\n".join(sections) + "\n"


def convert(input_path: Path) -> tuple[str, str]:
    """Prefer GPU VLM, then Docling, then pypdf as a fallback."""
    if importlib.util.find_spec("docling") is None:
        status(
            "Docling is unavailable to the Python interpreter running this script: "
            f"{sys.executable}\nUsing pypdf fallback. Install Docling with: "
            f"{install_command('docling[vlm]')}"
        )
        return convert_with_pypdf(input_path), "pypdf"

    selected_device = select_accelerator()
    if selected_device != "cpu":
        status(f"Converting with SmolDocling VLM on {selected_device.upper()}.")
        try:
            return convert_with_vlm(input_path, selected_device), "docling-vlm"
        except Exception as error:  # noqa: BLE001 - VLM failures must trigger fallbacks.
            status(
                f"Docling VLM conversion on {selected_device.upper()} failed: {error}"
            )

    status(f"Converting with Docling on {selected_device.upper()}.")
    try:
        return convert_with_docling(input_path, selected_device), "docling"
    except Exception as error:  # noqa: BLE001 - Docling failures must trigger fallbacks.
        status(f"Docling conversion on {selected_device.upper()} failed: {error}")

    if selected_device != "cpu":
        status("Retrying Docling on CPU.")
        try:
            return convert_with_docling(input_path, "cpu"), "docling"
        except Exception as error:  # noqa: BLE001 - Docling failures must trigger fallbacks.
            status(f"Docling conversion on CPU failed: {error}")

    status("Using pypdf fallback.")
    return convert_with_pypdf(input_path), "pypdf"


def write_markdown(output_path: Path, markdown: str) -> None:
    """Atomically replace the output only after Markdown has been produced."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_path = tempfile.mkstemp(
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        text=True,
    )
    try:
        with os.fdopen(
            file_descriptor, "w", encoding="utf-8", newline="\n"
        ) as temporary_file:
            temporary_file.write(markdown)
        os.replace(temporary_path, output_path)
    except Exception:
        Path(temporary_path).unlink(missing_ok=True)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        input_path, output_path = validate_paths(args.input, args.output)
        validate_pdf(input_path)
        markdown, backend = convert(input_path)
        write_markdown(output_path, markdown)
    except ConversionError as error:
        status(f"Conversion failed: {error}")
        return 1
    except OSError as error:
        status(f"Conversion failed while writing output: {error}")
        return 1

    status(f"Wrote Markdown with {backend}: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
