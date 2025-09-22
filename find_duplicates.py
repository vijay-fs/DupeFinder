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
import shutil
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

    def move_duplicates(self, duplicates, destination_dir, keep_first=True, dry_run=False):
        """
        Move duplicate files to destination directory while preserving folder structure

        Args:
            duplicates: Dictionary of duplicate groups from find_duplicates_* methods
            destination_dir: Path to destination directory for moved duplicates
            keep_first: If True, keep the first file in each group and move the rest
            dry_run: If True, only show what would be moved without actually moving

        Returns:
            Dictionary with move statistics and any errors
        """
        destination = Path(destination_dir)
        stats = {
            'moved_files': 0,
            'created_dirs': 0,
            'errors': [],
            'total_space_freed': 0,
            'moved_groups': 0
        }

        if not dry_run and not destination.exists():
            try:
                destination.mkdir(parents=True, exist_ok=True)
                stats['created_dirs'] += 1
                print(f"Created destination directory: {destination}")
            except OSError as e:
                stats['errors'].append(f"Could not create destination directory {destination}: {e}")
                return stats

        print(f"\n{'DRY RUN: ' if dry_run else ''}Moving duplicate files...")
        print(f"Destination: {destination.absolute()}")
        print(f"Strategy: {'Keep first file' if keep_first else 'Move all files'}")

        for group_key, files in duplicates.items():
            if len(files) < 2:
                continue

            stats['moved_groups'] += 1
            files_to_move = files[1:] if keep_first else files

            print(f"\nProcessing duplicate group: {group_key}")
            if keep_first and len(files) > 1:
                print(f"  Keeping: {files[0].path}")

            for file_info in files_to_move:
                try:
                    moved_successfully = self._move_single_file(
                        file_info, destination, dry_run, stats
                    )
                    if moved_successfully:
                        stats['moved_files'] += 1
                        stats['total_space_freed'] += file_info.size

                except Exception as e:
                    error_msg = f"Error moving {file_info.path}: {e}"
                    stats['errors'].append(error_msg)
                    print(f"  ERROR: {error_msg}")

        return stats

    def _move_single_file(self, file_info, destination_root, dry_run, stats):
        """
        Move a single file while preserving its directory structure

        Args:
            file_info: FileInfo object of file to move
            destination_root: Root destination directory
            dry_run: If True, only simulate the move
            stats: Statistics dictionary to update

        Returns:
            True if file was moved successfully, False otherwise
        """
        source_path = file_info.path.absolute()

        # Get the relative path from the file's original location
        # This preserves the folder structure
        try:
            # Try to get relative path from current working directory
            relative_path = source_path.relative_to(Path.cwd())
        except ValueError:
            # If file is outside current directory, use just the filename
            relative_path = source_path.name

        destination_path = destination_root / relative_path

        print(f"  {'[DRY RUN] ' if dry_run else ''}Moving: {source_path}")
        print(f"    -> {destination_path}")

        if dry_run:
            return True

        # Create destination directory if it doesn't exist
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle filename conflicts
        if destination_path.exists():
            destination_path = self._get_unique_filename(destination_path)
            print(f"    Renamed to avoid conflict: {destination_path.name}")

        try:
            shutil.move(str(source_path), str(destination_path))
            return True
        except (OSError, IOError) as e:
            raise Exception(f"Could not move file: {e}")

    def _get_unique_filename(self, file_path):
        """
        Generate a unique filename by appending a number if the file already exists

        Args:
            file_path: Path object of the target file

        Returns:
            Path object with unique filename
        """
        base_path = file_path.parent
        stem = file_path.stem
        suffix = file_path.suffix
        counter = 1

        while file_path.exists():
            new_name = f"{stem}_{counter}{suffix}"
            file_path = base_path / new_name
            counter += 1

        return file_path


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
  %(prog)s /path/to/directory --by-content --move-to ./duplicates
  %(prog)s /path/to/directory --by-content --move-to ./duplicates --dry-run
  %(prog)s /path/to/directory --by-content --move-to ./duplicates --move-all
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

    parser.add_argument(
        "--move-to",
        metavar="DIR",
        help="Move duplicate files to specified directory (preserving folder structure)"
    )

    parser.add_argument(
        "--move-all",
        action="store_true",
        help="Move all duplicate files (default: keep first file in each group)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be moved without actually moving files"
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
    all_duplicates = {}

    if args.all or args.by_content:
        duplicates = finder.find_duplicates_by_content()
        display_duplicates(duplicates, "DUPLICATES BY CONTENT", show_hash=True)
        if args.move_to:
            all_duplicates.update(duplicates)

    if args.all or args.by_size:
        duplicates = finder.find_duplicates_by_size()
        display_duplicates(duplicates, "DUPLICATES BY SIZE")
        if args.move_to and not args.by_content:  # Avoid duplicate moves
            all_duplicates.update(duplicates)

    if args.all or args.by_name:
        duplicates = finder.find_duplicates_by_name()
        display_duplicates(duplicates, "DUPLICATES BY FILENAME")
        if args.move_to and not (args.by_content or args.by_size):
            all_duplicates.update(duplicates)

    if args.all or args.by_stem:
        duplicates = finder.find_duplicates_by_stem()
        display_duplicates(duplicates, "DUPLICATES BY FILENAME (without extension)")
        if args.move_to and not (args.by_content or args.by_size or args.by_name):
            all_duplicates.update(duplicates)

    # Move duplicates if requested
    if args.move_to and all_duplicates:
        print(f"\n{'='*60}")
        print("MOVING DUPLICATE FILES")
        print(f"{'='*60}")

        move_stats = finder.move_duplicates(
            all_duplicates,
            args.move_to,
            keep_first=not args.move_all,
            dry_run=args.dry_run
        )

        print(f"\n{'='*60}")
        print("MOVE OPERATION SUMMARY")
        print(f"{'='*60}")
        print(f"Duplicate groups processed: {move_stats['moved_groups']}")
        print(f"Files moved: {move_stats['moved_files']}")
        print(f"Space freed: {format_file_size(move_stats['total_space_freed'])}")

        if move_stats['errors']:
            print(f"\nErrors encountered ({len(move_stats['errors'])}):")
            for error in move_stats['errors']:
                print(f"  - {error}")
    elif args.move_to:
        print("\nNo duplicate files found to move.")


if __name__ == "__main__":
    main()