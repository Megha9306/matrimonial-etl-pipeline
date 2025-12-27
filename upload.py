import os
import pathlib
import shutil
import glob
from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt"}


def upload_file(source_path, destination_folder):
    """
    Upload a single file to a destination folder
    
    Args:
        source_path: Path to the source file
        destination_folder: Path to destination folder
    """
    source = Path(source_path)
    destination = Path(destination_folder)
    
    if not source.exists():
        print(f"Error: Source file '{source_path}' does not exist")
        return False
    
    if source.suffix.lower() not in ALLOWED_EXTENSIONS:
        print(f"Unsupported file type: {source.suffix}")
        return False
    
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination / source.name)
    print(f"✓ File uploaded: {source.name}")
    return True

def upload_folder(source_folder, destination_parent):
    """
    Upload an entire folder to a destination parent folder
    
    Args:
        source_folder: Path to the source folder
        destination_parent: Path to parent destination folder
    """
    source = Path(source_folder)
    destination_parent = Path(destination_parent)
    
    if not source.exists():
        print(f"Error: Source folder '{source_folder}' does not exist")
        return False
    
    destination = destination_parent / source.name
    destination.mkdir(parents=True, exist_ok=True)
    
    for item in source.rglob("*"):
        if item.is_file() and item.suffix.lower() in ALLOWED_EXTENSIONS:
            shutil.copy2(item, destination / item.name)
    
    shutil.copytree(source, destination, dirs_exist_ok=True)
    print(f"✓ Folder uploaded: {source.name}")
    return True




def upload_multiple_files(source_pattern, destination_folder):
    """
    Upload multiple files matching a pattern
    
    Args:
        source_pattern: Glob pattern (e.g., '/path/*.csv')
        destination_folder: Path to destination folder
    """
    destination = Path(destination_folder)
    destination.mkdir(parents=True, exist_ok=True)
    
    files = glob.glob(source_pattern)
    if not files:
        print(f"No files found matching pattern: {source_pattern}")
        return False
    
    for file in files:
        file_path = Path(file)
        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            print(f"Skipped unsupported file: {file_path.name}")
            continue

    shutil.copy2(file_path, destination / file_path.name)
    print(f"✓ Uploaded: {file_path.name}")

    
    success_count = 0
    failed_files = []

    for file in files:
        file_path = Path(file)
        try:
            shutil.copy2(file_path, destination / file_path.name)
            print(f"✓ Uploaded: {file_path.name}")
            success_count += 1
        except Exception as e:
            print(f"✗ Failed to upload {file_path.name}: {e}")
            failed_files.append(file_path.name)

        print(f"\nTotal successful uploads: {success_count}")
        print(f"Total failed uploads: {len(failed_files)}")




# Example usage:
# upload_file('C:/path/to/file.csv', './input')
upload_file(r'C:\Users\Dell\OneDrive\Desktop\Matrimonial\Data\biodata\pareek_new_data_stage_4.txt', './input')
# upload_multiple_files('C:/path/*.csv', './input')