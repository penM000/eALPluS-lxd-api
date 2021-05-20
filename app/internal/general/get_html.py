import asyncio
import aiohttp
import time
import json


async def check_http_response(
        https, assign_ip, assign_port, status, time_out) -> bool:
    return await wait_get_html(
        make_url(https, assign_ip, assign_port),
        status,
        time_out
    )


async def oneshot_check_http_response(
        https, assign_ip, assign_port, status) -> bool:
    return await oneshot_get_html(
        make_url(https, assign_ip, assign_port),
        status,
    )


def make_url(https, assign_ip, assign_port) -> str:
    # URL生成
    try_url = ""
    if https == 0:
        try_url += "http://"
    else:
        try_url += "https://"
    try_url += str(assign_ip)
    try_url += ":" + str(assign_port)
    return try_url


async def oneshot_get_html(url, status) -> bool:
    result = await get_html_status_code(url)
    if str(result) == str(status):
        return True
    return False


async def wait_get_html(url, status, time_out) -> bool:
    start_time = time.time()
    while time.time() - start_time < time_out:
        result = await get_html_status_code(url)
        if str(result) == str(status):
            return True
        await asyncio.sleep(1)
    return False


async def get_html_status_code(url) -> int:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, verify_ssl=False) as resp:
                return int(resp.status)
        except aiohttp.client_exceptions.ClientConnectorError:
            return 0
        except aiohttp.client_exceptions.ServerDisconnectedError:
            return 0
        except Exception:
            return 0


async def get_html(url) -> str:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, verify_ssl=False) as resp:
                assert resp.status == 200
                return await resp.text()
        except aiohttp.client_exceptions.ClientConnectorError:
            return None
        except aiohttp.client_exceptions.ServerDisconnectedError:
            return None
        except Exception:
            return None

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    hoge = loop.run_until_complete(
        get_html("http://192.168.1.21:8000/node/used_port"))
    print(type(json.loads(hoge)[0]))
