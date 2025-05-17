import asyncio
from random import randint

from core.reqs import join_waitlist
from utils.file_utils import read_proxies, read_emails, read_x_tokens
from utils.log_utils import logger
from configs import config

async def start():
    tasks = []
    for email, proxy, x_auth_token in zip(EMAILS, PROXIES, X_AUTH_TOKENS):
        task = asyncio.create_task(join_waitlist(email, proxy, x_auth_token))
        tasks.append(task)
        await asyncio.sleep(randint(config.DELAY_BETWEEN_ACCOUNTS[0], config.DELAY_BETWEEN_ACCOUNTS[1]))

    while tasks:
        tasks = [task for task in tasks if not task.done()]
        await asyncio.sleep(10)

    logger.success(f"Все аккаунты обработаны!")

if __name__ == '__main__':
    EMAILS = read_emails()
    PROXIES = read_proxies()
    X_AUTH_TOKENS = read_x_tokens()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(start())