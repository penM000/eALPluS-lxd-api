#!/usr/bin/python3
import asyncio
import pylxd
from typing import Union

from .client import client
from .network import create_network
from .port import get_port
from .image import check_existence_of_image
from .launch import launch_container_instance
from .tag import instance_tag


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

        # それ以外は仮想マシン
        else:
            pass
    # インスタンスの作成が殆ど同時の対処
    if instance is None:
        while True:
            try:
                instance = await get_instance(hostname)
            except BaseException:
                instance = None
                await asyncio.sleep(0.1)
            if instance is not None:
                break

    # インスタンスの作成前に起動することを防止
    if instance.status != "Running":
        while True:
            instance = await get_instance(hostname)
            tag = instance_tag(instance)
            if instance.status == "Running":
                break
            if "creating" in tag.tag and tag.tag["creating"] == "0":
                await async_wrap(instance.start)(wait=True)
                break
            else:
                await asyncio.sleep(0.1)

    assign_port = await get_port(instance, port_name, src_port)
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


async def get_all_instance_name():
    all_instances = await async_wrap(client.instances.all)()
    all_instances_name = [instance.name for instance in all_instances]
    return all_instances_name


async def get_instance(name: str) -> Union[
        pylxd.models.instance.Instance,
        None]:

    instance = None
    try:
        instance = await async_wrap(client.instances.get)(name)
    except pylxd.exceptions.NotFound:
        return instance
    return instance
