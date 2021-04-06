#!/usr/bin/python3
import asyncio
import time
import aiohttp
from functools import wraps, partial
import shlex

import pylxd

from .lxd_client import client
from .lxd_network import scan_available_port, check_port_available, create_network


# 同期関数を非同期関数にする


def async_wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run


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


async def launch_machine(
    hostname: str,
    imagealias="",
    imagefinger="",
    machinetype="container",
    cpu=2,
    memory="3GB",
    storage="32GB",
    network="lxdbr0",
    srcport=8080,
    startcheck=1,
    https=0,
    httpstatus=200,
    starttimeout=60,
    startportassign=10000
):

    # ローカルイメージ検索
    aliases, fingerprint = get_all_image()
    if (imagealias == "") and (imagefinger == ""):
        # raise Exception("イメージが指定されていません")
        return make_response_dict(False, "image_error", "イメージが指定されていません")

    elif imagealias != "" and len([s for s in aliases if imagealias == s]) == 0:
        # raise Exception("イメージ名が異なっています")
        return make_response_dict(False, "image_error", "イメージエイリアスが異なっています")
    elif imagefinger != "" and len([s for s in fingerprint if s.startswith(imagefinger)]) == 0:
        # raise Exception("イメージ名が異なっています")
        return make_response_dict(
            False, "image_error", "イメージフィンガープリントが異なっています")

    # ネットワーク作成
    await create_network(network)
    # マシンが無ければ新規作成
    machine = get_machine(hostname)
    assign_port = None
    if None is machine:
        # コンテナであれば
        if machinetype == "container":
            assign_port = scan_available_port(int(startportassign))
            print("なし")
            await launch_container_machine(
                hostname=hostname,
                srcport=srcport,
                dstport=assign_port,
                cpu=cpu,
                memory=memory,
                fingerprint=imagefinger,
                aliases=imagealias,
                network=network
            )

            # print(get_ip())
            pass
        # それ以外は仮想マシン
        else:
            pass
    # マシンが存在場合
    else:
        from .lxd_schedule import remove_stop_machine_schedule
        remove_stop_machine_schedule(hostname)
        if len(get_machine_used_port(hostname)) != 0:
            assign_port = get_machine_used_port(hostname)[0]

        if machine.status == "Running":

            if await wait_get_html(make_url(https, assign_port), httpstatus, 5):
                pass

            else:
                machine.restart()
        else:
            machine.start()

    # 起動確認
    if 1 == startcheck:
        result = await wait_get_html(
            make_url(https, assign_port),
            httpstatus,
            starttimeout
        )
        if result:
            return make_response_dict(assign_port=assign_port)
        else:
            return make_response_dict(False, "timeout_error")
    else:
        return make_response_dict(assign_port=assign_port)


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


async def wait_get_html(url, status, time_out):
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
    C = [virtual_machine.name for virtual_machine in client.virtual_machines.all()]
    A.extend(B)
    A.extend(C)
    return A


async def launch_container_machine(
        hostname="",
        srcport="",
        dstport="",
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
        "config": {"limits.cpu": str(cpu), "limits.memory": str(memory)},
        "devices": {
            "vscode-port": {
                "bind": "host",
                "connect": "tcp:127.0.0.1:" + str(srcport),
                "listen": "tcp:0.0.0.0:" + str(dstport),
                "type": "proxy"
            },
            'eth0': {
                'name': 'eth0',
                'network': str(network),
                'type': 'nic'
            }
        }
    }
    # container = client.containers.create(config, wait=True)
    # container.start()
    # print(config)
    async_execute = async_wrap(client.containers.create)
    container = await async_execute(config, wait=True)
    container.start()


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


def get_machine_used_port(machine_name):
    machine = get_machine(machine_name)
    if machine is None:
        return []
    used_ports = []

    for key in machine.devices:
        if "type" in machine.devices[key]:
            if machine.devices[key]["type"] == "proxy":
                used_ports.append(
                    int(machine.devices[key]["listen"].split(":")[-1]))
    return used_ports


def read_file(file_path):
    with open(file_path) as f:
        l_strip = [s.strip() for s in f.readlines()]
        return l_strip


def make_csv(
        in_file_path,
        out_file_path,
        start_port=0,
        prefix="",
        suffix="",
        image_aliases="",
        image_fingerprint="",
        class_code="",
        ip_address=""):
    members = read_file(in_file_path)
    port_offset = 0
    file_meta = ["class_code,name,ip,port,image_aliases,image_fingerprint"]
    for i in range(len(members)):
        while True:
            port_candidate = start_port + i + port_offset
            if check_port_available(port_candidate):
                file_meta.append(
                    class_code + "," +
                    members[i] + "," +
                    ip_address + "," +
                    str(port_candidate) + "," +
                    image_aliases + "," +
                    image_fingerprint
                )
                break
            else:
                port_offset += 1
    with open(out_file_path, mode='w') as f:
        f.write('\n'.join(file_meta))


def make_csv_from_str(
        in_file_str="",
        start_port=0,
        prefix="",
        suffix="",
        image_aliases="",
        image_fingerprint="",
        class_code="",
        ip_address=""):
    members = in_file_str.splitlines()
    port_offset = 0
    file_meta = ["class_code,name,ip,port,image_aliases,image_fingerprint"]
    for i in range(len(members)):
        while True:
            port_candidate = start_port + i + port_offset
            if check_port_available(port_candidate):
                file_meta.append(
                    class_code + "," +
                    members[i] + "," +
                    ip_address + "," +
                    str(port_candidate) + "," +
                    image_aliases + "," +
                    image_fingerprint
                )
                break
            else:
                port_offset += 1
    return '\n'.join(file_meta)


def get_machine_file(machine_name, file_path, local_path):
    machine = get_machine(machine_name)
    file_meta = machine.files.recursive_get(file_path, local_path)

    return file_meta


async def test():
    hoge = await wait_get_html("https://yukkuriikouze.com", 200, 5)
    print(hoge)


async def test():
    await asyncio.gather(exec_command_to_machine("funo", "sleep 10"), exec_command_to_machine("funo", "sleep 10"), exec_command_to_machine("funo", "sleep 10"))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())


"""
make_csv(
        'member.txt',
        'member.csv',
        start_port=10000,
        ip_address="160.252.131.148",
        class_code="PIT0014",
        image_aliases="PIT0014-v1")
    for line in read_file('member.csv')[1:]:
        class_code, name, ip, port, aliases, fingerprint = line.split(",")
        #print(class_code+"-"+name, port, aliases, fingerprint)
        print("launch"+class_code+"-"+name)
        #launch_container_machine(class_code+"-"+name, port)
    # launch_container_machine("my-test2","5659")
    # delete_machine("my-vmapitest")
"""
