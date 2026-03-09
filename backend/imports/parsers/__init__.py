"""Multi-format financial file parsers."""

import os

from imports.parsers.csv_parser import apply_mapping, detect_column_mapping, parse_csv
from imports.parsers.ofx_parser import parse_ofx
from imports.parsers.qif_parser import parse_qif

__all__ = [
    "parse_csv",
    "parse_ofx",
    "parse_qif",
    "parse_file",
    "detect_format",
    "apply_mapping",
    "detect_column_mapping",
]


def detect_format(filename: str) -> str:
    """Auto-detect file format from extension."""
    ext = os.path.splitext(filename)[1].lower()
    format_map = {
        ".csv": "csv",
        ".ofx": "ofx",
        ".qfx": "ofx",  # QFX is Quicken's OFX variant
        ".qif": "qif",
    }
    return format_map.get(ext, "csv")


def parse_file(file_content: str, filename: str) -> dict:
    """Parse a financial file, auto-detecting format from extension.

    Supports CSV, OFX/QFX, and QIF formats.
    """
    fmt = detect_format(filename)
    if fmt == "ofx":
        return parse_ofx(file_content)
    elif fmt == "qif":
        return parse_qif(file_content)
    return parse_csv(file_content)
