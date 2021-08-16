import os
from pathlib import Path
from datetime import datetime, timedelta
from pytz import timezone
from config import settings

tz = timezone(settings.timezone)

base_dir = os.path.join(os.path.dirname(__file__),'../')

def get_all_file_paths(directory: str, exclude_filename: list = []) -> list:
    # initializing empty file paths list
    file_paths = []

    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            if filename not in exclude_filename:
                # join the two strings in order to form the full filepath.
                filepath = os.path.join(root, filename)
                created_at = datetime.fromtimestamp(Path(filepath).stat().st_mtime)
                file_paths.append((filepath, created_at))

    # returning all file paths
    file_paths.sort(key=lambda tup: tup[-1])
    return file_paths

def delete_file(path_file: str) -> None:
    if os.path.exists(path_file):
        os.remove(path_file)

def clear_qrcode_expired() -> None:
    time_now = datetime.now(tz).replace(tzinfo=None)
    three_day_ago = time_now - timedelta(days=3)

    qrcode_files = get_all_file_paths(os.path.join(base_dir,'static/qrcode/'), exclude_filename=['qrcode.png'])
    qrcode_files = [x for x in qrcode_files if x[-1].date() <= three_day_ago.date()]

    [delete_file(x[0]) for x in qrcode_files]
