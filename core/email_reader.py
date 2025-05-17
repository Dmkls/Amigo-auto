import asyncio
import imaplib
import email
from email.header import decode_header

from utils.log_utils import logger
from configs import config

EMAIL = "nhudau3@icloud.com"
APP_PASSWORD = "jwfr-scxp-nddn-kuke"
IMAP_SERVER = "imap.mail.me.com"
IMAP_PORT = 993


FOLDERS_TO_CHECK = ["INBOX", "Junk"]
TARGET_SUBJECT_KEYWORD = "Verify your email for Amigo"  # 🔍 <-- Измени по необходимости

def format_body(body: str):
    return body.split("**")[1]

def extract_email_content(msg):
    for part in msg.walk():
        content_type = part.get_content_type()
        content_disp = str(part.get("Content-Disposition", ""))

        if content_type == "text/plain" and "attachment" not in content_disp:
            payload = part.get_payload(decode=True)
            if payload:
                return payload.decode(part.get_content_charset() or "utf-8", errors="ignore")

        elif content_type == "message/rfc822":
            embedded_msg = part.get_payload(0)
            return extract_email_content(embedded_msg)

    return None


def fetch_emails_from_folder(mail, folder, current_email):
    typ, _ = mail.select(folder, readonly=True)
    if typ != "OK":
        logger.error(f"{email} | Не удалось открыть папку {folder}")
        return None

    typ, data = mail.uid('search', None, 'UNSEEN')  # Только непрочитанные письма
    if typ != 'OK' or not data or not data[0]:
        return None

    uids = data[0].split()

    last_uids = uids[-5:]

    for uid in reversed(last_uids):
        uid_str = uid.decode()

        typ, msg_data = mail.uid("fetch", uid_str, "(BODY.PEEK[])")
        if typ != "OK" or not msg_data:
            logger.error(f"{current_email} | Не удалось получить тело письма UID {uid_str}")
            continue

        for part in msg_data:
            if isinstance(part, tuple) and part[1]:
                try:
                    msg = email.message_from_bytes(part[1])

                    subject_raw, encoding = decode_header(msg.get("Subject"))[0]
                    subject = subject_raw.decode(encoding or 'utf-8', errors='ignore') if isinstance(subject_raw, bytes) else subject_raw

                    if TARGET_SUBJECT_KEYWORD.lower() in subject.lower():
                        body = extract_email_content(msg)
                        logger.success(f"{current_email} | Успешно найдено письмо от Amigo")
                        result, _ = mail.uid('store', uid, '+FLAGS', '(\\Seen)')
                        if result == "OK":
                            logger.info(f"Письмо UID {uid} помечено как прочитанное.")
                        else:
                            logger.error(f"Не удалось пометить письмо UID {uid}.")
                        return body

                except Exception as e:
                    logger.error(f"{current_email} | Ошибка разбора письма UID {uid_str}: {e}")
                break

    return None


async def get_verification_code(current_email: str, email_password=None):
    try:
        if config.SINGLE_IMAP_ACCOUNT:
            mail = imaplib.IMAP4_SSL(config.SINGLE_IMAP_SERVER, config.SINGLE_IMAP_PORT)
            mail.login(config.SINGLE_EMAIL, config.SINGLE_APP_PASSWORD)
        else:
            mail = imaplib.IMAP4_SSL(config.IMAP_SERVER, config.IMAP_PORT)
            mail.login(current_email, email_password)

        logger.info(f"{current_email} | Ожидаю письмо..")
        for attempt in range(10):
            logger.info(f"{current_email} | Попытка {attempt+1} / 10")
            for folder in FOLDERS_TO_CHECK:
                await asyncio.sleep(10)
                body = fetch_emails_from_folder(mail, folder, current_email)
                if body:
                    mail.logout()
                    return format_body(body)
            else:
                logger.error(f"{current_email} | Подходящее письмо не найдено.")

        mail.logout()
        return None

    except Exception as e:
        logger.error(f"{current_email} | Ошибка подключения: {e}")

