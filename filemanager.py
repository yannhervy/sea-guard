import re
from datetime import datetime, timedelta
from pathlib import Path

def clean_old_logfiles(log_dir: Path, days=3):
    """
    Removes log files older than 'days' from the specified directory.
    Log files must be named in the format 'YYYY-MM-DD_something.log'.
    """
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2})_.+\.log$")
    for file_path in log_dir.glob("*.log"):
        match = pattern.match(file_path.name)
        if match:
            file_date_str = match.group(1)
            file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
            if (datetime.now().date() - file_date).days > days:
                file_path.unlink()