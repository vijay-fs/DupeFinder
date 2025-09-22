# Duplicate File Finder

A powerful command-line tool to find duplicate files based on various criteria including content hash, file size, name, and metadata.

## Features

- **Content-based detection**: Uses SHA256 hashing for accurate duplicate detection
- **Size-based detection**: Quick identification of files with identical sizes
- **Name-based detection**: Find files with identical names across directories
- **Stem-based detection**: Find files with same name but different extensions
- **File type filtering**: Target specific file extensions
- **Recursive scanning**: Scan subdirectories automatically
- **Detailed output**: Shows file paths, sizes, timestamps, and MIME types
- **Wasted space calculation**: Reports total space consumed by duplicates

## Installation

No installation required. Just ensure you have Python 3.6+ installed.

```bash
# Make the script executable
chmod +x find_duplicates.py
```

## Usage

### Basic Usage

```bash
# Find content duplicates in current directory (default behavior)
python find_duplicates.py .

# Find duplicates in specific directory
python find_duplicates.py /path/to/directory
```

### Detection Methods

```bash
# Content-based detection (most accurate, slower)
python find_duplicates.py /path/to/directory --by-content

# Size-based detection (faster, may have false positives)
python find_duplicates.py /path/to/directory --by-size

# Name-based detection
python find_duplicates.py /path/to/directory --by-name

# Filename without extension
python find_duplicates.py /path/to/directory --by-stem

# Run all detection methods
python find_duplicates.py /path/to/directory --all
```

### File Type Filtering

```bash
# Find duplicate images only
python find_duplicates.py /path/to/photos --by-content --types .jpg .png .gif .jpeg

# Find duplicate documents
python find_duplicates.py /path/to/docs --by-content --types .pdf .doc .docx .txt

# Find duplicate videos
python find_duplicates.py /path/to/videos --by-content --types .mp4 .avi .mkv .mov
```

### Advanced Options

```bash
# Don't scan subdirectories
python find_duplicates.py /path/to/directory --no-recursive

# Combine multiple detection methods
python find_duplicates.py /path/to/directory --by-size --by-name --types .jpg .png
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `directory` | Directory to scan for duplicate files (required) |
| `--by-content` | Find duplicates by file content (hash comparison) |
| `--by-size` | Find duplicates by file size |
| `--by-name` | Find duplicates by filename |
| `--by-stem` | Find duplicates by filename without extension |
| `--all` | Run all duplicate detection methods |
| `--types EXT [EXT ...]` | Filter by file extensions (e.g., .jpg .png .txt) |
| `--no-recursive` | Don't scan subdirectories recursively |

## Output Format

The tool provides detailed information about duplicate files:

```
=============================================================
DUPLICATES BY CONTENT
=============================================================

Duplicate group (3 files):
  Hash: a1b2c3d4e5f6...
  Size: 2.5 MB
  [1] /home/user/photos/vacation/IMG_001.jpg
      Modified: 2024-03-15 14:30:25
      Type: image/jpeg
  [2] /home/user/backup/photos/IMG_001.jpg
      Modified: 2024-03-15 14:30:25
      Type: image/jpeg
  [3] /home/user/duplicates/copy_of_IMG_001.jpg
      Modified: 2024-03-16 09:15:42
      Type: image/jpeg
----------------------------------------

Summary:
  Total duplicate files: 2
  Total wasted space: 5.0 MB
```

## Detection Methods Explained

### Content-Based Detection (`--by-content`)
- **Most Accurate**: Uses SHA256 hashing to compare actual file content
- **Slower**: Reads entire file content for hashing
- **Best for**: Critical duplicate detection where accuracy is paramount
- **Use case**: Cleaning up photo libraries, important documents

### Size-Based Detection (`--by-size`)
- **Fast**: Only compares file sizes
- **May have false positives**: Different files can have same size
- **Best for**: Quick initial scan or when combined with other methods
- **Use case**: Finding obviously large duplicate files

### Name-Based Detection (`--by-name`)
- **Very Fast**: Only compares filenames
- **Useful for**: Finding files with identical names in different locations
- **Best for**: Organizing file systems, finding scattered copies
- **Use case**: Cleaning up downloads folder, organizing documents

### Stem-Based Detection (`--by-stem`)
- **Fast**: Compares filename without extension
- **Useful for**: Finding same content in different formats
- **Best for**: Media files that might be converted between formats
- **Use case**: Finding duplicate songs/videos in different formats

## Performance Tips

1. **For large directories**: Start with `--by-size` for a quick overview
2. **For photo libraries**: Use `--by-content --types .jpg .png .gif .jpeg`
3. **For documents**: Use `--by-content --types .pdf .doc .docx .txt`
4. **For quick cleanup**: Use `--by-name` to find obvious duplicates
5. **For comprehensive scan**: Use `--all` but be prepared for longer execution time

## Examples

### Find Duplicate Photos
```bash
python find_duplicates.py ~/Pictures --by-content --types .jpg .jpeg .png .gif .bmp
```

### Clean Up Downloads Folder
```bash
python find_duplicates.py ~/Downloads --by-name --by-size
```

### Comprehensive Media Scan
```bash
python find_duplicates.py /media/storage --all --types .mp4 .avi .mkv .mp3 .flac
```

### Quick Size-Based Scan
```bash
python find_duplicates.py /large/directory --by-size --no-recursive
```

## Requirements

- Python 3.6 or higher
- Standard library modules only (no external dependencies)

## License

This tool is provided as-is for educational and personal use.