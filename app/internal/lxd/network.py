
import psutil
import os
import socket
import netifaces as ni

import time
from typing import List
from ipaddress import (
    ip_interface, ip_address)
from functools import lru_cache

from .client import client
from .cluster import check_cluster
from ..general.async_wrap import async_wrap


async def create_network(name: str, network_type: str = "auto") -> None:
    async_execute = async_wrap(client.networks.exists)
    if not await async_execute(name):
        async_execute = async_wrap(client.networks.create)
        if network_type == "auto":
            if await check_cluster():
                network_type = "ovn"
                config = {
                    "network": "lxdbr0",
                    "ipv4.address": "auto",
                    "ipv4.nat": "true",
                    "ipv6.address": "auto",
                    "ipv6.nat": "true"
                }
            else:
                network_type = "bridge"
                config = {
                    "ipv4.address": "auto",
                    "ipv4.nat": "true",
                    "ipv6.address": "auto",
                    "ipv6.nat": "true"
                }
        await async_execute(
            name,
            description=f"Network automatically generated by ealplus for {name}.",
            type=network_type,
            config=config
        )
    return


cache_timer = time.time()


def get_ip_address(client_ip: str = "0.0.0.0") -> List[str]:
    global cache_timer
    if time.time() - cache_timer > 10:
        cache_get_ip_address.cache_clear()
        cache_timer = time.time()
    return cache_get_ip_address(client_ip)


@lru_cache(maxsize=128)
def cache_get_ip_address(client_ip: str = "0.0.0.0") -> List[str]:
    """
    概要:
        このAPIが動作しているIPアドレスから、
        引数で渡されたIPアドレスと同一ネットワーク上のものを検索する。
    返り値:
        ipアドレスのリスト
    """
    if os.name == "nt":
        # Windows
        return socket.gethostbyname_ex(socket.gethostname())[2]
        pass
    else:
        # それ以外
        result = []
        address_list = psutil.net_if_addrs()
        for nic in address_list.keys():
            try:
                temp = ni.ifaddresses(nic)[ni.AF_INET][0]
                ip_adress = temp['addr']
                subnet = temp['netmask']
                ip = ip_interface(f"{ip_adress}/{subnet}")
                if ip_address(client_ip) in ip.network:
                    return [str(ip.ip)]
                if ip_adress not in ["127.0.0.1"]:
                    result.append(str(ip_adress))
            except KeyError as err:
                # print(err)
                err
                pass
        return result
