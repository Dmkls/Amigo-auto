import os
import sys
from pathlib import Path

def create_directory(path: str | Path) -> bool:
    try:
        path = Path(path) if isinstance(path, str) else path

        if path.exists():
            return True

        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {str(e)}")
        return False

if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent.parent.absolute()
else:
    ROOT_DIR = Path(__file__).parent.parent.absolute()

LOG_DIR = os.path.join(ROOT_DIR, "log")
RESULTS_DIR = os.path.join(ROOT_DIR, "results")
CONFIGS_DIR = os.path.join(ROOT_DIR, "configs")

create_directory(LOG_DIR)
create_directory(RESULTS_DIR)

EMAILS_PATH = os.path.join(CONFIGS_DIR, 'emails.txt')
PROXIES_PATH = os.path.join(CONFIGS_DIR, "proxies.txt")
X_AUTH_TOKENS_PATH = os.path.join(CONFIGS_DIR, "x_tokens.txt")
FAILED_EMAILS_PATH = os.path.join(RESULTS_DIR, 'failed_emails.txt')
SUCCESS_EMAILS_PATH = os.path.join(RESULTS_DIR, 'success_emails.txt')
FAILED_CONNECT_X_TOKENS = os.path.join(RESULTS_DIR, 'failed_x_tokens.txt')
SUCCESS_CONNECT_X_TOKENS = os.path.join(RESULTS_DIR, 'success_x_tokens.txt')