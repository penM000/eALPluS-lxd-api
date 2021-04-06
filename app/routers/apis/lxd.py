from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.responses import RedirectResponse
from typing import List


from ...internal.lxd_machine import launch_machine
from ...internal.lxd_network import create_network, get_ip
from ...internal.lxd_client import client


router = APIRouter(
    prefix="/lxd",
    tags=["lxd"],
    responses={404: {"description": "Not found"}},
)


@router.get("/ip")
async def get_cluster():
    return get_ip()


@router.get("/image")
async def get_cluster():
    for i in client.images.all():
        print(i.aliases)
    return


@router.get("/cluster")
async def get_cluster():
    cluster = client.cluster.get()
    members = cluster.members.all()
    return members


@router.get("/container")
async def get_container():
    names = list()
    for i in client.containers.all():
        names.append(i.name)
    return names


@router.get("/container/{prefix}")
async def get_container_prefix(prefix: str):
    names = list()
    for i in client.containers.all():
        if str(i.name).startswith(prefix):
            names.append(i.name)
    return names


@router.get("/container/delete/{name}")
async def get_container_prefix(name: str):
    if client.containers.exists(name):
        client.containers.get(name).stop(wait=True)
        client.containers.get(name).delete(wait=True)
        return True
    return False


@router.get("/container/delete/prefix/{prefix}")
async def get_container_prefix(prefix: str):
    containers = list()
    for i in client.containers.all():
        if str(i.name).startswith(prefix):
            containers.append(i)
    for container in containers:
        container.stop(wait=True)
        container.delete(wait=True)


@router.get("/network")
async def get_network():
    for i in client.networks.all():
        print(i.name)
    return


@router.get("/network/{name}")
async def get_network(name: str):
    return client.networks.get(name)


@router.get("/network/create/{name}")
async def get_network(name: str):
    await create_network(name)
    return client.networks.get(name)


@router.get("/container/url/{ealps_cid}/{ealps_sid}")
async def get_container_url(ealps_cid: str, ealps_sid: str):
    """
    ealps_cid = 授業コード(イメージ名)\n
    ealps_sid = 学籍番号(授業コード内で一意に定まるもの)
    """
    result = await launch_machine(hostname=f"{ealps_cid}-{ealps_sid}",
                                  imagealias=ealps_cid,
                                  network=ealps_cid)
    if result["status"]:
        ipaddr = "192.168.1.80"
        port = result["assign_port"]
        # print(f"http://{ipaddr}:{port}")
        response = RedirectResponse(url=f"http://{ipaddr}:{port}")
        return response
    else:
        return result
