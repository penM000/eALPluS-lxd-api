import json
import asyncio
from urllib.parse import urlparse
from typing import List
from ..general.async_wrap import async_wrap
from .client import client
from ..general.get_html import get_html


async def check_cluster():
    cluster = await async_wrap(client.cluster.get)()
    return cluster.enabled


async def get_cluster_status():
    """
    {'rpi1': ['192.168.1.21', 'Online'],
    'rpi2': ['192.168.1.22', 'Online'],
    'rpi3': ['192.168.1.23', 'Online']}
    """
    cluster = await async_wrap(client.cluster.get)()
    members = await async_wrap(cluster.members.all)()
    result = dict()
    for node in members:
        result[node.server_name] = [urlparse(node.url).hostname, node.status]
    return result


async def get_all_node_used_port() -> List[int]:
    used_ports = []
    if await check_cluster():
        cluster = await get_cluster_status()
        tasks = []
        for node_name in cluster.keys():
            if cluster[node_name][1] == "Online":
                ip = cluster[node_name][0]
                port = 8000
                path = "/node/used_port"
                url = f"http://{ip}:{port}{path}"
                tasks.append(get_html(url))
        import time
        now = time.time()
        task_result = await asyncio.gather(*tasks)
        print(time.time() - now)
        for result in task_result:
            if result is None:
                continue
            else:
                used_ports = used_ports + json.loads(result)
    used_ports = sorted(set(used_ports))
    return used_ports
