import asyncio

import aiohttp
from aiohttp import ClientHttpProxyError, ClientResponseError
from fake_useragent import UserAgent
from socket import AF_INET

from utils.log_utils import logger
from utils.file_utils import write_failed_x_tokens, write_success_x_tokens
from utils.file_utils import write_failed_emails, write_success_emails

from core.email_reader import get_verification_code
from configs import config

ua = UserAgent(os=["Windows", "Linux", "Ubuntu", "Mac OS X"])

async def fetch_with_retries(method, url, session, email, proxy, retries=10, **kwargs) -> aiohttp.ClientResponse | None:
    for attempt in range(retries):
        try:
            response = await session.request(method, url, proxy=proxy, **kwargs)
            return response
        except ClientHttpProxyError:
            logger.error(f"{email} | Bad proxy: {proxy}")
        except ClientResponseError:
            logger.error(f"{email} | Request failed, attempt {attempt + 1}/{retries}")
        except TimeoutError:
            logger.error(f"{email} | TimeoutError, attempt {attempt + 1}/{retries}")
        except Exception as e:
            logger.error(f"{email} | Unexpected error: {e}, attempt {attempt + 1}/{retries}")
        await asyncio.sleep(3, 10)

    return None

async def join_waitlist(email, proxy, auth_token):
    email_password = None
    if not config.SINGLE_IMAP_ACCOUNT:
        parts = email.split(':')
        email, email_password = parts[0], parts[1]

    logger.success(f"{email} | Начинаю присоединяться к вайт листу..")
    current_ua = ua.random
    headers = {
        "User-Agent": current_ua
    }
    connector = aiohttp.TCPConnector(family=AF_INET, limit_per_host=10)
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector, max_line_size=8190 * 2, max_field_size=8190 * 2) as session:
        try:
            logger.info(f"{email} | Подключаю твиттер..")

            auth_url = await get_x_auth_link(email, proxy, session, headers)
            x_cookies, twitter_id, url_to_get_auth_code = await get_twitter_data(email, proxy, session, headers, auth_url, auth_token)
            await asyncio.sleep(5)
            if twitter_id:
                logger.info(f"{email} | Успешно авторизовался в твиттер аккаунте")
            else:
                logger.error(f"{email} | Не удалось авторизоватсья в твиттер аккаунте")
                write_failed_x_tokens(auth_token)
                return
            auth_token_to_redirect, x_headers = await get_x_auth_code(
                email, proxy, session, current_ua, x_cookies, auth_url, url_to_get_auth_code
            )
            await asyncio.sleep(4)
            if auth_token_to_redirect:
                logger.info(f"{email} | Успешно авторизовался в твиттер-приложении Amigo")
            else:
                logger.error(f"{email} | Не удалось авторизоваться через твиттер в Amigo")
                write_failed_x_tokens(auth_token)
                return

            redirect_uri = await x_auth_and_get_redirect_url(email, proxy, session, x_headers, x_cookies, auth_token_to_redirect)
            await asyncio.sleep(1)
            status, user_id = await request_to_redirect_url(email, proxy, session, current_ua, redirect_uri)
            await asyncio.sleep(5)
            if status == -1:
                logger.info(f"{email} | Аккаунт уже верифицировано и допущен к вайт листу")
                return
            if not user_id:
                logger.error(f"{email} | Не удалось авторизоваться на сайте Amigo через твиттер")
                return

            logger.info(f"{email} | Успешно авторизовался на сайте Amigo через твиттер")
            await asyncio.sleep(10)
            for attempt_to_get_verification_code in range(5):

                for attempt_to_send_email in range(5):
                    send_email_status = await send_email(email, proxy, session, user_id)

                    if not send_email_status:
                        logger.info(f"{email} | Не удалось отправить письмо, попытка {attempt_to_send_email+1}/5")
                    else:
                        logger.info(f"{email} | Успешно отправленно письмо")
                        break

                verify_code = await get_verification_code(email, email_password)
                if verify_code:
                    break

                logger.info(f"{email} | Не удалось найти письмо, попытка {attempt_to_get_verification_code+1}/5")

            status = await verify_email_code(email, proxy, session, verify_code)
            if status:
                logger.success(f"{email} | Аккаунт присоединился к вейт листу!")
                write_success_emails(email)
                write_success_x_tokens(auth_token)
            else:
                logger.error(f"{email} | Ошибка во время подтверждения почты")
                write_failed_x_tokens(auth_token)
                write_failed_emails(email)


        except Exception as e:
            logger.error(f"{email} | Ошибка: {e}")
            write_failed_x_tokens(auth_token)
            write_failed_emails(email)
    return


async def get_x_auth_link(email, proxy, session: aiohttp.ClientSession, headers: dict):
    url_to_get_x_auth_link = "https://www.amigo.cool/api/link/twitter"

    response = await fetch_with_retries(
        method="POST", url=url_to_get_x_auth_link, session=session, email=email, proxy=proxy, headers=headers
    )

    try:
        response_json = await response.json()

        if "url" in response_json:
            return response_json["url"]
    except:
        return

