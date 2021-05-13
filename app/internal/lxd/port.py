import psutil
import random
import asyncio
from typing import List, Dict

import pylxd

from .client import client
from .cluster import check_cluster, get_cluster_status, get_all_node_used_port
from ..general.async_wrap import async_wrap


async def get_listen_status() -> List[int]:
    net_status = await async_wrap(psutil.net_connections)()
    listen_ports = [int(conn.laddr.port) for conn in net_status
                    if conn.status == 'LISTEN']

    listen_ports = sorted(set(listen_ports))
    return listen_ports


async def get_used_port() -> List[int]:
    """
    現在利用中のportと割り当て済みのport一覧作成
    """
    if await check_cluster():
        used_ports = await get_all_node_used_port()
    else:
        used_ports = await get_listen_status()
    all_instances = await async_wrap(client.instances.all)()
    for instance in all_instances:
        for key in instance.devices:
            if "type" in instance.devices[key]:
                if instance.devices[key]["type"] == "proxy":
                    used_ports.append(
                        int(instance.devices[key]["listen"].split(":")[-1]))

    used_ports = sorted(set(used_ports))
    return used_ports


async def check_port_available(port: int) -> bool:
    used_ports = await get_used_port()
    if (port in used_ports):
        return False
    else:
        return True


async def scan_available_port(start_port: int, mode: str = "random") -> int:
    """
    概要:
        このAPIが動作しているコンピューターの空きポートを検索する関数
    動作モード:
        random: ポート割当はランダム
        countup: 最初からきれいにポートを割り当てる
    返り値:
        割当可能なポート番号(int)
    """
    port_offset = 0
    used_ports = await get_used_port()
    available_port_count = (65535 - start_port) - len(
        [1 for x in used_ports if x >= start_port])
    if available_port_count < 10:
        raise Exception("利用可能なport上限を超えました")
    while True:
        if mode == "random":
            port_candidate = random.randint(start_port, 65535)
        elif mode == "countup":
            port_candidate = start_port + port_offset
        if port_candidate in used_ports:
            port_offset += 1
            continue
        else:
            return port_candidate


def get_instance_used_port(
        instance: pylxd.models.Container) -> Dict[str, Dict[str, int]]:
    """
    返り値:
        {device_name:{src_port:int,dst_port:int}}
    """
    used_ports = {}
    for key in instance.devices:
        if "type" in instance.devices[key]:
            if instance.devices[key]["type"] == "proxy":
                dst_port = int(instance.devices[key]["listen"].split(":")[-1])
                src_port = int(instance.devices[key]["connect"].split(":")[-1])
                used_ports[key] = {"src_port": src_port, "dst_port": dst_port}
    return used_ports


async def get_port(instance: pylxd.models.Container,
                   device_name: str,
                   srcport: int,
                   startportassign: int = 49152,
                   retry: bool = False) -> int:

    used_ports = get_instance_used_port(instance)

    if device_name in used_ports:
        used_port = used_ports[device_name]["src_port"]
    else:
        used_port = None

    if used_port == srcport and not retry:
        assign_port = used_ports[device_name]["dst_port"]
    else:
        # srcポートが異なる・srcポートが割当られていない・前回失敗している場合ポートを割当
        assign_port = await scan_available_port(int(startportassign))
        instance.devices[device_name] = {
            'bind': 'host',
            'connect': f'tcp:127.0.0.1:{srcport}',
            'listen': f'tcp:0.0.0.0:{assign_port}',
            'type': 'proxy'}
        try:
            await async_wrap(instance.save)(wait=True)
        except BaseException:
            print("INFO:conflict port!! retry")
            return await get_port(instance, device_name, srcport, retry=True)
        # 同時割当時の対策
        instance = await async_wrap(client.instances.get)(instance.name)
        if assign_port == get_instance_used_port(
                instance)[device_name]["dst_port"]:
            return assign_port
        else:
            print("INFO:conflict setting!! retry")
            return await get_port(instance, device_name, srcport, retry=True)
    return assign_port
