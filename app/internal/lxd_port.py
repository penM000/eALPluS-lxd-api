import pylxd
from typing import Dict
from .lxd_client import client
from .lxd_network import scan_available_port
from .general.async_wrap import async_wrap


def get_machine_used_port(
        machine: pylxd.models.Container) -> Dict[str, Dict[str, int]]:
    """
    返り値:
        {device_name:{src_port:int,dst_port:int}}
    """
    used_ports = {}
    for key in machine.devices:
        if "type" in machine.devices[key]:
            if machine.devices[key]["type"] == "proxy":
                dst_port = int(machine.devices[key]["listen"].split(":")[-1])
                src_port = int(machine.devices[key]["connect"].split(":")[-1])
                used_ports[key] = {"src_port": src_port, "dst_port": dst_port}
    return used_ports


async def get_port(hostname: str,
                   device_name: str,
                   srcport: int,
                   startportassign: int = 49152) -> int:

    machine = get_machine(hostname)
    used_ports = get_machine_used_port(machine)

    if device_name in used_ports:
        used_port = used_ports[device_name]["src_port"]
    else:
        used_port = None

    if used_port == srcport:
        assign_port = used_ports[device_name]["dst_port"]
    else:
        # srcポートが異なる・srcポートが割当られていない場合ポートを追加
        assign_port = scan_available_port(int(startportassign))
        machine.devices[device_name] = {
            'bind': 'host',
            'connect': f'tcp:127.0.0.1:{srcport}',
            'listen': f'tcp:0.0.0.0:{assign_port}',
            'type': 'proxy'}
        async_execute = async_wrap(machine.save)
        try:
            await async_execute(wait=True)
        except BaseException:
            print("INFO:conflict port!! retry")
            return await get_port(hostname, device_name, srcport)

    return assign_port


def get_machine(name):
    machine = None
    try:
        machine = client.containers.get(name)
    except pylxd.exceptions.NotFound:
        pass
    try:
        machine = client.virtual_machines.get(name)
    except pylxd.exceptions.NotFound:
        pass
    return machine
