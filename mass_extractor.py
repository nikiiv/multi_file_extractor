#!/usr/bin/env python3
import os
import zipfile
import rarfile
import argparse
from pathlib import Path

import faulthandler


faulthandler.enable()


def extract_archive(archive_path, extract_path):
    """
    Extract a single archive file (zip or rar) to the specified path.

    Args:
        archive_path (Path): Path to the archive file
        extract_path (Path): Path where files should be extracted

    Returns:
        bool: True if extraction was successful, False otherwise
    """
    try:
        if archive_path.suffix.lower() == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as archive:
                archive.extractall(extract_path)
        elif archive_path.suffix.lower() == '.rar':
            with rarfile.RarFile(archive_path, 'r') as archive:
                archive.extractall(extract_path)
        return True
    except Exception as e:
        print(f"Error processing {archive_path.name}: {str(e)}")
        return False


def extract_archives(folder_path, target_folder, num_files=None):
    """
    Extract zip and rar files from source folder to target folder, creating subdirectories
    matching archive file names (without extension).

    Args:
        folder_path (str): Path to folder containing archive files
        target_folder (str): Path where files should be extracted
        num_files (int, optional): Number of files to process. If None, process all files

    Returns:
        tuple: (processed_count, skipped_count)
    """
    # Convert paths to Path objects for better handling
    source_path = Path(folder_path)
    target_path = Path(target_folder)

    # Create target folder if it doesn't exist
    target_path.mkdir(parents=True, exist_ok=True)

    # Get list of archive files
    archive_files = list(source_path.glob('*.zip')) + list(source_path.glob('*.rar'))
    archive_files.sort()  # Sort to ensure consistent processing order

    # # Limit number of files if specified
    # if num_files is not None:
    #     archive_files = archive_files[:num_files]

    processed_count = 0
    skipped_count = 0

    for archive_file in archive_files:
        # Create target subfolder name by removing extension
        subfolder_name = archive_file.stem
        extract_path = target_path / subfolder_name

        # Skip if target folder already exists
        if extract_path.exists():
            print(f"Skipping {archive_file.name} - target folder already exists")
            skipped_count += 1
            continue

        print(f"{processed_count}/{num_files}. Extracting {archive_file.name} to {extract_path}")
        if extract_archive(archive_file, extract_path):
            processed_count += 1
        if processed_count >= num_files:
            break

    return processed_count, skipped_count


def main():
    parser = argparse.ArgumentParser(description='Extract zip and rar files to separate folders')
    parser.add_argument('-f','--folder', help='Source folder containing zip/rar files')
    parser.add_argument('-t','--target', help='Target folder for extracted files')
    parser.add_argument('-n', '--num_files', type=int, help='Number of files to process')

    args = parser.parse_args()

    processed, skipped = extract_archives(args.folder, args.target, args.num_files)
    print(f"\nExtraction complete:")
    print(f"Files processed: {processed}")
    print(f"Files skipped: {skipped}")


if __name__ == "__main__":
    main()