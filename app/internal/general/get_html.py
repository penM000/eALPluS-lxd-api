import asyncio
import aiohttp
import time


async def check_http_response(https, assign_port, status, time_out):
    return await wait_get_html(
        make_url(https, assign_port),
        status,
        time_out
    )


def make_url(https, assign_port):
    # URL生成
    try_url = ""
    if https == 0:
        try_url += "http://"
    else:
        try_url += "https://"
    try_url += "127.0.0.1"
    try_url += ":" + str(assign_port)
    return try_url


async def wait_get_html(url, status, time_out) -> bool:
    start_time = time.time()
    while time.time() - start_time < time_out:
        result = await get_html(url)
        if str(result) == str(status):
            return True
        await asyncio.sleep(1)
    return False


async def get_html(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, verify_ssl=False) as resp:
                return int(resp.status)
        except aiohttp.client_exceptions.ClientConnectorError:
            return 0
        except aiohttp.client_exceptions.ServerDisconnectedError:
            return 0
        except BaseException:
            return 0
