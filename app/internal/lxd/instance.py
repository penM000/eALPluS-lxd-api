#!/usr/bin/python3
import asyncio
import pylxd
from typing import Union, List

from .client import client
from .network import create_network
from .port import get_port
from .image import check_existence_of_image
from .launch import launch_container_instance
from .tag import instance_tag
from .cluster import check_cluster, get_container_hostnode_ip

from ..general.get_html import oneshot_check_http_response
from ..general.response import make_response_dict
from ..general.async_wrap import async_wrap


async def launch_instance(
    hostname: str,
    port_name: str,
    imagealias="",
    imagefinger="",
    instancetype="container",
    cpu=2,
    memory="2GB",
    storage="32GB",
    network="lxdbr0",
    src_port=8080,
    startcheck=1,
    https=0,
    httpstatus=200,
    starttimeout=10,
    startportassign=49152,
    role_id="student",
    class_id=""

):

    # ローカルイメージ検索
    temp = await check_existence_of_image(alias=imagealias, finger=imagefinger)
    if not temp[0]:
        return make_response_dict(False, temp[1])

    instance = await get_instance(hostname)
    # マシンが無ければ新規作成
    if None is instance:
        # ネットワーク作成
        await create_network(network)
        if instancetype == "container":

            instance = await launch_container_instance(
                hostname=hostname,
                cpu=cpu,
                memory=memory,
                fingerprint=imagefinger,
                aliases=imagealias,
                network=network,
                role_id=role_id,
                class_id=class_id
            )
            if instance is None:
                return make_response_dict(
                    False, "インスタンス作成に失敗しました")

        # それ以外は仮想マシン
        else:
            pass
    # この行以降、instanceが存在しないことは想定しない
    # instanceが存在しない場合は削除が上記タイミングで行われた場合である
    # インスタンスの作成が殆ど同時の対処
    if instance is None:
        max_try = 200
        while True:
            try:
                instance = await get_instance(hostname)
            except Exception:
                instance = None
                max_try -= 1
                await asyncio.sleep(0.1)
            if instance is not None:
                break
            if max_try < 0:
                return make_response_dict(
                    False, "インスタンス起動中にインスタンスの削除処理が行われました")

    # インスタンスの作成前に起動することを防止
    if instance.status != "Running":
        max_try = 200
        while True:
            instance = await get_instance(hostname)
            if instance is None:
                return make_response_dict(
                    False, "インスタンス起動中にインスタンスの削除処理が行われました")
            tag = instance_tag(instance)
            if instance.status == "Running":
                break
            if "creating" in tag.usertag and tag.usertag["creating"] == "0":
                if await start_instance(instance):
                    break
                else:
                    return make_response_dict(
                        False, "インスタンス起動中にインスタンスの削除処理が行われました")
            elif max_try < 0:
                # 手動で作成されたインスタンスの場合
                tag.usertag["creating"] = "0"
                tag.usertag["role_id"] = role_id
                tag.usertag["class_id"] = class_id
                await async_wrap(tag.save)()
                if await start_instance(instance):
                    break
                else:
                    return make_response_dict(
                        False, "インスタンス起動中にインスタンスの削除処理が行われました")
            else:
                max_try -= 1
                await asyncio.sleep(0.1)
    #
    # port割当
    assign_port = await get_port(instance, port_name, src_port)
    if await check_cluster():
        assign_ip = await get_container_hostnode_ip(instance)
    else:
        assign_ip = "127.0.0.1"
    # 起動確認
    if 1 == startcheck:
        for loop in range(starttimeout):
            result = await oneshot_check_http_response(https,
                                                       assign_ip,
                                                       assign_port,
                                                       httpstatus)
            if result:
                return make_response_dict(
                    assign_ip=assign_ip, assign_port=assign_port)
            else:
                await asyncio.sleep(2)
                instance = await get_instance(hostname)
                if instance is None:
                    return make_response_dict(
                        False, "インスタンス起動中にインスタンスの削除処理が行われました")
                elif instance.status != "Running":
                    return make_response_dict(
                        False, "インスタンス起動中にインスタンスの停止処理が行われました")
                assign_port = await get_port(instance, port_name, src_port)

        return make_response_dict(
            False,
            "timeout_error",
            assign_ip=assign_ip,
            assign_port=assign_port)
    else:
        return make_response_dict(assign_ip=assign_ip, assign_port=assign_port)


async def operation_of_class_instances(class_id, mode: str = "start"):
    instances = await get_all_instance()
    task = []
    for instance in instances:
        if instance.name.startswith(class_id):
            if mode == "start" and instance.status == "Stopped":
                task.append(async_wrap(instance.start)(wait=True))
            elif mode == "stop" and instance.status == "Running":
                task.append(async_wrap(instance.stop)(wait=True))
            elif mode == "delete" and instance.status == "Stopped":
                task.append(async_wrap(instance.delete)(wait=True))
    return await asyncio.gather(*task)


async def get_all_instance_name():
    all_instances = await async_wrap(client.instances.all)()
    all_instances_name = [instance.name for instance in all_instances]
    return all_instances_name


async def get_all_instance() -> List[pylxd.models.instance.Instance]:
    all_instances = await async_wrap(client.instances.all)()
    return all_instances


async def get_instance(name: str) -> Union[
        pylxd.models.instance.Instance,
        None]:

    instance = None
    try:
        instance = await async_wrap(client.instances.get)(name)
    except pylxd.exceptions.NotFound:
        return instance
    return instance


async def stop_instance(instance: pylxd.models.instance.Instance) -> bool:
    try:
        await async_wrap(instance.stop)(wait=True)
        return True
    except Exception:
        return False


async def start_instance(instance: pylxd.models.instance.Instance) -> bool:
    try:
        await async_wrap(instance.start)(wait=True)
        return True
    except Exception:
        return False
