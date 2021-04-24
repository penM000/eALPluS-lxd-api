#!/usr/bin/python3
import shlex
import pylxd

from .client import client
from .network import create_network
from .port import get_port
from .image import check_existence_of_image
from .launch import launch_container_machine

from ..general.async_wrap import async_wrap
from ..general.get_html import check_http_response
from ..general.response import make_response_dict


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
    port_name: str,
    imagealias="",
    imagefinger="",
    machinetype="container",
    cpu=2,
    memory="2GB",
    storage="32GB",
    network="lxdbr0",
    src_port=8080,
    startcheck=1,
    https=0,
    httpstatus=200,
    starttimeout=20,
    startportassign=49152,
    role_id="",
    class_id=""

):

    # ローカルイメージ検索
    temp = check_existence_of_image(alias=imagealias, finger=imagefinger)
    if not temp[0]:
        return make_response_dict(False, temp[1])

    # ネットワーク作成
    await create_network(network)

    machine = get_machine(hostname)
    # マシンが無ければ新規作成
    if None is machine:
        if machinetype == "container":
            print(f"create new container:{hostname}")
            await launch_container_machine(
                hostname=hostname,
                cpu=cpu,
                memory=memory,
                fingerprint=imagefinger,
                aliases=imagealias,
                network=network,
                role_id=role_id,
                class_id=class_id
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


def get_all_machine_name():
    A = []
    B = [container.name for container in client.containers.all()]
    C = [virtual_machine.name for virtual_machine
         in client.virtual_machines.all()]
    A.extend(B)
    A.extend(C)
    return A


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


def get_machine_file(machine_name, file_path, local_path):
    machine = get_machine(machine_name)
    file_meta = machine.files.recursive_get(file_path, local_path)

    return file_meta
