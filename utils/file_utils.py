from configs.constants import EMAILS_PATH, X_AUTH_TOKENS_PATH, PROXIES_PATH
from configs.constants import SUCCESS_EMAILS_PATH, FAILED_EMAILS_PATH
from configs.constants import SUCCESS_CONNECT_X_TOKENS, FAILED_CONNECT_X_TOKENS

def read_file(path: str, add=''):
    with open(path, encoding='utf-8') as file:
        return [f"{add}{line.strip()}" for line in file]

def read_emails() -> list[str]:
    return read_file(EMAILS_PATH)

def read_x_tokens() -> list[str]:
    return read_file(X_AUTH_TOKENS_PATH)

def read_proxies() -> list[str]:
    return read_file(PROXIES_PATH, add='http://')

def write_failed_emails(private_key: str):
    with open(FAILED_EMAILS_PATH, 'a', encoding="utf-8") as f:
        f.write(f'{private_key}\n')

def write_success_emails(private_key: str):
    with open(SUCCESS_EMAILS_PATH, 'a', encoding="utf-8") as f:
        f.write(f'{private_key}\n')

def write_failed_x_tokens(private_key: str):
    with open(FAILED_CONNECT_X_TOKENS, 'a', encoding="utf-8") as f:
        f.write(f'{private_key}\n')

def write_success_x_tokens(private_key: str):
    with open(SUCCESS_CONNECT_X_TOKENS, 'a', encoding="utf-8") as f:
        f.write(f'{private_key}\n')
