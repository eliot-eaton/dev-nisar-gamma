#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


# Matches timestamps such as:
# _20260625T114338_
TIMESTAMP_PATTERN = re.compile(r"_(\d{8})T\d{6}(?:_|$)")


def get_acquisition_date(filename: str) -> str | None:
    """Return the first YYYYMMDD acquisition date found in a NISAR filename."""
    match = TIMESTAMP_PATTERN.search(filename)
    return match.group(1) if match else None


def unique_destination(destination: Path) -> Path:
    """
    Avoid overwriting an existing file.

    Example:
        product.h5 -> product_1.h5
    """
    if not destination.exists():
        return destination

    suffixes = "".join(destination.suffixes)
    base_name = (
        destination.name[: -len(suffixes)]
        if suffixes
        else destination.name
    )

    counter = 1
    while True:
        candidate = destination.with_name(
            f"{base_name}_{counter}{suffixes}"
        )
        if not candidate.exists():
            return candidate
        counter += 1


def sort_nisar_files(
    source_directory: Path,
    output_directory: Path,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Sort NISAR files into output_directory/YYYYMMDD/ directories."""
    moved_count = 0
    skipped_count = 0

    if not source_directory.is_dir():
        raise NotADirectoryError(
            f"Source directory does not exist: {source_directory}"
        )

    for item in sorted(source_directory.iterdir()):
        # Only process files in the source directory.
        if not item.is_file():
            continue

        acquisition_date = get_acquisition_date(item.name)

        if acquisition_date is None:
            print(f"Skipping: no acquisition date found: {item.name}")
            skipped_count += 1
            continue

        date_directory = output_directory / acquisition_date
        destination = unique_destination(date_directory / item.name)

        if dry_run:
            print(f"Would move: {item} -> {destination}")
        else:
            date_directory.mkdir(parents=True, exist_ok=True)
            shutil.move(str(item), str(destination))
            print(f"Moved: {item.name} -> {destination}")

        moved_count += 1

    return moved_count, skipped_count


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sort downloaded NISAR files into "
            "h5s/YYYYMMDD/ directories."
        )
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=".",
        type=Path,
        help="Directory containing downloaded files; default: current directory",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="h5s",
        type=Path,
        help="Top-level output directory; default: h5s",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned moves without changing any files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    source_directory = args.source.expanduser().resolve()

    if args.output.is_absolute():
        output_directory = args.output.expanduser().resolve()
    else:
        output_directory = source_directory / args.output

    try:
        moved, skipped = sort_nisar_files(
            source_directory=source_directory,
            output_directory=output_directory,
            dry_run=args.dry_run,
        )
    except (OSError, shutil.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    action = "would be moved" if args.dry_run else "moved"
    print(f"\nFinished: {moved} file(s) {action}; {skipped} skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
