#!/usr/bin/env python3
"""
Duplicate File Finder
A command-line tool to find duplicate files based on various criteria including
content hash, file size, name, and metadata.
"""

import os
import sys
import hashlib
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import mimetypes


class FileInfo:
    """Class to store file information for comparison"""

    def __init__(self, filepath):
        self.path = Path(filepath)
        self.size = self.path.stat().st_size
        self.name = self.path.name
        self.stem = self.path.stem
        self.suffix = self.path.suffix
        self.modified_time = self.path.stat().st_mtime
        self.mime_type = mimetypes.guess_type(str(self.path))[0]
        self._hash = None

    @property
    def hash(self):
        """Lazy computation of file hash"""
        if self._hash is None:
            self._hash = self._calculate_hash()
        return self._hash

    def _calculate_hash(self):
        """Calculate SHA256 hash of file content"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(self.path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (IOError, OSError) as e:
            print(f"Warning: Could not read {self.path}: {e}")
            return None


class DuplicateFinder:
    """Main class for finding duplicate files"""

    def __init__(self):
        self.files = []

    def scan_directory(self, directory, recursive=True, file_types=None):
        """Scan directory for files"""
        path = Path(directory)
        if not path.exists():
            print(f"Error: Directory '{directory}' does not exist")
            return

        if not path.is_dir():
            print(f"Error: '{directory}' is not a directory")
            return

        pattern = "**/*" if recursive else "*"

        try:
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    # Filter by file types if specified
                    if file_types:
                        if not any(file_path.suffix.lower() == ext.lower() for ext in file_types):
                            continue

                    try:
                        file_info = FileInfo(file_path)
                        self.files.append(file_info)
                    except (OSError, IOError) as e:
                        print(f"Warning: Could not process {file_path}: {e}")
        except (OSError, IOError, PermissionError) as e:
            print(f"Warning: Error scanning directory structure: {e}")
            print("Attempting alternative scanning method...")
            # Fallback to os.walk for problematic directory structures
            self._scan_with_walk(path, recursive, file_types)

    def _scan_with_walk(self, root_path, recursive, file_types):
        """Alternative scanning method using os.walk for problematic directories"""
        try:
            if recursive:
                for root, dirs, files in os.walk(str(root_path)):
                    for file_name in files:
                        file_path = Path(root) / file_name
                        self._process_file(file_path, file_types)
            else:
                try:
                    for item in os.listdir(str(root_path)):
                        item_path = root_path / item
                        if item_path.is_file():
                            self._process_file(item_path, file_types)
                except (OSError, IOError) as e:
                    print(f"Warning: Could not list directory contents: {e}")
        except (OSError, IOError, PermissionError) as e:
            print(f"Warning: Could not scan with fallback method: {e}")

    def _process_file(self, file_path, file_types):
        """Process a single file with error handling"""
        try:
            # Filter by file types if specified
            if file_types:
                if not any(file_path.suffix.lower() == ext.lower() for ext in file_types):
                    return

            file_info = FileInfo(file_path)
            self.files.append(file_info)
        except (OSError, IOError, UnicodeDecodeError, ValueError) as e:
            print(f"Warning: Could not process {file_path}: {e}")

    def find_duplicates_by_content(self):
        """Find duplicates based on file content hash"""
        hash_groups = defaultdict(list)

        print("Calculating file hashes...")
        for i, file_info in enumerate(self.files, 1):
            print(f"\rProgress: {i}/{len(self.files)}", end="", flush=True)

            if file_info.hash:
                hash_groups[file_info.hash].append(file_info)

        print()  # New line
        return {hash_val: files for hash_val, files in hash_groups.items() if len(files) > 1}

    def find_duplicates_by_size(self):
        """Find duplicates based on file size"""
        size_groups = defaultdict(list)

        for file_info in self.files:
            size_groups[file_info.size].append(file_info)

        return {size: files for size, files in size_groups.items() if len(files) > 1}

    def find_duplicates_by_name(self):
        """Find duplicates based on filename"""
        name_groups = defaultdict(list)

        for file_info in self.files:
            name_groups[file_info.name].append(file_info)

        return {name: files for name, files in name_groups.items() if len(files) > 1}

    def find_duplicates_by_stem(self):
        """Find duplicates based on filename without extension"""
        stem_groups = defaultdict(list)

        for file_info in self.files:
            stem_groups[file_info.stem].append(file_info)

        return {stem: files for stem, files in stem_groups.items() if len(files) > 1}


def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def format_timestamp(timestamp):
    """Convert timestamp to readable format"""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def display_duplicates(duplicates, title, show_hash=False):
    """Display duplicate files in a formatted way"""
    if not duplicates:
        print(f"\n{title}: No duplicates found")
        return

    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

    total_duplicates = 0
    total_wasted_space = 0

    for key, files in duplicates.items():
        if len(files) < 2:
            continue

        total_duplicates += len(files) - 1
        file_size = files[0].size
        total_wasted_space += file_size * (len(files) - 1)

        print(f"\nDuplicate group ({len(files)} files):")
        if show_hash:
            print(f"  Hash: {key}")
        else:
            print(f"  Key: {key}")
        print(f"  Size: {format_file_size(file_size)}")

        for i, file_info in enumerate(files, 1):
            print(f"  [{i}] {file_info.path.absolute()}")
            print(f"      Modified: {format_timestamp(file_info.modified_time)}")
            if file_info.mime_type:
                print(f"      Type: {file_info.mime_type}")
        print("-" * 40)

    print(f"\nSummary:")
    print(f"  Total duplicate files: {total_duplicates}")
    print(f"  Total wasted space: {format_file_size(total_wasted_space)}")


def main():
    parser = argparse.ArgumentParser(
        description="Find duplicate files based on various criteria",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/directory --by-content
  %(prog)s /path/to/directory --by-size --by-name
  %(prog)s /path/to/directory --by-content --types .jpg .png .gif
  %(prog)s /path/to/directory --all --no-recursive
        """
    )

    parser.add_argument(
        "directory",
        help="Directory to scan for duplicate files"
    )

    parser.add_argument(
        "--by-content",
        action="store_true",
        help="Find duplicates by file content (hash comparison)"
    )

    parser.add_argument(
        "--by-size",
        action="store_true",
        help="Find duplicates by file size"
    )

    parser.add_argument(
        "--by-name",
        action="store_true",
        help="Find duplicates by filename"
    )

    parser.add_argument(
        "--by-stem",
        action="store_true",
        help="Find duplicates by filename without extension"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all duplicate detection methods"
    )

    parser.add_argument(
        "--types",
        nargs="+",
        metavar="EXT",
        help="Filter by file extensions (e.g., .jpg .png .txt)"
    )

    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't scan subdirectories recursively"
    )

    args = parser.parse_args()

    # If no specific method is chosen, default to content-based detection
    if not any([args.by_content, args.by_size, args.by_name, args.by_stem, args.all]):
        args.by_content = True

    # Initialize finder
    finder = DuplicateFinder()

    print(f"Scanning directory: {args.directory}")
    if args.types:
        print(f"Filtering file types: {', '.join(args.types)}")

    # Scan directory
    finder.scan_directory(
        args.directory,
        recursive=not args.no_recursive,
        file_types=args.types
    )

    print(f"Found {len(finder.files)} files to analyze")

    if not finder.files:
        print("No files found to analyze")
        return

    # Find duplicates based on selected criteria
    if args.all or args.by_content:
        duplicates = finder.find_duplicates_by_content()
        display_duplicates(duplicates, "DUPLICATES BY CONTENT", show_hash=True)

    if args.all or args.by_size:
        duplicates = finder.find_duplicates_by_size()
        display_duplicates(duplicates, "DUPLICATES BY SIZE")

    if args.all or args.by_name:
        duplicates = finder.find_duplicates_by_name()
        display_duplicates(duplicates, "DUPLICATES BY FILENAME")

    if args.all or args.by_stem:
        duplicates = finder.find_duplicates_by_stem()
        display_duplicates(duplicates, "DUPLICATES BY FILENAME (without extension)")


if __name__ == "__main__":
    main()