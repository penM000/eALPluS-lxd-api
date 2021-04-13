import asyncio
import psutil
import os
import socket
import netifaces as ni
import random
from functools import wraps, partial

from .lxd_client import client


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run


async def create_network(name):
    if not client.networks.exists(name):
        async_execute = async_wrap(client.networks.create)
        await async_execute(
            name,
            description='ealplus network',
            type='bridge',
            config={
                "ipv4.address": "auto",
                "ipv4.nat": "true",
                "ipv6.address": "auto",
                "ipv6.nat": "true"
            }
        )


def get_used_port():
    """
    現在利用中のportと割り当て済みのport一覧作成
    """
    used_ports = [int(conn.laddr.port) for conn in psutil.net_connections()
                  if conn.status == 'LISTEN']
    for machine in client.containers.all():
        for key in machine.devices:
            if "type" in machine.devices[key]:
                if machine.devices[key]["type"] == "proxy":
                    used_ports.append(
                        int(machine.devices[key]["listen"].split(":")[-1]))

    for machine in client.virtual_machines.all():
        for key in machine.devices:
            if "type" in machine.devices[key]:
                if machine.devices[key]["type"] == "proxy":
                    used_ports.append(
                        int(machine.devices[key]["listen"].split(":")[-1]))
    used_ports = sorted(set(used_ports))
    return used_ports


def check_port_available(port):
    used_ports = get_used_port()
    if (port in used_ports):
        return False
    else:
        return True


def scan_available_port(start_port):
    used_ports = get_used_port()
    available_port_count = (65535 - start_port) - len(
        [1 for x in used_ports if x >= start_port])
    if available_port_count < 10:
        raise Exception("利用可能なport上限を超えました")
    while True:
        port_candidate = random.randint(start_port, 65535)
        if port_candidate in used_ports:
            continue
        else:
            return port_candidate


def get_ip() -> list:
    if os.name == "nt":
        # Windows
        return socket.gethostbyname_ex(socket.gethostname())[2]
        pass
    else:
        # それ以外
        result = []
        address_list = psutil.net_if_addrs()
        for nic in address_list.keys():
            ni.ifaddresses(nic)
            try:
                ip = ni.ifaddresses(nic)[ni.AF_INET][0]['addr']
                if ip not in ["127.0.0.1"]:
                    result.append(ip)
            except KeyError as err:
                print(err)
                pass
        return result