async def get_twitter_data(email, proxy, session: aiohttp.ClientSession, headers: dict, auth_url, auth_token: str):
    x_cookies = {
        "auth_token": auth_token
    }

    response = await fetch_with_retries(
        method="GET", url="https://x.com", session=session, email=email, proxy=proxy,
        headers=headers, cookies=x_cookies
    )

    try:
        response_text = await response.text()
        a = response_text.find('"id_str":"')
        if a == -1:
            return None, None, None
        b = response_text[a + len('"id_str":"'):].find('"')
        twitter_id = response_text[a + len('"id_str":"'):a + len('"id_str":"') + b]
        ct0 = str(response.cookies.get("ct0"))

        a = ct0.find("ct0=")
        b = ct0.find(";")
        x_cookies["ct0"] = ct0[a + len("ct0="):b]

        # get token to x auth
        # create link to get x code
        a = auth_url.find("client_id")
        b = a + 44
        client_id = auth_url[a + len("client_id") + 1:b]

        a = auth_url.find("code_challenge")
        b = a + 58
        code_challenge = auth_url[a + len("code_challenge") + 1:b]

        a = auth_url.find("&state=")
        b = a + 50
        state = auth_url[a + len("&state") + 1:b]

        # link to get x code
        url_to_get_auth_code = f"https://x.com/i/api/2/oauth2/authorize?client_id={client_id}&code_challenge={code_challenge}&code_challenge_method=s256&redirect_uri=https%3A%2F%2Fwww.amigo.cool%2Fapi%2Flink%2Ftwitter%2Fcallback&response_type=code&scope=users.read%20tweet.read&state={state}"

        return x_cookies, twitter_id, url_to_get_auth_code
    except:
        return None, None, None

async def get_x_auth_code(email, proxy, session: aiohttp.ClientSession, current_ua: str, x_cookies: dict, auth_url, url_to_get_auth_code: str):
    headers = {
        "User-Agent": current_ua,
        "Referer": auth_url,
        "X-Csrf-Token": x_cookies["ct0"],
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
    }

    response = await fetch_with_retries(
        method="GET", url=url_to_get_auth_code, session=session, email=email, proxy=proxy,
        headers=headers, cookies=x_cookies
    )
    try:
        return (await response.json())["auth_code"], headers
    except:
        return None, None

async def x_auth_and_get_redirect_url(email, proxy, session: aiohttp.ClientSession, x_headers, x_cookies, auth_token_to_layer_redirect):
    url_auth = "https://twitter.com/i/api/2/oauth2/authorize"

    payload_x_auth = {
        "approval": True,
        "code": auth_token_to_layer_redirect
    }

    response = await fetch_with_retries(
        method="POST", url=url_auth, session=session, email=email, proxy=proxy,
        data=payload_x_auth, headers=x_headers, cookies=x_cookies
    )

    try:
        return (await response.json())["redirect_uri"]
    except:
        return None

async def request_to_redirect_url(email, proxy, session: aiohttp.ClientSession, current_ua, redirect_uri):
    headers = {
        "User-Agent": current_ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9"
    }

    await session.get(redirect_uri, headers=headers, proxy=proxy)

    response = await fetch_with_retries(
        method="GET", url=redirect_uri, session=session, email=email, proxy=proxy, headers=headers
    )


    user_id = None
    if "Cookie" in response.request_info.headers:
        is_verified = response.request_info.headers['Cookie'].split('; ')[2].split('=')[1]
        if is_verified == 'true':
            return -1, 0

        user_id = response.request_info.headers['Cookie'].split('; ')[1].split('=')[1]

    response_ok = response.ok

    amigo_main_url = "https://www.amigo.cool/"
    await fetch_with_retries(
        method="GET", url=amigo_main_url, session=session, email=email, proxy=proxy, headers=headers
    )
    return response_ok, user_id

async def send_email(email, proxy, session: aiohttp.ClientSession, user_id):
    logger.info(f"{email} | Начинаю подключать почту")

    url_to_send_email = "https://www.amigo.cool/api/link/email"

    payload = {
        'email': email,
        'id': int(user_id)
    }

    response = await fetch_with_retries(
        method="POST", url=url_to_send_email, session=session, email=email, proxy=proxy, json=payload
    )
    try:
        response_json = await response.json()
        if 'success' in response_json:
            return response_json['success']
    except:
        return None

async def verify_email_code(email, proxy, session: aiohttp.ClientSession, verify_code):
    logger.info(f"{email} | Подтверждаю почту...")

    url_to_confirm_email = "https://www.amigo.cool/api/link/email/verify"

    payload = {
        'code': int(verify_code),
        'email': email
    }

    for attempt in range(5):
        response = await fetch_with_retries(
            method="POST", url=url_to_confirm_email, session=session, email=email, proxy=proxy, json=payload
        )

        if response.status == 200:
            break

        await asyncio.sleep(5)
    try:
        response_json = await response.json()
        if 'success' in response_json:
            return response_json['success']
        return None
    except:
        return None
