#!/usr/bin/python3
import shlex
import pylxd


from .lxd_client import client
from .lxd_network import (scan_available_port,
                          create_network,)
from .general.async_wrap import async_wrap
from .general.get_html import check_http_response


def make_response_dict(
    status=True,
    details="success",
    assign_port="",
    option=""
):
    return {
        "status": status,
        "details": details,
        "assign_port": assign_port,
        "option": option
    }


# マシンコマンド実行
async def exec_command_to_machine(hostname, cmd):
    machine = get_machine(hostname)
    if machine is None:
        raise Exception("マシンが見つかりません")
    async_machine_execute = async_wrap(machine.execute)
    result = await async_machine_execute(shlex.split(cmd))
    return make_response_dict(status=result[0], details=result[1])


# ファイル送信
async def send_file_to_machine(hostname, filename, filedata):
    machine = get_machine(hostname)
    if machine is None:
        return make_response_dict(False, "machine not found")
    if filename[0] != "/":
        filename = "/" + filename
    async_machine_file_put = async_wrap(machine.files.put)
    try:
        await async_machine_file_put(filename, filedata)
        return make_response_dict()
    except BaseException:
        return make_response_dict(False, "file put error")


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
        machine = get_machine(hostname)

    return assign_port


async def launch_machine(
    hostname: str,
    port_name: str,
    imagealias="",
    imagefinger="",
    machinetype="container",
    cpu=2,
    memory="3GB",
    storage="32GB",
    network="lxdbr0",
    src_port=8080,
    startcheck=1,
    https=0,
    httpstatus=200,
    starttimeout=20,
    startportassign=49152,

):

    # ローカルイメージ検索
    aliases, fingerprint = get_all_image()
    if (imagealias == "") and (imagefinger == ""):
        # raise Exception("イメージが指定されていません")
        return make_response_dict(False, "image_error", "イメージが指定されていません")

    elif imagealias != "" and \
            len([s for s in aliases if imagealias == s]) == 0:
        # raise Exception("イメージ名が異なっています")
        return make_response_dict(False, "image_error", "イメージエイリアスが異なっています")

    elif imagefinger != "" and \
            len([s for s in fingerprint if s.startswith(imagefinger)]) == 0:
        # raise Exception("イメージ名が異なっています")
        return make_response_dict(
            False, "image_error", "イメージフィンガープリントが異なっています")

    # ネットワーク作成
    await create_network(network)

    machine = get_machine(hostname)
    assign_port = None
    # マシンが無ければ新規作成
    if None is machine:
        if machinetype == "container":
            print(f"create new container:{hostname}")
            assign_port = scan_available_port(int(startportassign))
            await launch_container_machine(
                hostname=hostname,
                cpu=cpu,
                memory=memory,
                fingerprint=imagefinger,
                aliases=imagealias,
                network=network
            )
            pass
        # それ以外は仮想マシン
        else:
            pass
    # 停止スケジュールを中止
    from .lxd_schedule import remove_stop_machine_schedule
    remove_stop_machine_schedule(hostname)

    assign_port = await get_port(hostname, port_name, src_port)
    # マシン状態確認
    machine = get_machine(hostname)
    if machine.status == "Running":
        pass
    else:
        # portの動的割当
        assign_port = await get_port(hostname, port_name, src_port)
        machine.start()

    # 起動確認
    if 1 == startcheck:
        result = await check_http_response(
            https,
            assign_port,
            httpstatus,
            starttimeout
        )
        if result:
            return make_response_dict(assign_port=assign_port)
        else:
            return make_response_dict(False, "timeout_error")
    else:
        return make_response_dict(assign_port=assign_port)


def get_all_image():
    aliases = []
    fingerprint = []
    for image in client.images.all():
        if len(image.aliases) != 0:
            for i in image.aliases:
                if "name" in i:
                    aliases.append(i["name"])
        fingerprint.append(image.fingerprint)
    return aliases, fingerprint


def get_all_machine_name():
    A = []
    B = [container.name for container in client.containers.all()]
    C = [virtual_machine.name for virtual_machine
         in client.virtual_machines.all()]
    A.extend(B)
    A.extend(C)
    return A


async def launch_container_machine(
        hostname="",
        cpu="2",
        memory="4GB",
        fingerprint="",
        aliases="",
        network="lxdbr0"):
    image = {}
    if fingerprint != "":
        image = {"type": "image", "fingerprint": str(fingerprint)}
    elif aliases != "":
        image = {"type": "image", "alias": str(aliases)}
    config = {
        "name": str(hostname),
        "source": image,
        "config": {
            "limits.cpu": str(cpu),
            "limits.memory": str(memory),
            "security.nesting": "1"
        },
        "devices": {
            'eth0': {
                'name': 'eth0',
                'network': str(network),
                'type': 'nic'
            }
        }
    }
    async_execute = async_wrap(client.containers.create)
    container = await async_execute(config, wait=True)
    async_execute = async_wrap(container.start)
    await async_execute(wait=True)


def launch_virtual_machine():
    config = {
        "name": "my-vmapitest",
        "source": {
            "type": "image",
            "fingerprint": "fbca989572df"},
        "config": {
            "limits.cpu": "2",
            "limits.memory": "3GB"},
        "devices": {
            "root": {
                "path": "/",
                "pool": "default",
                "type": "disk",
                "size": "20GB"}}}
    virtual_machines = client.virtual_machines.create(config, wait=True)
    virtual_machines.start(wait=True)


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


def stop_machine(machine_name, call_from_scheduler=False):
    from .lxd_schedule import remove_stop_machine_schedule
    if call_from_scheduler:
        remove_stop_machine_schedule(machine_name)
    machine = get_machine(machine_name)
    if machine is None:
        return False
    try:
        machine.stop()
    except BaseException:
        return False
    return True


def start_machine(name):
    machine = get_machine(name)
    if machine is None:
        return False
    machine.start()


def delete_machine(name):
    print(get_machine(name))


def get_machine_used_port(machine: pylxd.models.Container) -> dict:
    used_ports = {}
    for key in machine.devices:
        if "type" in machine.devices[key]:
            if machine.devices[key]["type"] == "proxy":
                dst_port = int(machine.devices[key]["listen"].split(":")[-1])
                src_port = int(machine.devices[key]["connect"].split(":")[-1])
                used_ports[key] = {"src_port": src_port, "dst_port": dst_port}
    return used_ports


def get_machine_file(machine_name, file_path, local_path):
    machine = get_machine(machine_name)
    file_meta = machine.files.recursive_get(file_path, local_path)

    return file_meta
