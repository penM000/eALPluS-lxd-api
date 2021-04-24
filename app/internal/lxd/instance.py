#!/usr/bin/python3
import pylxd
from typing import Union

from .client import client
from .network import create_network
from .port import get_port
from .image import check_existence_of_image
from .launch import launch_container_instance


from ..general.get_html import check_http_response
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
    starttimeout=20,
    startportassign=49152,
    role_id="",
    class_id=""

):

    # ローカルイメージ検索
    temp = await check_existence_of_image(alias=imagealias, finger=imagefinger)
    if not temp[0]:
        return make_response_dict(False, temp[1])

    instance = await get_instance(hostname)
    # print(instance.name)
    # マシンが無ければ新規作成
    if None is instance:
        # ネットワーク作成
        await create_network(network)
        if instancetype == "container":
            print(f"create new container:{hostname}")
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

        # それ以外は仮想マシン
        else:
            pass

    assign_port = await get_port(instance, port_name, src_port)
    if instance.status == "Running":
        pass
    else:
        # portの動的割当
        assign_port = await get_port(instance, port_name, src_port)
        await async_wrap(instance.start)(wait=True)
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


def get_all_instance_name():
    A = []
    B = [container.name for container in client.containers.all()]
    C = [virtual_instance.name for virtual_instance
         in client.virtual_instances.all()]
    A.extend(B)
    A.extend(C)
    return A


async def get_instance(name) -> Union[pylxd.models.Container,
                                      pylxd.models.VirtualMachine]:
    instance = None

    try:
        async_execute = async_wrap(client.containers.get)
        instance = await async_execute(name)
    except pylxd.exceptions.NotFound:
        pass
    try:
        async_execute = async_wrap(client.virtual_machines.get)
        instance = await async_execute(name)
    except pylxd.exceptions.NotFound:
        pass
    return instance