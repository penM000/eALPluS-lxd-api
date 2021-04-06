from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.responses import RedirectResponse
from typing import List


from ...internal.lxd_machine import launch_machine
from ...internal.lxd_network import create_network
from ...internal.lxd_client import client


router = APIRouter(
    prefix="/lxd",
    tags=["lxd"],
    responses={404: {"description": "Not found"}},
)


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
    for i in client.containers.all():
        print(i.name)
        print(i.devices)
    return


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
        print(f"http://{ipaddr}:{port}")
        response = RedirectResponse(url=f"http://{ipaddr}:{port}")
        return response
    else:
        return result
