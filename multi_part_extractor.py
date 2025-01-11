#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Unpack zip/rar/7z (including multi-part) archives, "
                    "skipping secondary parts (e.g., .r01, .z01, .7z.002). "
                    "Only the main/core archive is extracted."
    )
    parser.add_argument(
        '-f', '--folder',
        required=True,
        help='Path to folder containing archive files.'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Path to output folder.'
    )
    parser.add_argument(
        '-t', '--tmp_dir',
        default='/tmp/unpack_folder',
        help='Path to temporary folder for extraction.'
    )
    parser.add_argument(
        '-n', '--num_files',
        type=int,
        default=0,
        help='Number of archives to process. 0 means no limit.'
    )
    return parser.parse_args()


def is_core_archive(file_path: Path) -> bool:
    """
    Return True if file is considered the "core" part of an archive.
    - Single-part WinRAR: .rar
    - Single-part WinZip: .zip
    - Single-part 7-Zip: .7z
    - Multi-part 7-Zip: .7z.001 (treated as core)

    Everything else like .r00, .r01, .z01, .7z.002, etc. is skipped.
    """
    filename = file_path.name.lower()

    # If it is just .rar, .zip, or .7z, treat as core archive
    if filename.endswith('.rar') or filename.endswith('.zip') or filename.endswith('.7z'):
        return True

    # Special case for multi-part 7z (like data.7z.001 as the first part)
    # Some 7z multi-part splits start at .7z.001, .7z.002, etc.
    # We'll treat .7z.001 as the "core."
    if re.search(r'\.7z\.001$', filename):
        return True

    return False


def extract_archive(archive_path: Path, tmp_dir: Path):
    """
    Extracts an archive to tmp_dir using external commands.
    Adjust as needed for different archive types.
    """
    tmp_dir.mkdir(parents=True, exist_ok=True)

    filename = archive_path.name.lower()

    # Use 7z for most things, but we’ll try specialized tools for .rar and .zip
    if filename.endswith('.zip'):
        cmd = ['unzip', '-o', str(archive_path), '-d', str(tmp_dir)]
    elif filename.endswith('.rar'):
        cmd = ['unrar', 'x', '-o+', str(archive_path), str(tmp_dir)]
    else:
        # Fallback: 7z can handle .7z, .7z.001, .gz, .tar, etc.
        # It's also possible to handle .zip and .rar with 7z if you prefer.
        cmd = ['7z', 'x', '-y', f'-o{tmp_dir}', str(archive_path)]

    print(f"[INFO] Extracting {archive_path} ...")
    try:
        # subprocess.run(cmd, check=True)
        subprocess.run(cmd, stdout=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Extraction failed for {archive_path}: {e}")


def move_non_archives(src_dir: Path, dest_dir: Path):
    """
    Moves non-archive files from src_dir to dest_dir (recursively).
    Also, skip any known multi-part splits (like .r01, .z01, .7z.002, etc.).
    This ensures we do NOT copy those "split" files into output.
    """
    # Pattern for multi-part splits we do NOT want to copy:
    skip_patterns = [
        r'\.r\d+$',  # .r00, .r01, .r02, ...
        r'\.\d{3}$',  # .001, .002, .003, ...
        r'\.z\d{2}$',  # .z01, .z02, .z03, ...
        r'\.7z\.\d{3}$'  # .7z.001, .7z.002, .7z.003, ...
    ]
    skip_regex = re.compile('|'.join(skip_patterns), re.IGNORECASE)

    for root, dirs, files in os.walk(src_dir):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(src_dir)
            # target_path = dest_dir  / rel_path
            target_path = dest_dir

            # If it’s a known split part, skip it.
            if skip_regex.search(file.lower()):
                #print(f"[INFO] Skipping multi-part segment: {file_path}")
                continue

            # If it's an archive but not a "core" archive, skip it as well.
            if is_core_archive(file_path):
                # We only want to move non-archives here, so skip .rar/.zip/.7z
                print(f"[INFO] Skipping core archive: {file_path}")
                continue

            # Otherwise, move the file
            print(f"[INFO] Moving file: {file_path} to {target_path}")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file_path), str(target_path))


def recursively_extract(tmp_dir: Path, dest_folder: Path):
    """
    Recursively finds "core" archives in tmp_dir and extracts them in-place
    until there are no more core archives to extract.
    """
    something_extracted = True
    while something_extracted:
        something_extracted = False
        archives = []

        # Gather all "core" archives in the tmp_dir
        for root, dirs, files in os.walk(tmp_dir):
            for f in files:
                p = Path(root) / f
                if is_core_archive(p):
                    archives.append(p)

        if not archives:
            break

        for archive in archives:
            #extract_archive(archive, archive.parent)  # extract in place
            extract_archive(archive, dest_folder)  # extract directly to outut
            # After extraction, remove the original archive file
            try:
                archive.unlink()
            except Exception as e:
                print(f"[WARNING] Could not delete archive {archive}: {e}")
            something_extracted = True


def main():
    args = parse_args()

    input_folder = Path(args.folder)
    output_folder = Path(args.output)
    tmp_dir = Path(args.tmp_dir)
    max_files = args.num_files

    # Create output folder if it doesn't exist
    output_folder.mkdir(parents=True, exist_ok=True)

    # Collect the "core" archives from the input folder
    all_core_archives = []
    for file_path in input_folder.iterdir():
        if file_path.is_file() and is_core_archive(file_path):
            all_core_archives.append(file_path)

    processed_count = 0

    for archive_path in all_core_archives:
        if max_files and processed_count >= max_files:
            print(f"[INFO] Reached the limit of {max_files} files to process.")
            break

        # Derive a folder name from the archive's stem
        # (Note: for something like data.7z.001, .stem yields 'data.7z')
        # If you have complicated multi-dot files, you may want to handle differently.
        core_name = archive_path.stem
        dest_folder = output_folder / core_name

        if dest_folder.exists():
            print(f"[INFO] Skipping {archive_path.name}, already processed (folder exists).")
            continue

        print(f"[INFO] Processing {archive_path.name} ...")

        # 1. Clean tmp_dir
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        #Also create oputut_dir
        dest_folder.mkdir(parents=True, exist_ok=True)


        # 2. Extract the top-level archive to tmp_dir
        extract_archive(archive_path, tmp_dir)


        # 3. Recursively extract any nested core archives in tmp_dir
        recursively_extract(tmp_dir, dest_folder)

        # 4. Move non-archive (non-split) files into the destination folder
        #dest_folder.mkdir(parents=True, exist_ok=True)
        move_non_archives(tmp_dir, dest_folder)

        # 5. Clean up tmp_dir
        shutil.rmtree(tmp_dir, ignore_errors=True)

        processed_count += 1

    print(f"[INFO] Done. Processed {processed_count} archives.")


if __name__ == "__main__":
    main()
